import os , requests  , time
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from ratelimit import limits, sleep_and_retry
from dotenv import load_dotenv
from src.utils.logs import append_csv  
from src.logging.logger import debug_log

load_dotenv(override = True)
#azure face api
API_KEY = os.environ.get('AZURE_FACE_API_KEY')
ENDPOINT = os.environ.get('AZURE_FACE_API_ENDPOINT')

subscription_key = os.environ.get('AZURE_COMPUTERVISION_OCR_SUBSCRIPTION_KEY')
endpoint = os.environ.get('AZURE_COMPUTERVISION_OCR_ENDPOINT')
credentials = CognitiveServicesCredentials(subscription_key)
cv_client = ComputerVisionClient(endpoint, credentials)

ONE_SECOND = 1
MAX_CALLS_PER_SECOND = 9
@sleep_and_retry
@limits(calls=MAX_CALLS_PER_SECOND, period=ONE_SECOND)
def Azure_ocr_sdk(image_path , csv_row , sql_dict , request_id):
    try:
        azureOcr_Raw_Response = ""
        azureOcr_Method_Response = "" 
        # Create a computer vision client
        
        try:
            start_t = time.time()
            response = cv_client.read_in_stream(open(image_path,'rb'), raw=True, language='en', model_version='latest')
        except Exception as e:
            debug_log(f"Exception in sending Azure Ocr request as {str(e)} ", "img_process", request_id)
            append_csv(csv_row , "Azure_OCR_Failed")
            sql_dict.update({'ocr_time' : "Azure_OCR_Failed" })

            print("Exception in azure ocr ",e)
            azureOcr_Raw_Response = "Exception in azureComputerVisionOCR"+" "+str(e)
            azureOcr_Method_Response = {'text_blob':[], 'text_string':[], 'words_blob':[], 'confidence_scores':[], 'words_loc':[]}
            return {'text_blob':[], 'text_string':"", 'words_blob':[], 'confidence_scores':[], 'words_loc':{}, "azureOcr_Raw_Response":azureOcr_Raw_Response, "azureOcr_Method_Response":azureOcr_Method_Response}

        end_t = time.time()
        append_csv(csv_row , end_t - start_t)
        sql_dict.update({'ocr_time' :end_t - start_t })
        operationLocation = response.headers['Operation-Location']
        operation_id = operationLocation.split('/')[-1]
        result = cv_client.get_read_result(operation_id)
        while(result.status == OperationStatusCodes.running):
            operationLocation = response.headers['Operation-Location']
            operation_id = operationLocation.split('/')[-1]
            result = cv_client.get_read_result(operation_id)

        text_blob = []
        words_blob = []
        confidence_scores = []
        words_pos = {}
        text_string = ""

        if result.status == OperationStatusCodes.succeeded:
            read_results = result.analyze_result.read_results
            azureOcr_Raw_Response = result.as_dict()
            for analyzed_result in read_results:
                angle = analyzed_result.angle
                print("angle;:::",angle)
                for line in analyzed_result.lines:
                    if line.appearance.style.name=="handwriting":
                        continue
                    w = line.text
                    text_blob.append(w.upper())
                    text_string = text_string+(w.upper())
                    text_string = text_string+" "
                    for word in line.words:
                        words_blob.append(word.text)
                        confidence_scores.append(word.confidence)
                        if word.text.upper() not in words_pos.keys():                           
                            words_pos[word.text.upper()] = [word.bounding_box]
                        else:
                            words_pos[word.text.upper()].append(word.bounding_box) 
                        
        azureOcr_Method_Response = {'text_blob':text_blob, 'text_string':text_string, 'words_blob':words_blob, 'confidence_scores':confidence_scores, 'words_loc':words_pos}
        return {'text_blob':text_blob, 'text_string':text_string, 'words_blob':words_blob, 'confidence_scores':confidence_scores, 'words_loc':words_pos,"angle": angle, "azureOcr_Raw_Response":azureOcr_Raw_Response, "azureOcr_Method_Response":azureOcr_Method_Response}
    except Exception as e:
        debug_log(f"Exception in Azure Ocr request as {str(e)} ", "img_process", request_id)
        return {'text_blob':[], 'text_string':"", 'words_blob':[], 'confidence_scores':[], 'words_loc':{},"angle": angle, "azureOcr_Raw_Response":azureOcr_Raw_Response, "azureOcr_Method_Response":azureOcr_Method_Response}


ONE_SECOND = 1
MAX_CALLS_PER_SECOND = 9
@sleep_and_retry
@limits(calls=MAX_CALLS_PER_SECOND, period=ONE_SECOND)
def face_api_request(result, image_path):
    try:
        azureFaceDetection_Parsed_Response = ""
        azureFaceDetection_Raw_Response = ""
        params = {
            'returnFaceId': 'false',
            'returnFaceLandmarks': 'true',
            'returnFaceAttributes': 'headPose,glasses,occlusion,accessories,blur,exposure,noise'
        }
        headers = {'Content-Type': 'application/octet-stream',
                'Ocp-Apim-Subscription-Key': API_KEY}
        data = None
        response = None
        parsed_response = None
        try:
            with open(image_path, 'rb') as f:
                data  = f.read()
            f.close()    
        except:
            result["remarks"] = result["remarks"] + " FAILURE AT FINDING IMAGE AT PATH. "
            result["process_status"] = "EXCEPTION OCCURRED"
        try:
            response = requests.post(ENDPOINT+"/face/v1.0/detect", params=params, headers=headers, data=data)
            parsed_response = response.json()
        except:
            try:
                response = requests.post(ENDPOINT+"/face/v1.0/detect", params=params, headers=headers, data=data)
                parsed_response = response.json()
            except Exception as e:
                print("Exception in azure face api request: ",e)
                azureFaceDetection_Raw_Response = "Exception in azureFaceDetectAI"+" "+str(e)
                azureFaceDetection_Parsed_Response = []
                result["remarks"] = result["remarks"] + " FACE API NETWORK CONNECTION ERROR. "
                result["process_status"] = "EXCEPTION OCCURRED"
                result["azure_response"] = []
                result["azureFaceDetection_Raw_Response"] = azureFaceDetection_Raw_Response
                result["azureFaceDetection_Parsed_Response"] = azureFaceDetection_Parsed_Response
                return result
        azureFaceDetection_Raw_Response = response.json()
        azureFaceDetection_Parsed_Response = parsed_response
        result["azure_response"] = parsed_response
        result["azureFaceDetection_Raw_Response"] = azureFaceDetection_Raw_Response
        result["azureFaceDetection_Parsed_Response"] = azureFaceDetection_Parsed_Response
        return result
    except Exception as e:
        print("Exception in face_api_request as::", str(e))
        return result