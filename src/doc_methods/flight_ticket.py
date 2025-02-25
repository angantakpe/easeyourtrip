from src.azure_services.llm import call_llm
import json, os
from pydantic import BaseModel

with open(os.path.join('assests', 'airports.json'), 'r') as file:
    AIRPORT_JSON = json.load(file)
file.close()

def flight_ticket_llm(source_text_string : str , FLIGHTTICKET_PROMPT : str , FlightTicketSchema : BaseModel):
    try:
        response = call_llm(source_text_string ,FLIGHTTICKET_PROMPT , FlightTicketSchema)
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
        print("Exception occured in flight_ticket_llm as ::", str(e))
        return response