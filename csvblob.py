from azure.storage.blob import BlobServiceClient
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

# Define the necessary variables
connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME')       # Replace with your container name
blob_name = f"log_csv.csv_{datetime.now()}"                     # The blob name in Azure Blob Storage
local_file_name = "/home/nuronai/nuronai-intellivisa-api/log_csv.csv"               # The local file name (same as the blob name in this case)

# Create the BlobServiceClient object
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Create the container if it doesn't exist
container_client = blob_service_client.get_container_client(container_name)
try:
    container_client.create_container()
except Exception as e:
    print(f"Container already exists or error occurred: {e}")

# Create a BlobClient object
blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

try:
    # Upload the file to the blob
    with open(local_file_name, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    print(f"File {local_file_name} successfully uploaded to {blob_name} in {container_name}.")
except Exception as e:
    print(f"An error occurred: {e}")
