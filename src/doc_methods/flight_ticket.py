from src.azure_services.llm import call_llm
import json, os
from pydantic import BaseModel
from src.logging.logger import debug_log

with open(os.path.join('assests', 'airports.json'), 'r') as file:
    AIRPORT_JSON = json.load(file)
file.close()

def flight_ticket_llm(source_text_string : str , FLIGHTTICKET_PROMPT : str , FlightTicketSchema : BaseModel , request_id):
    try:
        response = call_llm(source_text_string ,FLIGHTTICKET_PROMPT , FlightTicketSchema , request_id)
        if response.get("journey_details"):
            print("journey_details is not NONE")

            journey_details  =response.get("journey_details")
            # print("journey_details------>" , journey_details)
            for journey_det in journey_details :

                if journey_det.get("origin_airport_code")!= None:
                    origin_airport_code = journey_det.get("origin_airport_code").upper()
                    origin_country_name = AIRPORT_JSON.get(origin_airport_code).get("country")
                    journey_det["origin_country_name"] = origin_country_name.upper()

                if journey_det.get("destination_airport_code")!= None:
                    destination_airport_code = journey_det.get("destination_airport_code").upper()
                    destination_country_name = AIRPORT_JSON.get(destination_airport_code).get("country")
                    journey_det["destination_country_name"] = destination_country_name.upper()
        return response
    except Exception as e:
        debug_log(f"Exception in flight_ticket_llm as {str(e)} ", "flight_ticket_llm", request_id)
        return response