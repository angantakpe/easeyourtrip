from sqlalchemy import (
    create_engine,
    Column,
    String,
    JSON,
    Table,
    MetaData,
    DateTime,
    select,
    literal,
    insert,
    exists,
    delete,
)
from sqlalchemy.sql import not_
import os
import sqlalchemy
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv
from src.logging.external_service_logger import (
    log_external_request,
    log_external_response,
)
from src.logging.logger import debug_log

load_dotenv(override=True)
# Database URI for PostgreSQL
user_name = os.getenv("SQL_USERNAME")
password = os.getenv("SQL_PASSWORD")
cache_db = os.getenv("CACHE_DB_NAME")
port_no = os.getenv("SQL_PORT")
host = os.getenv("HOST")
Cache_table_name = os.getenv("CACHE_TABLE_NAME")
DATABASE_URI = (
    f"postgresql+psycopg2://{user_name}:{password}@{host}:{port_no}/{cache_db}"
)
ENGINE = create_engine(DATABASE_URI, pool_recycle=1000, pool_pre_ping=True)
METADATA = MetaData()

# Define the cache table globally, only once
CACHE_TABLE = Table(
    Cache_table_name,
    METADATA,
    Column("id", String(), primary_key=True),
    Column("hash", String()),
    Column("date", DateTime),
    Column("data", String(), nullable=False),
)


def insert_cache(image_hash, image_data, request_id=None):
    try:
        # Log the cache insert request
        request_log = None
        if request_id:
            request_payload = {
                "hash": str(image_hash),
                "data_size": len(json.dumps(image_data)),
            }
            request_log = log_external_request(
                "Cache", "insert", request_payload, request_id
            )

        # Ensure the table exists
        # get_cache_table()
        # Convert image data to JSON
        image_data_js = json.dumps(image_data)
        # Prepare the insert statement
        # stmt = CACHE_TABLE.insert().values(id=str(uuid.uuid4()), hash=str(image_hash), data=image_data_js, date=datetime.now())
        sel = select(
            literal(str(uuid.uuid4())),
            literal(str(image_hash)),
            literal(image_data_js),
            literal(datetime.now()),
        ).where(
            not_(
                exists().where(CACHE_TABLE.c.hash == str(image_hash))
            )  # Check if no row with id=1 exists
        )
        # Insert the selected values (if the condition is met)
        ins = insert(CACHE_TABLE).from_select(["id", "hash", "data", "date"], sel)

        with ENGINE.connect() as connection:
            with connection.begin():  # Begin a transaction
                connection.execute(ins)
        print("Added to db")

        # Log the successful response
        if request_id and request_log:
            response_data = {"status": "success", "hash": str(image_hash)}
            log_external_response(
                "Cache",
                "insert",
                response_data,
                request_id,
                request_log_file=request_log,
            )

    except Exception as e:
        print("Exception in insert_cache:", str(e))

        # Log the error
        if request_id and "request_log" in locals() and request_log:
            log_external_response(
                "Cache",
                "insert",
                None,
                request_id,
                status_code=500,
                error=str(e),
                request_log_file=request_log,
            )


def get_cache_data(image_hash, request_id=None):
    try:
        # Log the cache get request
        request_log = None
        if request_id:
            request_payload = {"hash": str(image_hash)}
            request_log = log_external_request(
                "Cache", "get", request_payload, request_id
            )

        # get_cache_table()
        select_query = select(CACHE_TABLE.c.data).where(
            CACHE_TABLE.c.hash == str(image_hash)
        )
        # print(f"select_query: {select_query}")
        with ENGINE.connect() as connection:
            result = connection.execute(
                select_query
            ).fetchone()  # Fetch one matching row
            if result is not None:
                print("result:")
                img_data = json.loads(result[0])

                # Log the successful response
                if request_id and request_log:
                    response_data = {
                        "status": "success",
                        "hash": str(image_hash),
                        "data_found": True,
                        "data_size": len(result[0]),
                    }
                    log_external_response(
                        "Cache",
                        "get",
                        response_data,
                        request_id,
                        request_log_file=request_log,
                    )

                return img_data  # Return the data column value
            else:
                print(f"No cache found for the hash: {image_hash}")

                # Log the not found response
                if request_id and request_log:
                    response_data = {
                        "status": "not_found",
                        "hash": str(image_hash),
                        "data_found": False,
                    }
                    log_external_response(
                        "Cache",
                        "get",
                        response_data,
                        request_id,
                        request_log_file=request_log,
                    )

                return None
    except Exception as e:
        print("Exception in get_cache_by_hash:", str(e))

        # Log the error
        if request_id and "request_log" in locals() and request_log:
            log_external_response(
                "Cache",
                "get",
                None,
                request_id,
                status_code=500,
                error=str(e),
                request_log_file=request_log,
            )

        return None


def get_cache_table():
    """Ensures the table exits the Dataabase. If not create it."""
    try:
        if not sqlalchemy.inspect(ENGINE).has_table(
            Cache_table_name
        ):  # If table doesn't exist, create it.
            METADATA.create_all(ENGINE)  # Create tables in the database
    except Exception as e:
        print("Exception in get_cache_table:", str(e))


def delete_cache(image_hash, request_id=None):
    try:
        # Log the cache delete request
        request_log = None
        if request_id:
            request_payload = {"hash": str(image_hash)}
            request_log = log_external_request(
                "Cache", "delete", request_payload, request_id
            )

        # get_cache_table()
        delete_query = delete(CACHE_TABLE).where(CACHE_TABLE.c.hash == str(image_hash))

        with ENGINE.connect() as connection:
            result = connection.execute(delete_query)
            connection.commit()

        # Log the successful response
        if request_id and request_log:
            response_data = {
                "status": "success",
                "hash": str(image_hash),
                "rows_deleted": result.rowcount,
            }
            log_external_response(
                "Cache",
                "delete",
                response_data,
                request_id,
                request_log_file=request_log,
            )

    except Exception as e:
        print("Exception in del_cache as ::", str(e))

        # Log the error
        if request_id and "request_log" in locals() and request_log:
            log_external_response(
                "Cache",
                "delete",
                None,
                request_id,
                status_code=500,
                error=str(e),
                request_log_file=request_log,
            )
