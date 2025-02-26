from src.classifier.classify import *
# from src.classifier.redis_function import add_to_cache ,get_from_cache
from src.logging.sql_log import insert_log , insert_face_log
from src.caching.cache_func import get_cache_data , insert_cache , delete_cache
from src.utils.util import *
from src.azure_services.cloud import *
import  time , base64
from src.img_processing.preprocessing.image_preprocessing import *
from src.face_api.face_func import get_face_landmarks
from src.azure_services.computerVision import *
from src.doc_methods.valid_test import *
from src.doc_methods.extraction import extract_data_based_on_doctype
from src.img_processing.img_process import get_response_image , img_size_check , corr_img_extn
import mimetypes
from src.utils.logs import savecsv_log , csvrow , append_csv
from dotenv import load_dotenv
import imagehash
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from src.logging.logger import debug_log

# import face_recognition
load_dotenv(override= True)


try:#The standard json schema at the document level is predefined in assests/documents.json. Loading the schema for updating it.
    with open(os.path.join('assests', 'ocr_categories.json'), 'r') as f:
        docs = json.load(f)
        OCR_CATS = docs["ocr_categories"]
        ALL_CATS = docs["all_categories"]
        not_to_extract = docs["no_extraction"]
    f.close()    
except Exception as e:        
    print("Exception in doc_schema loading as :", str(e))



def process_page_threads(i, 
        no_pgs, images, jsonObj, image_name, folder_path, tempFilePaths, request_id, api_key, 
        uploaded_filename, updated_img_cat, updated_txt_cat, doc_schema, doccat, doc_readability_score,
    ):
    
    jsonObj["Time"][f"Started_Page_{i+1}"] = str(datetime.now())
    new_image_name = image_name.split(".")[0]+"_page_"+str(i)+".jpeg"
    #saving the images of the pdf on local disc for processing
    # check_pdf_pixels()
    images[i] = check_doc_pixels(images[i])
    images[i].save(os.path.join(folder_path,new_image_name))
    new_img_path = folder_path+new_image_name
    tempFilePaths.append(new_img_path)
    upload_to_azure(new_img_path,new_image_name)
    new_image_url = get_img_url_with_blob_sas_token(new_image_name)
    jsonObj["Time"]["Process Started"] = str(datetime.now())               
    try:
        sql_dict = {}
        csv_row = csvrow()
        append_csv(csv_row , request_id)
        start_pg = datetime.now()
        append_csv(csv_row , start_pg)
        append_csv(csv_row , api_key)
        append_csv(csv_row , uploaded_filename)
        append_csv(csv_row , image_name)
        append_csv(csv_row , "pdf")
        append_csv(csv_row , i+1)
        append_csv(csv_row , no_pgs)
        append_csv(csv_row , new_image_name)
        sql_dict.update({'request_id': request_id  ,
                         'page_start_time' : start_pg ,
                         'api_key' : api_key ,
                         'filename' : uploaded_filename ,
                         'blob_file_name' : image_name ,
                         'file_type' : "pdf" ,'page_no' : i+1 ,
                         'total_pages' : no_pgs ,'image_name':new_image_name  })
        
    except Exception as e:
        print("Exception in csv_row as :", str(e))
        debug_log
        csv_row = []
    pg_result = img_process(new_img_path, new_image_name, new_image_url ,  i+1 ,updated_img_cat, updated_txt_cat, jsonObj , csv_row ,sql_dict, tempFilePaths , request_id)   
    jsonObj["Time"][f"Processed_Page_{i+1}"] = str(datetime.now())
    jsonObj["Time"][f"T_Time_Page_No_{i+1}"] = str( datetime.strptime(jsonObj["Time"][f"Processed_Page_{i+1}"], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(jsonObj["Time"][f"Started_Page_{i+1}"], "%Y-%m-%d %H:%M:%S.%f") )
    
    doc_schema["pages"].append(pg_result)
    if pg_result["Category"] == "Photo":
        doccat.add("photo")
    else:    
        doccat.add(pg_result["Category"])
    if "readabilityScore" in pg_result.keys():
        if float(pg_result["readabilityScore"]) > 0:
            doc_readability_score.append(pg_result["readabilityScore"])  
    doc_schema["DocCategory"] = list(doccat)      
    end_pg = datetime.now()
    append_csv(csv_row , end_pg)
    append_csv(csv_row , end_pg - start_pg)
    json_res_name = image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
    append_csv(csv_row , json_res_name)
    print('this savecsv')
    savecsv_log(csv_row)
    sql_dict.update({'final_time': end_pg , 'total_page_time':end_pg - start_pg , "response_file":json_res_name , "page_status" : "Success" , "page_remark" : "NO"  })
    insert_log(sql_dict , request_id)


 #Doc Process handels the whole document and returns the output in the STANDARD JSON OUTPUT. 
def docprocess(uploaded_filename , file_content , api_key ,updated_img_cat, updated_txt_cat, request_id): 
    try:                                                     
        jsonObj = {}
        jsonObj["Time"] = {}
        tempFilePaths = [] #making a array to collect the path of the temporary files stored on disc for later on deleting the files
        try:#The standard json schema at the document level is predefined in assests/documents.json. Loading the schema for updating it.
            with open(os.path.join('assests', 'document.json'), 'r') as f:
                doc_schema = json.load(f)
            f.close()    
        except Exception as e:        
            print("Exception in doc_schema loading as :", str(e))
        jsonObj["Timestamp"] =  str(datetime.now()).replace(":","-")
        jsonObj["Time"]["Process_Started"] = str(datetime.now())
        jsonObj["file_upload_name"] = uploaded_filename
        jsonObj["requestRoute"] = "Process"
        jsonObj["apikey"] = api_key
        #saving the uploaded file object on disc(static folder) and taking the path, name and extension of the file
        img_path ,image_name, file_extension = save_and_gen_filepath(uploaded_filename , file_content ,tempFilePaths)
        #validatin API key , if invalid then saving the file on blob and returning error message
        val_api =  validate_apikey(api_key ,image_name ,jsonObj ,tempFilePaths )
        if not val_api:
            return "Please Provide a valid api key"

        jsonObj["Time"]["file_saved"] = str(datetime.now())
        folder_path = os.path.join("static")+"/"
        file_size = os.path.getsize(img_path)
        jsonObj["file_size"] = file_size
        doccat = set() #making a set of all unique documents in the file. later on convert it into list.
        doc_schema["filename"] = uploaded_filename
        doc_schema["fileSize"] = str(file_size / 1024 ** 2) + " MB"


        if file_extension == 'pdf':
            doc_readability_score = []
            try:
                #converting pdf pages into images. 
                images = pdf_to_jpeg(img_path)
            except Exception as e:
                print("Exception occured in processing file: ",e)
                jsonObj["requestResponse"] = "Invalid file format, current file format: "+file_extension
                with open("static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json", "w") as f:
                    json.dump(jsonObj, f)
                f.close()
                file_path = "static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
                file_name = image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
                upload_to_azure(file_path, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                # print("temperory stored file: ",tempFilePaths)
                deleteFiles(tempFilePaths)
                return "Uploaded pdf file is corrupted."
            no_pgs = len(images)
            jsonObj["pageCount"] = no_pgs
            doc_schema["number_pgs"] = no_pgs
            #processing each page of PDF by iterating on the array of images extracted from pdf

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(process_page_threads, i, 
                    no_pgs, images, jsonObj, image_name, folder_path, tempFilePaths, request_id, 
                    api_key, uploaded_filename, updated_img_cat, updated_txt_cat, doc_schema, 
                    doccat, doc_readability_score
                    ) for i in range(no_pgs)
                ]
        else:
            sql_dict = {}  
            try:
                csv_row = csvrow()
                append_csv(csv_row , request_id)
                start_pg = datetime.now()
                append_csv(csv_row , start_pg)
                append_csv(csv_row , api_key)
                append_csv(csv_row , uploaded_filename)
                append_csv(csv_row , image_name)
                append_csv(csv_row , "image")
                append_csv(csv_row , 1)
                append_csv(csv_row , 1)
                append_csv(csv_row , image_name)
                sql_dict.update({'request_id': request_id,
                                     'page_start_time' : start_pg ,
                                     'api_key' : api_key ,
                                     'filename' : uploaded_filename ,
                                     'blob_file_name' : image_name ,
                                     'file_type' : "image" ,'page_no' : 1,
                                     'total_pages' : 1 ,'image_name': image_name  })


            except Exception as e:
                print("Exception in csv_row as :", str(e))
                csv_row = []
            img = Image.open(img_path)
            if img.format not in ['JPG','JPEG','PNG','BMP','TIFF']:                
                img_correct = corr_img_extn(img ,img_path ,image_name ,  tempFilePaths, jsonObj )
                if img_correct:
                    img = img_correct
                else:
                    sql_dict.update({"page_status" : f"Invalid file format, current file format:{img.format}"})
                    insert_log(sql_dict , request_id)

                    return("Invalid file format, current file format: "+img.format)
            img = check_doc_pixels(img)    
            width,height = img.size
            img.close()   
            siz_check = img_size_check(width,height, image_name ,jsonObj , tempFilePaths)
            if not siz_check:
                sql_dict.update({"page_status" : f"Image is either too small in dimension or too large:Diam::{width,height}"})
                insert_log(sql_dict , request_id)
                return  "Image is either too small in dimension or too large. Reupload a right document"
            doc_schema["imageDpi"] = getDPI(img_path)

            image_blob_url = get_img_url_with_blob_sas_token(image_name)  

            jsonObj["Time"]["Started_Page_Image"] = str(datetime.now())
            pg_result = img_process( img_path, image_name,image_blob_url ,  1 ,updated_img_cat, updated_txt_cat, jsonObj , csv_row , sql_dict ,tempFilePaths , request_id) 
            jsonObj["Time"]["Processed_Page_Image"] = str(datetime.now())
            jsonObj["Time"]["T_Time_Page_Image"] = str( datetime.strptime(jsonObj["Time"]["Processed_Page_Image"], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(jsonObj["Time"]["Started_Page_Image"], "%Y-%m-%d %H:%M:%S.%f") )
            end_pg = datetime.now()
            append_csv(csv_row , end_pg)
            append_csv(csv_row , end_pg - start_pg)
            json_res_name = image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
            append_csv(csv_row , json_res_name)
            sql_dict.update({'final_time': end_pg , 'total_page_time':end_pg - start_pg , "response_file":json_res_name , "page_status" : "Success" , "page_remark" : "NO"  })
            insert_log(sql_dict , request_id)
            savecsv_log(csv_row)
            doc_schema["pages"].append(pg_result)
            if pg_result["Category"] == "Photo":
                doc_schema["DocCategory"]  = "photo"
            else:    
                doc_schema["DocCategory"] = str(pg_result["Category"])
            doc_schema["number_pgs"] = 1
            if "readabilityScore" in pg_result.keys():
                doc_schema["readabilityScore"] = pg_result["readabilityScore"]
                doc_schema["readabilityLevel"] = pg_result["readabilityLevel"]
        if doc_schema["readabilityScore"]  is not None:
            if float(doc_schema["readabilityScore"]) < 0.66:
                doc_schema["readabilityLevel"] = "Poor"
            # elif float(doc_schema["readabilityScore"]) < 0.65:
            #     doc_schema["readabilityLevel"] = "Medium"
            else:
                doc_schema["readabilityLevel"] = "Good"

        # print("final doc::::" ,doc_schema )        
        jsonObj["requestResponse"] = json.dumps(doc_schema)
        jsonObj["Time"]["Final_response"] = str(datetime.now())
        jsonObj["Time"]["Doc_time"] = str( datetime.strptime(jsonObj["Time"]["Final_response"], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(jsonObj["Time"]["Process_Started"], "%Y-%m-%d %H:%M:%S.%f") )
        with open("static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json", "w") as f:
            json.dump(jsonObj, f)
        f.close()
        file_path = "static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
        file_name = image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
        upload_to_azure(file_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)
        deleteFiles(tempFilePaths)
        doc_schema = validations(doc_schema , updated_img_cat)
        doc_schema = sort_doc_pages(doc_schema)
        # print(sys.getsizeof(doc_schema))
        return doc_schema        
    except Exception as e:
        sql_dict.update({"page_status":  "Failed"})       
        sql_dict.update({"page_remark":  str(e)})  
        insert_log(sql_dict , request_id)
        print("Excepion in DocProcess as :", str(e))
        return {"error" : "Some thing went wrong"}

def img_process(new_img_path ,new_image_name,new_image_url , pg_no ,updated_img_cat, updated_txt_cat , jsonObj , csv_row,sql_dict, tempFilePaths , request_id):

    try:
        cropped_image_path , crop_image_blob_url = crop_and_generate_image_url(new_image_name ,csv_row ,sql_dict , jsonObj)
        image_pil = Image.open(new_img_path)
        new_img_diam  = image_pil.size
        ss = time.time()
        img_hash = imagehash.average_hash(image_pil) 
        if updated_img_cat==None and updated_txt_cat ==None:
            image_data  = get_cache_data(str(img_hash))
        else:   
            delete_cache(str(img_hash))
            image_data = None 
    except Exception as e:
        debug_log(f"Exception in checking cache as {str(e)} ", "img_process", request_id)
        print("Exception in making image hash as ::", str(e))     
        image_data = None
            
    if image_data!= None:
        sql_dict.update({'pre_cached_status': "True",'hash_id': str(img_hash) })
        append_csv(csv_row , "cached result")
        append_csv(csv_row , "cached result")
        append_csv(csv_row , "no_ocr_called")
        append_csv(csv_row , "no_openai_called")
        append_csv(csv_row , "no_faceapi_called")
        return image_data
    else:
        sql_dict.update({'pre_cached_status': "False"})
        sql_dict.update({'hash_id': str(img_hash)})
        try:
            with open(os.path.join('assests','image.json')) as f:      #image 
                image_schema = json.load(f)
            f.close()    
        except Exception as e:   
            debug_log(f"Exception in loading image_schema as {str(e)} ", "img_process", request_id)
            print("Exception in getting Image schema as :", str(e))

        try:    
            new_img_array = cv2.imread(cropped_image_path)
            height, width, channels = new_img_array.shape
            crop_img_diam = (width ,height)
            # print("cropped image diamentiions::::", Image.open(cropped_image_path).size  )
            new_emb_tensor = get_embedding(new_img_array , request_id)
            new_emb = new_emb_tensor.tolist()
            db_path = os.getenv("DB_PATH")
            jsonObj["Time"][f"Classify_started_{pg_no}"] = str(datetime.now())

            if updated_img_cat== None:
                start_cl_t = time.time()
                new_cat = get_category(new_emb, csv_row , request_id)
                end_cl_t = time.time()
                append_csv(csv_row , new_cat)
                append_csv(csv_row , end_cl_t - start_cl_t)
                sql_dict.update({'class_of_page' :new_cat,'classification_time' : end_cl_t - start_cl_t })
                jsonObj["Time"][f"Classify_done_{pg_no}"] = str(datetime.now())
            else :
                new_cat = updated_img_cat

            if (new_cat in OCR_CATS):
                jsonObj["Time"]["Azure_called"] = str(datetime.now())
                ocr_resp = Azure_ocr_sdk(cropped_image_path , csv_row , sql_dict , request_id)
                if updated_txt_cat==None:
                    # new_cat = 'passport_front'
                    text_st = time.time()
                    new_cat = get_category_text(ocr_resp['text_string'] ,new_cat ,csv_row,sql_dict , request_id)

                    text_end = time.time()
                    sql_dict.update({"text_class_time" : text_end - text_st })
                    # new_cat = validate_img_text_cat(new_cat , text_cat)
                else:
                    new_cat = updated_txt_cat

                # rotated_cropped_img_url , rotated_cropped_img_dim , cropped_image_coordinates , cropped_text_blob =  rotate_and_crop_image(cropped_image_path, ocr_resp["angle"]) 

                angle= ocr_resp["angle"]
                rotate_im_path = rotate_image(cropped_image_path, angle , request_id) 
                rotate_im_name = new_image_name.split('.')[0] + "_cropped_rotated." + new_image_name.split('.')[1]
                rotate_im_dim = Image.open(rotate_im_path).size
                rot_coord_staus , rotated_cordinates = rotate_coordinates( ocr_resp['words_loc'] ,angle, Image.open(cropped_image_path).size, Image.open(rotate_im_path).size , request_id)
                if rot_coord_staus:
                    cropped_image , cropped_image_coordinates , cropped_text_blob =   crop_img_text_locations( Image.open(rotate_im_path) , rotate_im_path , rotated_cordinates ,new_cat , ocr_resp["text_string"] , request_id )                      
                else:
                    cropped_image , cropped_image_coordinates , cropped_text_blob =   crop_img_text_locations( Image.open(cropped_image_path) , cropped_image_path , ocr_resp['words_loc'] ,new_cat , ocr_resp["text_string"] , request_id)  

                base, ext = os.path.splitext(rotate_im_path)
                rotated_cropped_img_path = f"{base}_cropped{ext}"
                
                rotated_cropped_img_name = rotate_im_name.split('.')[0] + "_cropped." + new_image_name.split('.')[1]

                cropped_image.save(rotated_cropped_img_path)
                upload_to_azure(rotated_cropped_img_path, rotated_cropped_img_name)
                rotated_cropped_img_url = get_img_url_with_blob_sas_token(rotated_cropped_img_name)
                rotated_cropped_img_dim = cropped_image.size

                tempFilePaths.append(rotate_im_path)
                image_schema["preprocessed_image"] = rotated_cropped_img_url
                image_schema["preprocessed_image_dimensions"] = rotated_cropped_img_dim 
                # cropped_image.save("test.png")
                jsonObj["Time"]["Azure_complete"] = str(datetime.now())
                jsonObj["Time"]["Azure_time"] = str( datetime.strptime(jsonObj["Time"]["Azure_complete"], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(jsonObj["Time"]["Azure_called"], "%Y-%m-%d %H:%M:%S.%f") )
                confidence_scores = ocr_resp['confidence_scores']
            else:
                cropped_image_coordinates = {}
                ocr_resp = {}
                image_schema["preprocessed_image"] = crop_image_blob_url
                image_schema["preprocessed_image_dimensions"] = crop_img_diam
                append_csv(csv_row , "no_ocr_called")
                sql_dict.update({'ocr_time' : 'no_ocr_called'})
                confidence_scores = []
            if(len(confidence_scores)>0):
                avgConfidence = sum(confidence_scores) / len(confidence_scores)
                readabilityScore =avgConfidence
            else:
                avgConfidence = -1
                readabilityScore = avgConfidence
            if avgConfidence!=-1:
                readabilityScore = avgConfidence
                if avgConfidence < 0.66:
                    readabilityLevel = "Poor"
                # elif avgConfidence < 0.65:
                #     readabilityLevel = "Medium"
                else:
                    readabilityLevel = "Good"
            else:
                readabilityLevel = "Poor"

            base64img, mimetype = get_response_image(new_img_path)
            image_schema.update({"available":1 ,"image" :  new_image_url , "image_dimensions" : new_img_diam , "mimetype" : mimetype , "pg_no" : pg_no ,
                                  "readabilityLevel" : readabilityLevel , "readabilityScore" : readabilityScore})
            
            sql_dict.update({'openai_time' : 'no_openai_called','face_api_time' : 'no_faceapi_called'})

            if new_cat not in ALL_CATS:
                new_cat = "other"
            image_schema =  pagecatname(image_schema,  new_cat)
            debug_log("starting extraction", "img_process", request_id)

            image_schema = extract_data_based_on_doctype(image_schema , new_cat   , cropped_image_coordinates  ,new_image_name , new_img_path  ,ocr_resp, new_image_url ,new_img_diam ,  csv_row ,sql_dict , jsonObj , tempFilePaths , request_id)
            debug_log("extraction complete", "img_process", request_id)

            insert_cache(img_hash , image_schema)   
            debug_log("inserted cache in db", "img_process", request_id)
            return image_schema    
        except Exception as e:
            debug_log(f"Exception in img_process as {str(e)} ", "img_process", request_id)
            sql_dict.update({"page_status":  "Failed"})       
            sql_dict.update({"page_remark":  str(e)})  
            insert_log(sql_dict , request_id)
            print("Exception in img_process as ;", str(e))
            return image_schema

def process_photo(uploaded_filename ,file_content, api_key , customCrop ,cropHeight , cropWidth,cropImg,  jsonObj ):
    try:
        face_sql_dict = {}
        tempFilePaths = []
        start = time.time()
        file_mimeType =  mimetypes.guess_type(uploaded_filename)[0]
        jsonObj["mimetype"] = file_mimeType
        img_path ,image_name, file_extension = save_and_gen_filepath(uploaded_filename , file_content  ,tempFilePaths )
        jsonObj["file_extension"] = file_extension
        jsonObj["file_blobname"] = image_name
        
        face_sql_dict.update({"page_start_time" : datetime.now() , 'api_key' : api_key ,"filename" : uploaded_filename , "blob_file_name" : image_name , "file_type": file_mimeType  })
        upload_to_azure(img_path , image_name )
        
        val_api =  validate_apikey(api_key ,image_name ,jsonObj ,tempFilePaths )
        if not val_api:
            face_sql_dict.update({"page_status": "Fail" , "page_remark": f"Please Provide a valid api key:: {api_key}"})
            insert_face_log(face_sql_dict , None)
            return "Please Provide a valid api key"
        
        if not file_mimeType.startswith('image/'):
            face_sql_dict.update({"page_status": "Fail" , "page_remark": f"Not a image file {file_mimeType}"})
            insert_face_log(face_sql_dict , None)
            return "Please upload a Image file"           
        
        try:    
            img = Image.open(img_path)
        except Exception as e:
            print("exception as :::", str(e))    
        if img.format not in ['JPG','JPEG','PNG','BMP','TIFF']:

            img_correct = corr_img_extn(img ,img_path ,image_name ,  tempFilePaths, jsonObj )
            if img_correct:
                img = img_correct
            else:
                face_sql_dict.update({"page_status": "Fail" , "page_remark": f"Invalid file format, current file format: {img.format}"})
                insert_face_log(face_sql_dict , None)
                return("Invalid file format, current file format: "+img.format)
            
        width,height = img.size 
        img.close()   
        siz_check = img_size_check(width,height, image_name ,jsonObj , tempFilePaths)
        if not siz_check:
            face_sql_dict.update({"page_status": "Fail" , "page_remark":  f"Image is either too small in dimension or too large {width,height}" })
            insert_face_log(face_sql_dict , None)
            return  "Image is either too small in dimension or too large. Reupload a right document"
        
        apiResponse = get_face_landmarks(uploaded_filename, img_path ,image_name,customCrop , cropHeight ,cropWidth ,cropImg, jsonObj , tempFilePaths)


        with open("static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json", "w") as f:
            json.dump(jsonObj, f)
        f.close()
        file_path = "static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
        file_name = image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
        upload_to_azure(file_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)
        deleteFiles(tempFilePaths)
        end = time.time()
        face_sql_dict.update({"final_time": datetime.now() ,"total_page_time" : end- start ,"response_file":file_name,"page_status" : "SUCESS", "page_remark" : "NO"   })
        insert_face_log(face_sql_dict , None)
        return apiResponse
    except Exception as e:
        face_sql_dict.update({"page_status" : "Failed", "page_remark" : str(e)  })
        insert_face_log(face_sql_dict , None)
        print("Exception in process_photo as ::", str(e))
        return {}

#function works as main function for 
def face_compare(filename1 , file_content,filename2 , file_content2, request_id):
    
    response = {"filename1" : "" , "filename2": "" , "base64cropImg1": "" ,"base64cropImg2" : "", "data" : {}}
    try:
        #collecting all temporary files for deletion before response
        response.update({"filename1" :filename1 , "filename2": filename2 })
        tempFilePaths = []
        img_path_1 ,image_name_1, file_extension_1 = save_and_gen_filepath(filename1 ,file_content, tempFilePaths)
        img_path_2 ,image_name_2, file_extension_2 = save_and_gen_filepath(filename2 ,file_content2, tempFilePaths)

        img_path_1  = face_pdf_to_img(img_path_1 , image_name_1 , file_extension_1)
        img_path_2  = face_pdf_to_img(img_path_2 ,image_name_2 ,  file_extension_2)

        similarity_score , cropped_img1 , cropped_img2 = cal_face_similarity(img_path_1 , img_path_2, tempFilePaths )
        with open(cropped_img1, 'rb') as im:
            cropped_img1_string = base64.b64encode(im.read()).decode('utf-8')
        im.close()
        with open(cropped_img2, 'rb') as im:
            cropped_img2_string = base64.b64encode(im.read()).decode('utf-8')
        im.close()
        response.update({"base64cropImg1" : cropped_img1_string ,"base64cropImg2" : cropped_img2_string, "data" : similarity_score })
        deleteFiles(tempFilePaths)
        return response
    except Exception as e:
        print("Exception in face_comapre as :::", str(e))
        return response




      
