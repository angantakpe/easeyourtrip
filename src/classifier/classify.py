from src.classifier.clip_embedding import *
from src.azure_services.llm import openaiclient_textemb 
from dotenv import load_dotenv
import json
import pandas as pd
from src.logging.sql_log import ENGINE
load_dotenv(override= True)


with open('./assests/img_textclass.json') as file:
    PAGE_CLASS = json.load(file)
file.close()

def fetch_df(query,engine):
    try:
        data = pd.read_sql(query,engine)
        data_json =  data.to_dict(orient='records')
        return (True,data_json[0])
    except Exception as e:
        print(400,f"exception occured: {str(e)}","fetch_df")
        return (False,"No info fetched")


def get_category(emb, csv_row):
    try:
        querry = f"SELECT id, category, (embeddings <=> '{emb[0]}') AS similarity FROM public.image_embedding_clip  ORDER BY similarity ASC LIMIT 1"
        status, image_embedding_record = fetch_df(querry, ENGINE)
        option = image_embedding_record.get("category")
        # append_csv(csv_row , str(similar_img['distances'][0][0]))
        return option
    except Exception as e:
        print("Exception in get_category as :", str(e))
        return None


def get_category_text(input_text ,img_cat , csv_row , sql_dict):
    try:
        text_features  = get_embedding_openai(input_text)
        text_emb = text_features
        distance = 1
        similar_img_new = None
        for i in range(len(PAGE_CLASS[img_cat])):
            # print("img_cat i:::>>" , PAGE_CLASS[img_cat][i])
            querry = f"SELECT id, category, (embeddings <=> '{text_emb}') AS similarity FROM public.text_embedding_ada where category = '{PAGE_CLASS[img_cat][i]}' ORDER BY similarity ASC LIMIT 1"
            status, text_embedding_record = fetch_df(querry, ENGINE)

            current_distance = text_embedding_record.get('similarity')

            if float(current_distance) < float(distance):
                similar_img_new = text_embedding_record
                distance = current_distance

        option = similar_img_new.get("category")
        dist = float(str(similar_img_new['similarity']))*100

        if float(str(dist))>13.5:   
            option = 'other'
        sql_dict.update({"text_class" : similar_img_new.get("category") ,"distance": dist , "final_page_class" :option  })

        return option
        
    except Exception as e:
        print("Exception in get_category_text as ::::", str(e))
        return None


def get_embedding_openai(text):
    try:
        embed = openaiclient_textemb.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        ).data[0].embedding
        return embed
    except Exception as e:
        print("Exception in get_embedding_openai as ::::", str(e))
