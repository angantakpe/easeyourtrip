import os , csv
from dotenv import load_dotenv

load_dotenv(override=True)


def savecsv_log(row):
    try:
        print("started savecsv")
        csv_path = os.getenv('CSV_LOG_PATH')
        if csv_path is None:
            print("CSV_LOG_PATH environment variable is not set", "savecsv_log")
            return
        file_exists = os.path.isfile(csv_path)

        try:
            with open(csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists or os.stat(csv_path).st_size == 0:
                    # field = ["request_id", "page_start_time", "api_key", "filename","blob_file_name", "file_type", "page_no", "total_pages","image_name", "preprocessing_time","preprocess_image","distanse_image",  "class_of_page","classification_time",  "ocr_time", "distance_text" , "text_class", "openai_time", "face_api_time", "final_time", "total_page_time" , "response_file"]
                    field = ["request_id", "page_start_time", "api_key", "filename","blob_file_name", "file_type", "page_no", "total_pages","image_name", "preprocessing_time","preprocess_image", "class_of_page", "classification_time", "ocr_time", "openai_time", "face_api_time", "final_time", "total_page_time" , "response_file"]
                    writer.writerow(field)
                
                writer.writerow(row)
            f.close()    
        except Exception as e:
            print(f"An error occurred: {e}", "savecsv_log")
    except Exception as e:        
        print("Exception in savecsv_log as:", str(e))
        return

def csvrow():
    try:
        return []
    except Exception as e:
        print("Exception in csvrow as:", str(e))
        return []

def append_csv(array, value):
    try:
        array = array.append(value)
        return array
    except Exception as e:
        print("Exception in append CSV as :", str(e))
        return array
