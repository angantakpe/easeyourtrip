import time, uuid
from datetime import datetime
import os
from main import docprocess, process_photo
from src.utils.util import *
from src.azure_services.cloud import *
from src.face_api.face_func import *
from src.azure_services.computerVision import *
from src.img_processing.img_process import *
from fastapi import FastAPI, Form, UploadFile
from typing import Annotated, Optional
import asyncio
from src.logging.sql_log import get_log_table
from src.caching.cache_func import get_cache_table
from src.logging.logger import debug_log

load_dotenv(override=True)

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    try:
        LOG_TABLE_NAME = os.getenv("LOG_TABLE_NAME")
        FACE_TABLE_NAME = os.getenv("FACE_TABLE_NAME")
        get_log_table(LOG_TABLE_NAME)
        get_log_table(FACE_TABLE_NAME)
        get_cache_table()
        
        # Create external service logs directory
        os.makedirs(os.path.join("logs", "external_services"), exist_ok=True)
        debug_log("Created external services log directory", "startup", "system")
    except Exception as e:
        print("Exception is: ", e)


with open(os.path.join("assests", "page_name_new.json"), "r") as f:
    catg_mapp = json.load(f)
f.close()
# Create a custom ThreadPoolExecutor


@app.post("/process")
def classify_doc(file: Annotated[UploadFile, Form()], apikey: Annotated[str, Form()]):
    request_id = str(uuid.uuid4())
    debug_log("request started", "route process", request_id)

    try:
        # file_content = await file.read()
        file_content = asyncio.run(file.read())
        filename = file.filename
        # file_mimeType =  mimetypes.guess_type(file.filename)[0]
    except Exception as e:
        print("Exception is: ", e)

    result = docprocess(filename, file_content, str(apikey), None, None, request_id)
    debug_log("request processed", "route process", request_id)
    print("response fastapi:::\n")
    return result


@app.post("/validImage")
def validImage(
    file: Annotated[UploadFile, Form()],
    apikey: Annotated[str, Form()],
    crop_img=Annotated[str, None],
    custom_Crop=Annotated[str, None],
    height=Annotated[str, None],
    width=Annotated[str, None],
):
    print("requestRecieved validImage")
    start = time.time()
    jsonObj = {}
    jsonObj["Timestamp"] = str(datetime.now()).replace(":", "-")
    request_id = uuid.uuid4()
    try:
        file_content = asyncio.run(file.read())
        filename = file.filename
        # file_content =  await file.read()
        try:
            cropImg = crop_img
        except KeyError:
            cropImg = True
        try:
            customCrop = custom_Crop
        except KeyError:
            customCrop = False
    except:
        print("Exception in Valid image file handeling as ::", str(e))
    if customCrop != True and customCrop != "True":
        customCrop = False
        cropHeight = None
        cropWidth = None
    else:
        customCrop = True
        cropHeight = int(height)
        cropWidth = int(width)
    jsonObj["requestRoute"] = "validImage"
    jsonObj["file_upload_name"] = file.filename
    api_key = apikey
    result_final = process_photo(
        filename,
        file_content,
        api_key,
        customCrop,
        cropHeight,
        cropWidth,
        cropImg,
        jsonObj,
    )
    return result_final


@app.post("/extract_with_category")
def upload_doc(
    apikey: Annotated[str, Form()],
    file: Annotated[Optional[UploadFile], Form()] = None,
    updated_cat: Annotated[Optional[str], Form()] = None,
    url: Annotated[Optional[str], Form()] = None,
):
    print("requestRecieved process")
    request_id = str(uuid.uuid4())
    # making a Unique request Id for each request for making LOGS around that request
    try:
        if file:
            file_content = asyncio.run(file.read())
            filename = file.filename
            # file_mimeType =  mimetypes.guess_type(file.filename)[0]

        elif url:
            file_content, filename = save_url_file(url)
        else:
            file_content = None
    except Exception as e:
        print("Exception is: ", e)
        return "Exception in uploading file"

    if file_content == None:
        return "Uploaded file is none"

    api_key = str(apikey)
    if (
        api_key != os.environ.get("NURONAI_API_KEY")
        and api_key != os.environ.get("NURONAI_API_KEY2")
        and api_key != os.environ.get("NURONAI_API_KEY_LOCAL")
    ):
        return "Give  a Valid API key"
    cat_imgclass = catg_mapp.get("page_image_class_map")
    cat_textclass = catg_mapp.get("page_name")
    if updated_cat != None:
        updated_img_cat = cat_imgclass[updated_cat]
        for k, v in cat_textclass.items():
            if v == updated_cat:
                updated_txt_cat = k
    else:
        updated_img_cat = None
        updated_txt_cat = None

    try:
        response = docprocess(
            filename,
            file_content,
            str(api_key),
            updated_img_cat,
            updated_txt_cat,
            request_id,
        )
        return response
    except Exception as e:
        print("Exception in newroute as ::", str(e))
        return str(e)


# sync fast_api files are
@app.get("/live")
async def live():
    print("requestRecieved process")
    return "API IS LIVE"


@app.get("/")
async def root():
    """
    Root endpoint that provides basic information about the API
    """
    return {
        "name": "EaseYourTrip Document AI API",
        "version": "1.0.0",
        "description": "API for processing and analyzing travel documents",
        "endpoints": {
            "/process": "Process and classify documents",
            "/validImage": "Validate and process images",
            "/extract_with_category": "Extract information with specified category",
            "/live": "Check if the API is live",
            "/docs": "API documentation (Swagger UI)",
        },
    }


if __name__ == "__main__":
    import uvicorn

    if not (os.path.exists(os.path.join("logs"))):
        os.mkdir(os.path.join("logs"), 0o666)
    if not (os.path.exists(os.path.join("static"))):
        os.mkdir(os.path.join("static"), 0o666)
    uvicorn.run("fast_api:app", host="127.0.0.1", port=5321, workers=4)
