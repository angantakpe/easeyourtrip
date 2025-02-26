from src.doc_methods.passport_front import Passport_front
from src.doc_methods.flight_ticket import flight_ticket_llm
from src.doc_methods.basemethods import (
    PassportBackSchema ,PassportFrontSchema  , FlightTicketSchema , 
    SalarySlipSchema, AccountStatementSchema, BalanceCertificateSchema, FixedDepositSummarySchema, HotelTicketSchema, LettersSchema, 
    TravelInsuranceSchema,BirthCertificate,EmploymentLetter,IncomeTaxReturn,BusinessBalanceSheet,
     MarriageCertificate,PropertyOwnership,UsPrCard,UtilityBills,ItinerarySchema , NationalIdSchema , StatementOfPurpose
)
from src.utils.logs import  append_csv
from src.utils.coordinates import get_coordinates 
from src.azure_services.llm import call_llm
from src.face_api.face_func import get_face_landmarks
from src.utils.util import make_photo_conclusion
from datetime import datetime
from src.logging.logger import debug_log
import json , time , os

try:#The standard json schema at the document level is predefined in assests/documents.json. Loading the schema for updating it.
    with open(os.path.join('assests', 'ocr_categories.json'), 'r') as f:
        docs = json.load(f)
        NOT_TO_EXTRACT = docs["no_extraction"]
    f.close()    
except Exception as e:        
    print("Exception in doc_schema loading as :", str(e))


def get_document_prompt( document_type : str ):
    try:#The standard json schema at the document level is predefined in assests/documents.json. Loading the schema for updating it.
        with open(os.path.join('assests', 'prompts.json'), 'r' , encoding= 'utf-8') as f:
            PROMPTS_DICT = json.load(f)
        f.close() 

        return PROMPTS_DICT[document_type]
    except Exception as e:        
        print("Exception in get_document_prompt as :", str(e))
        return None

def extract_data_based_on_doctype(image_schema , new_cat   , cropped_image_coordinates  ,new_image_name , new_img_path  ,ocr_resp, new_image_url ,new_img_diam ,  csv_row ,sql_dict , jsonObj , tempFilePaths , request_id):
    try:
        if new_cat == 'other':
            image_schema["data"].update({})
            image_schema["readabilityLevel"] = "Poor"
            image_schema["readabilityScore"] = -1 
            append_csv(csv_row , "no_openai_called")
            append_csv(csv_row , "no_faceapi_called")
            sql_dict.update({'face_api_time' : 'no_faceapi_called'})

        elif new_cat in NOT_TO_EXTRACT :    
            image_schema["data"].update({})
            append_csv(csv_row , "no_openai_called")
            append_csv(csv_row , "no_faceapi_called")

        elif new_cat == 'passport_front':
            jsonObj["Time"]["Passport_front_called"] = str(datetime.now())
            resp =  Passport_front( ocr_resp["text_blob"] , ocr_resp['text_string'] , csv_row , PassportFrontSchema  , request_id)
            jsonObj["Time"]["Passport_front_done"] = str(datetime.now())
            jsonObj["Time"]["Passport_front_time"]= str( datetime.strptime(jsonObj["Time"]["Passport_front_done"], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(jsonObj["Time"]["Passport_front_called"], "%Y-%m-%d %H:%M:%S.%f") )
            coordinates = get_coordinates(resp ,cropped_image_coordinates)
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , "no_openai_called")
            append_csv(csv_row , "no_faceapi_called") 

        elif new_cat == 'passport_back':    
            try:
                prompt_template = get_document_prompt("passport_back")
                jsonObj["Time"]["Passport_back_called"] = str(datetime.now())
                start_time = time.time()
                resp = call_llm(ocr_resp["text_string"] , prompt_template , PassportBackSchema , request_id)
                openai_time = str(time.time() - start_time)
            except:
                resp = {}
            jsonObj["Time"]["Passport_back_done"] = str(datetime.now())
            jsonObj["Time"]["Passport_back_time"]= str( datetime.strptime(jsonObj["Time"]["Passport_back_done"], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(jsonObj["Time"]["Passport_back_called"], "%Y-%m-%d %H:%M:%S.%f") )
            coordinates = get_coordinates(resp , cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp   
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })

            append_csv(csv_row , "no_faceapi_called")

        elif new_cat == 'flight_ticket' :  
            prompt_template = get_document_prompt("flight_ticket")
            start_time = time.time()
            resp = flight_ticket_llm(ocr_resp["text_string"] , prompt_template , FlightTicketSchema , request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp , cropped_image_coordinates)
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })

            append_csv(csv_row , "no_faceapi_called")

        elif new_cat in ["aadhar_back" , "aadhar_front" , "aadhar_full" , "aadhar_full2" , "pancard" , "driving_licence"] :  
            print("text_string::::::::" ,ocr_resp["text_string"] )
            prompt_template = get_document_prompt("national_id")
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , NationalIdSchema, request_id)
            openai_time = str(time.time() - start_time)
            
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp   
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")

        elif new_cat.split('_')[0] == 'photo':
            append_csv(csv_row , "no_openai_called")

            image_schema.update({ "preprocessed_image" : new_image_url ,
                                 "preprocessed_image_dimensions" : new_img_diam })
            del image_schema["readabilityLevel"] 
            del image_schema["readabilityScore"]
            image_schema["isPass"] = ''
            pof_res = {}
            start_fa = time.time()

            jsonObj["Time"]["FaceAPI_called"] = str(datetime.now())
            try:
                start_time = time.time()
                response = get_face_landmarks(uploadFileName=None, img_path= new_img_path ,image_name= new_image_name,customCrop = False , cropHeight = None ,cropWidth = None,cropImg = False, jsonObj = jsonObj , tempFilePaths = tempFilePaths)
                sql_dict.update({"face_api_time" : str(time.time() - start_time) })
            except Exception as e:
                debug_log(f"Exception in get_face_landmarks as {str(e)} ", "img_process", request_id)
                append_csv(csv_row , "face_api_failed")
                sql_dict.update({'face_api_time' : "face_api_failed"})
                response = False

            jsonObj["Time"]["FaceAPI_done"] = str(datetime.now())
            jsonObj["Time"]["FaceAPI_time"]= str( datetime.strptime(jsonObj["Time"]["FaceAPI_done"], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(jsonObj["Time"]["FaceAPI_called"], "%Y-%m-%d %H:%M:%S.%f") )
            if response:
                try:
                    end_fa = time.time()
                    append_csv(csv_row , end_fa - start_fa)
                    sql_dict.update({'face_api_time' : end_fa - start_fa})
                    pof_res = response
                    if "DocCategory" in pof_res.keys():
                        del pof_res["DocCategory"]
                    if "filename" in pof_res.keys():
                        del pof_res["filename"]
                    if "isPass" in pof_res.keys():
                        image_schema["isPass"] = pof_res["isPass"]
                        del pof_res["isPass"]
                except Exception as e:
                        print(f"exception occured: {str(e)}")
                        pof_res = {}
            pof_res = make_photo_conclusion(pof_res)            
            image_schema["data"].update(pof_res)


        elif new_cat == 'salary_slip':
            prompt_template = get_document_prompt("salary_slip")
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , SalarySlipSchema, request_id)
            openai_time = str(time.time() - start_time)

            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp   
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")
        
        elif new_cat == 'account_statement':
            prompt_template = get_document_prompt('account_statement')
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , AccountStatementSchema, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp   
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")
        
        
        elif new_cat == 'balance_certificate':
            prompt_template = get_document_prompt('balance_certificate')
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , BalanceCertificateSchema, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp   
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")
        
        
        elif new_cat == 'fixed_deposit_summary':
            prompt_template = get_document_prompt('fixed_deposit_summary')
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , FixedDepositSummarySchema, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp   
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")
        
        elif new_cat == 'hotel_ticket':
            prompt_template = get_document_prompt('hotel_ticket')
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , HotelTicketSchema, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")
        

        elif new_cat == 'travel_insurance':
            prompt_template = get_document_prompt(new_cat)
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , TravelInsuranceSchema, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")
        
        elif new_cat == 'letters':
            prompt_template = get_document_prompt(new_cat)
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , LettersSchema, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")

        elif new_cat == 'itinerary':
            def calculate_days(start_date, end_date):
                date_format = "%d/%m/%Y"
                start = datetime.strptime(start_date, date_format)
                end = datetime.strptime(end_date, date_format)
                return (end - start).days

            prompt_template = get_document_prompt(new_cat)
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , ItinerarySchema, request_id)
            openai_time = str(time.time() - start_time)
            merged_country_list = []
            if resp.get("country_stay_list"):
                for index, entry in enumerate(resp['country_stay_list']):
                    if merged_country_list and (merged_country_list[-1]["country"] == entry["country"]):
                        merged_country_list[-1]["departure_date"] = entry["departure_date"]
                        merged_country_list[-1]["num_of_days"] = calculate_days(
                            merged_country_list[-1]["arrival_date"], merged_country_list[-1]["departure_date"]
                        )
                    else:
                        merged_country_list.append(entry)
                
                resp["country_stay_list"] = merged_country_list

            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")
        

        elif new_cat == 'birth_certificate':
            prompt_template = get_document_prompt(new_cat)
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , BirthCertificate, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")


        elif new_cat == 'business_balance_sheet':
            prompt_template = get_document_prompt(new_cat)
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , BusinessBalanceSheet, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")


        elif new_cat == 'employment_letter':
            prompt_template = get_document_prompt(new_cat)
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , EmploymentLetter, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")


        elif new_cat == 'itr':
            prompt_template = get_document_prompt(new_cat)
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , IncomeTaxReturn, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")



        elif new_cat == 'marriage_certificate' or  new_cat == 'divorce_certificate':
            prompt_template = get_document_prompt(new_cat)
             
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , MarriageCertificate, request_id)
            openai_time = str(time.time() - start_time)

            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")


        elif new_cat == 'property_ownership':
            prompt_template = get_document_prompt(new_cat)
             
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , PropertyOwnership, request_id)
            openai_time = str(time.time() - start_time)

            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")


        elif new_cat == 'statement_of_purpose':
            prompt_template = get_document_prompt(new_cat)
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , StatementOfPurpose, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")


        elif new_cat == 'us_pr_card':
            prompt_template = get_document_prompt(new_cat)
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , UsPrCard, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")


        elif new_cat == 'utility_bills':
            prompt_template = get_document_prompt(new_cat)
            start_time = time.time()
            resp = call_llm(ocr_resp["text_string"] , prompt_template , UtilityBills, request_id)
            openai_time = str(time.time() - start_time)
            coordinates = get_coordinates(resp ,cropped_image_coordinates )
            resp["values_coordinates"] = coordinates
            image_schema["data"] = resp
            append_csv(csv_row , openai_time)
            sql_dict.update({"openai_time" :openai_time })
            append_csv(csv_row , "no_faceapi_called")


        return image_schema
    except Exception as e:
        debug_log(f"Exception in extract_data_based_on_doctype as {str(e)} ", "img_process", request_id)
        return image_schema
    



