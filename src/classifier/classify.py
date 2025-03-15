from src.classifier.clip_embedding import *
from src.azure_services.llm import openaiclient_textemb
from dotenv import load_dotenv
import json
import pandas as pd
from src.caching.cache_func import ENGINE
from src.logging.external_service_logger import (
    log_external_request,
    log_external_response,
)
from src.logging.logger import debug_log

load_dotenv(override=True)


with open("./assests/img_textclass.json") as file:
    PAGE_CLASS = json.load(file)
file.close()


def fetch_df(query, engine, request_id=None):
    try:
        # Log the database query request
        request_log = None
        if request_id:
            request_payload = {"query": query}
            request_log = log_external_request(
                "Database", "query", request_payload, request_id
            )

        data = pd.read_sql(query, engine)
        data_json = data.to_dict(orient="records")

        # Log the successful response
        if request_id and request_log:
            response_data = {"status": True, "record_count": len(data_json)}
            log_external_response(
                "Database",
                "query",
                response_data,
                request_id,
                request_log_file=request_log,
            )

        return (True, data_json[0])
    except Exception as e:
        print(400, f"exception occured: {str(e)}", "fetch_df")

        # Log the error
        if request_id and "request_log" in locals() and request_log:
            log_external_response(
                "Database",
                "query",
                None,
                request_id,
                status_code=500,
                error=str(e),
                request_log_file=request_log,
            )

        return (False, "No info fetched")


def get_category(emb, csv_row, request_id):
    try:
        querry = f"SELECT id, category, (embeddings <=> '{emb[0]}') AS similarity FROM public.image_embedding_clip ORDER BY similarity ASC LIMIT 1"
        status, image_embedding_record = fetch_df(querry, ENGINE, request_id)

        # Check if the fetch was successful before accessing the result
        if status:
            option = image_embedding_record.get("category")
            # append_csv(csv_row , str(similar_img['distances'][0][0]))
            return option
        else:
            debug_log(
                f"Failed to fetch image embedding record: {image_embedding_record}",
                "img_process",
                request_id,
            )
            return None
    except Exception as e:
        debug_log(f"Exception in get_category as {str(e)} ", "img_process", request_id)
        return None


def get_category_text(input_text, img_cat, csv_row, sql_dict, request_id):
    try:
        # Log the OpenAI embedding request
        embedding_request_log = log_external_request(
            "OpenAI", "text_embedding", {"text_length": len(input_text)}, request_id
        )

        text_features = get_embedding_openai(input_text, request_id)

        # Log the OpenAI embedding response
        if text_features:
            log_external_response(
                "OpenAI",
                "text_embedding",
                {"embedding_dimensions": len(text_features)},
                request_id,
                request_log_file=embedding_request_log,
            )
        else:
            log_external_response(
                "OpenAI",
                "text_embedding",
                None,
                request_id,
                status_code=500,
                error="Failed to get embedding",
                request_log_file=embedding_request_log,
            )
            return None

        text_emb = text_features
        distance = 1
        similar_img_new = None
        for i in range(len(PAGE_CLASS[img_cat])):
            # print("img_cat i:::>>" , PAGE_CLASS[img_cat][i])
            querry = f"SELECT id, category, (embeddings <=> '{text_emb}') AS similarity FROM public.text_embedding_ada where category = '{PAGE_CLASS[img_cat][i]}' ORDER BY similarity ASC LIMIT 1"
            status, text_embedding_record = fetch_df(querry, ENGINE, request_id)

            # Check if the fetch was successful before accessing the result
            if not status:
                debug_log(
                    f"Failed to fetch text embedding record for category {PAGE_CLASS[img_cat][i]}: {text_embedding_record}",
                    "img_process",
                    request_id,
                )
                continue

            current_distance = text_embedding_record.get("similarity")

            if float(current_distance) < float(distance):
                similar_img_new = text_embedding_record
                distance = current_distance

        # Check if we found any valid embedding
        if similar_img_new is None:
            debug_log(
                f"No valid text embedding found for any category",
                "img_process",
                request_id,
            )
            return "other"

        option = similar_img_new.get("category")
        dist = float(str(similar_img_new["similarity"])) * 100

        if float(str(dist)) > 13.5:
            option = "other"
        sql_dict.update(
            {
                "text_class": similar_img_new.get("category"),
                "distance": dist,
                "final_page_class": option,
            }
        )

        return option

    except Exception as e:
        debug_log(
            f"Exception in get_category_text as {str(e)} ", "img_process", request_id
        )
        return None


def get_embedding_openai(text, request_id):
    try:
        # Log is already handled in the calling function
        embed = (
            openaiclient_textemb.embeddings.create(
                model="text-embedding-ada-002", input=text
            )
            .data[0]
            .embedding
        )
        return embed
    except Exception as e:
        debug_log(
            f"Exception in get_embedding_openai as {str(e)} ", "img_process", request_id
        )
        return None
