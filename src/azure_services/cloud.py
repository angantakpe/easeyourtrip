from azure.storage.blob import ContainerSasPermissions, generate_blob_sas
from azure.storage.blob import BlobServiceClient
import os 
from datetime import datetime , timedelta
from dotenv import load_dotenv

load_dotenv(override =True)
# Azure storage details
connect_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.environ.get('AZURE_STORAGE_CONTAINER_NAME')
blob_service_client = BlobServiceClient.from_connection_string(connect_str)


#uplaoding the files on azure cloud
def upload_to_azure(image_path,file_name):
    try:
        print("inside upload_to_azure")
        blob_client = blob_service_client.get_blob_client(container_name, file_name)
        with open(image_path,"rb") as data:
            blob_client.upload_blob(data, overwrite=True, metadata={"service":"nuronai_production_service"})
        data.close()
    except Exception as e: 
        print("Exception in upload_to_azure as :", str(e))

#generating URL to access the blob files uploaded on blob.
def get_img_url_with_blob_sas_token(blob_name):
    try:
        account_name=os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
        container_name=os.environ.get("AZURE_STORAGE_CONTAINER_NAME")
        account_key=os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
        blob_sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=ContainerSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(days=365*100)
        )
        blob_url_with_blob_sas_token = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{blob_sas_token}"
        return blob_url_with_blob_sas_token
    except Exception as e:
        print("Exception in getting image url with sas token: ",e)
        return ""
