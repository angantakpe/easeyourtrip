import os, csv
from dotenv import load_dotenv
import datetime

load_dotenv(override=True)


def savecsv_log(row):
    try:
        print("started savecsv")
        csv_path = os.getenv('CSV_LOG_PATH')
        
        # If CSV_LOG_PATH is not set or empty, use a default path
        if not csv_path:
            # Create logs directory if it doesn't exist
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
                
            # Set default CSV log path
            csv_filename = f"document_ai_log_{os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))}.csv"
            csv_path = os.path.join(logs_dir, csv_filename)
            print(f"CSV_LOG_PATH environment variable is not set, using default path: {csv_path}", "savecsv_log")
        else:
            # If CSV_LOG_PATH is a directory, append a default filename
            if os.path.isdir(csv_path) or csv_path.endswith('/') or csv_path.endswith('\\'):
                logs_dir = csv_path
                if not os.path.exists(logs_dir):
                    os.makedirs(logs_dir)
                csv_filename = f"document_ai_log_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
                csv_path = os.path.join(logs_dir, csv_filename)
                print(f"CSV_LOG_PATH is a directory, using file path: {csv_path}", "savecsv_log")
        
        # Ensure the directory exists
        csv_dir = os.path.dirname(csv_path)
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
            
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
