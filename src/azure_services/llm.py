import os , openai , json
from openai import AzureOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
import time
from src.logging.logger import debug_log
load_dotenv(override = True)


openaiClient = AzureOpenAI(
        azure_endpoint = os.environ.get("azure_openai_api_endpoint"), 
        api_version=os.environ.get("azure_openai_api_version"),
        api_key = os.environ.get("azure_openai_api_key")
        )

openaiclient_textemb = openai.AzureOpenAI(
    azure_endpoint=os.getenv("openai_endpoint"),
    api_key=os.getenv("openai_key"),
    api_version="2023-05-15"
)



def call_llm( input_text : str  , messages : list , baseclass:BaseModel , request_id ):
    try:
        for i in range(3):
            try:
                messages[-1]["content"] = messages[-1]["content"].format(input_text)        
                response = openaiClient.beta.chat.completions.parse(
                    model="gpt-4o", # replace with the model deployment name of your gpt-4o 2024-08-06 deployment
                    messages =messages,
                    max_tokens=1000, 
                    temperature=0.7,
                    response_format =baseclass)

                content = response.choices[0].message.content
                # print("response_json::message>>>>" , response.choices[0].message)
                response_json = json.loads(str(content))
                validate_response_json = baseclass(**response_json)
                final_response = validate_response_json.dict()
                return final_response
            except Exception as e:
                debug_log(f"Exception in {i} request of calling openai as {str(e)} ", "call_llm", request_id)
                time.sleep(60)
        return dict(baseclass(**{field: None for field in baseclass.__fields__}))        
    except Exception as e:
        debug_log(f"Exception in call_llm as {str(e)} ", "call_llm", request_id)
        return dict(baseclass(**{field: None for field in baseclass.__fields__}))




