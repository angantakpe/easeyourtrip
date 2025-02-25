import datetime

def multi_page_doc_base_handler(pages:list[dict]):
    def check_multi(pages:list[dict], page_name:str):
        return ( 
            sum(map(lambda page: page.get("page_name", "").lower() == page_name.lower(), pages)) 
                > 
            1
        )
    
    if check_multi(pages, "account statement"):
        return handle_multi_account_st(pages)
    if check_multi(pages, "itinerary"):
        return handle_multi_itinerary(pages)


def handle_multi_account_st(pages: dict):
    def parse_date(date_str):
        try:
            return datetime.datetime.strptime(date_str, "%d/%m/%Y")
        except (ValueError, TypeError):
            return None
    
    account_statements = [
        page for page in pages if page.get("page_name", "").lower() == "account statement"
    ]
    latest_entry = None
    latest_date = None
    
    for entry in account_statements:
        entry_date = parse_date(entry.get("data", {}).get("date"))
        if entry_date and (latest_date is None or entry_date > latest_date):
            latest_entry = entry
            latest_date = entry_date

    if latest_entry:
        latest_data = latest_entry.get("data")
        for entry in account_statements:
            entry["data"] = latest_data
    
    return pages


def handle_multi_itinerary(pages: dict):
    for page in pages:
        if page.get("page_name", "").lower() == "itinerary":
            country_stay_list = page["data"].get("country_stay_list", [])
            merged_list = []
            for stay in country_stay_list:
                if merged_list and merged_list[-1]["country"] == stay["country"]:
                    merged_list[-1]["departure_date"] = stay["departure_date"] or merged_list[-1]["departure_date"]
                    merged_list[-1]["num_of_days"] = str(
                        int(merged_list[-1]["num_of_days"]) + int(stay["num_of_days"])
                    )
                else:
                    merged_list.append(stay)
            page["data"]["country_stay_list"] = merged_list
    
    return pages
