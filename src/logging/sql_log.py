from sqlalchemy import create_engine, Column, String, Table, MetaData, DateTime,  insert
import os
import sqlalchemy
import uuid
from dotenv import load_dotenv
from src.logging.logger import debug_log
from src.caching.cache_func import METADATA , ENGINE
load_dotenv(override= True)


LOG_TABLE_NAME = os.getenv('LOG_TABLE_NAME')
FACE_TABLE_NAME= os.getenv('FACE_TABLE_NAME')


# Define the cache table globally, only once
LOG_TABLE = Table(
    LOG_TABLE_NAME , METADATA,
    Column('id', String(), primary_key=True),
    Column('request_id', String()),
    Column('page_start_time', DateTime),
    Column('api_key', String()),
    Column('filename', String()),
    Column('blob_file_name', String()),
    Column('file_type', String()),
    Column('page_no', String()),
    Column('total_pages', String()),
    Column('image_name', String()),
    Column('preprocessing_time', String()),
    Column('preprocess_image', String()),
    Column('pre_cached_status', String()),
    Column('hash_id', String()),
    Column('classification_time', String()),
    Column('class_of_page', String()),
    Column('ocr_time', String()),
    Column('text_class', String()),
    Column('distance', String()),
    Column('final_page_class', String()),
    Column('text_class_time', String()),
    Column('openai_time', String()),
    Column('face_api_time', String()),
    Column('final_time', String()),
    Column('total_page_time', String()),
    Column('response_file', String()),
    Column('page_status', String()),
    Column('page_remark', String()))
 

FACE_LOG_TABLE = Table(
    FACE_TABLE_NAME , METADATA,
    Column('id', String(), primary_key=True),
    Column('page_start_time', DateTime),
    Column('api_key', String()),
    Column('filename', String()),
    Column('blob_file_name', String()),
    Column('file_type', String()),
    Column('final_time', String()),
    Column('total_page_time', String()),
    Column('response_file', String()),
    Column('page_status', String()),
    Column('page_remark', String()))
 

def insert_log(log_dict , request_id):
    try:
        # Ensure the table exists, iif not make the table
        # get_log_table(LOG_TABLE_NAME)
        # Convert image data to JSON
        log_id = str(uuid.uuid4())
        # Insert the selected values (if the condition is met)
        log_dict.update({"id": log_id})
        debug_log(f"Inserting log in db as {log_dict}", "insert_log", request_id)

        # print("sql -difct new::" , log_dict)
        ins = insert(LOG_TABLE).values(log_dict)
        # Execute the insert operation
        with ENGINE.connect() as connection:
            with connection.begin():
                connection.execute(ins)
                debug_log("Inserted page log success", "insert_log", request_id)

    except Exception as e:
        debug_log(f"Inserted page log failed as: {str(e)}", "insert_log", request_id)
        print("Exception in insert_log:", str(e))


def insert_face_log(log_dict , request_id):
    try:
        # Ensure the table exists, iif not make the table
        # get_log_table(FACE_TABLE_NAME)
        # Convert image data to JSON
        log_id = str(uuid.uuid4())
        # Insert the selected values (if the condition is met)
        log_dict.update({"id": log_id})

        # print("sql -difct new::" , log_dict)
        debug_log(f"Inserting log in db as {log_dict}", "insert_log", request_id)

        
        ins = insert(FACE_LOG_TABLE).values(log_dict)
        # Execute the insert operation
        with ENGINE.connect() as connection:
            with connection.begin():
                connection.execute(ins)
                debug_log("Inserted page log success", "insert_log", request_id)

    except Exception as e:
        debug_log(f"Inserted page log failed as: {str(e)}", "insert_log", request_id)
        print("Exception in insert_log:", str(e))



def get_log_table(table_name):
    try:
        if not sqlalchemy.inspect(ENGINE).has_table(table_name):  # If table doesn't exist, create it.
            print("no table found")
            METADATA.create_all(ENGINE)  # Create tables in the database
    except Exception as e:
        print("Exception in get_cache_table:", str(e))

