# Document Processing API

A FastAPI-based service for processing and analyzing documents and photos using Azure Cognitive Services.

## Overview

This API service provides endpoints for:
- Document classification and data extraction
- Photo validation and analysis 
- Face detection and comparison
- Support for multiple document types including:
  - Passports
  - National IDs
  - Flight tickets
  - Hotel bookings
  - Bank statements
  - And more...

## Key Features

- Document classification using computer vision and text analysis
- Data extraction from documents using OCR and LLM processing
- Photo validation for compliance with international standards
- Face detection and biometric analysis
- Support for both single-page and multi-page documents
- Caching system for improved performance
- Comprehensive logging and monitoring

## API Endpoints

### `/process`
Process and extract data from documents
- **Input**: Document file
- **Output**: Extracted data in standardized JSON format

### `/validImage` 
Validate photos against standard requirements
- **Input**: Image file
- **Output**: Validation results and analysis

### `/extract_with_category`
Process documents with specified category
- **Input**: Document file and category
- **Output**: Extracted data based on document type

### `/live`
Health check endpoint
- **Output**: API status

## Setup

1. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2. **Configure environment variables:**
    ```bash
    AZURE_STORAGE_CONNECTION_STRING=
    AZURE_STORAGE_CONTAINER_NAME=
    AZURE_STORAGE_ACCOUNT_NAME=
    AZURE_STORAGE_ACCOUNT_KEY=
    AZURE_FACE_API_KEY=
    AZURE_FACE_API_ENDPOINT=
    AZURE_COMPUTERVISION_OCR_SUBSCRIPTION_KEY=
    AZURE_COMPUTERVISION_OCR_ENDPOINT=
    NURONAI_API_KEY=
    NURONAI_API_KEY2=
    NURONAI_API_KEY_LOCAL=             
    openai_key=
    openai_endpoint=
    azure_openai_api_endpoint=
    azure_openai_api_key=
    azure_openai_api_modelgpt4o=
    azure_openai_api_version=
    sql_username=
    sql_password=
    cache_db_name=
    sql_port=
    host=
    LOG_TABLE_NAME=
    FACE_TABLE_NAME=
    cache_table_name=
    POPPLER_PATH= 
    CSV_LOG_PATH= 
    LOGPATH=
    ```

3. **Start the server:**
    ```bash
    python -m uvicorn fast_api:app --port 5321
    ```
    The server will start on `http://127.0.0.1:5321` with 4 worker processes.

## Architecture

The service is built using:
- **FastAPI** for the REST API
- **Azure Cognitive Services** for:
  - OCR
  - Face Detection
  - Computer Vision
- **Azure Blob Storage** for file storage
- **PostgreSQL** for logging and caching
- **Custom ML models** for document classification

## Logging

The service includes comprehensive logging:
- Request/response logging
- Error tracking using 'debug logging'
- SQL database logging
- CSV logging for analytics

## Dependencies

- Python 3.12+
- FastAPI
- Azure SDK (for OpenaiLLM, FaceAPI, AzureOcr)
- OpenCV
- Pillow
- SQLAlchemy
- Other requirements listed in `requirements.txt`

## Error Handling

The API includes robust error handling for:
- Invalid API keys
- File format issues
- Processing failures
- Service unavailability
