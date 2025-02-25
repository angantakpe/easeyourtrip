from datetime import datetime, timedelta


def run_passport_validations(response):
    try:
        print("function started function: run_passport_validations")
        response_dup = {}
        is_passport = False
        response_dup["documents"] = {}
        passport_number = None
        passport_validations = {
            "passport_number_check": False,
            "passport_front": {
                "expiry_check" : False,
                "passport_number": False, 
                "front_page_check": False
                },
            "passport_back": {
                "back_page_check": False,
                "passport_number": False,
                },
            "status": True
            }
        doc_category = "Passport"
        
        if not ((doc_category in response["DocCategory"]) or (doc_category==response["DocCategory"])):
            return passport_validations
        else:
            #group passport pages
            for page in response["pages"]:
                if page["Category"] == "Passport":
                    if not is_passport:
                        response_dup["documents"]["Passport"] = {}
                        response_dup["documents"]["Passport"]["pages"] =[]
                        is_passport = True
                    response_dup["documents"]["Passport"]["pages"].append(page)
            # print("response_dup: ",str(response_dup))
            #iterate on passport pages
            for page in response_dup["documents"]["Passport"]["pages"]:
                if (page["page_name"] == "Passport_front") or (page["page_name"] == "Passport_back"):
                    if page["page_name"] == "Passport_front":
                        passport_validations["passport_front"]["front_page_check"]=True
                        if page["data"]["passport_number"]:
                            passport_validations["passport_front"]["passport_number"]=True
                    else:
                        passport_validations["passport_back"]["back_page_check"]=True
                        if page["data"]["passport_number"]:
                            passport_validations["passport_back"]["passport_number"]=True
                    # print("passport_number: ",passport_number)
                    # print("page['data']['passport_number']: ",page["data"]["passport_number"])
                    if passport_number==None:
                        passport_number = page["data"]["passport_number"]
                    elif passport_number == page["data"]["passport_number"]:
                        passport_validations["passport_number_check"] = True
                if page["page_name"] == "Passport_front":
                    # print("page['data']['passport_expiry_date']: ",page["data"]["passport_expiry_date"])
                    if is_six_months_ahead(page["data"]["passport_expiry_date"]):
                        passport_validations["expiry_check"] = True
        for key,value in passport_validations.items():
            if not value:
                passport_validations["status"]=False
        return passport_validations
    except Exception as e:
        print(f"exception occured: {str(e)} function: run_passport_validations")
        passport_validations["status"]=False
        return passport_validations

def validations(response , check_validation):
    try:
        if not check_validation:
            print("validation function started")
            response["document_validation"] = {}
            passport_pgs = 0
            other_pgs = 0
            if isinstance(response,dict):
                for key,value in response.items():
                    if key=="fileSize":
                        file_size_splits = value.split(" ")
                        if len(file_size_splits)>1:
                            if "MB"==file_size_splits[-1]:
                                print("file_size_splits: ",str(file_size_splits))
                                file_size = round(float(file_size_splits[0]), 2)
                                response[key] = str(file_size)+" MB"
                    if key=="readabilityScore":
                        if value and value !="":
                            # print("value: ",value)
                            readabilityScore=round(float(value),2)
                            response[key] = readabilityScore
                    if key=="pages":
                        for i,page in enumerate(value):
                            if "page_name" not in page.keys():
                                continue
                            page_category = page["page_name"]
                            temp = page_category.split("_")[0].lower()
                            print("page::cat:::", page_category , "temp::::", temp)
                            if temp == "passport":
                                passport_pgs = passport_pgs + 1
                            if temp == "other":
                                other_pgs = other_pgs + 1
                            if temp == "visa":
                                passport_pgs = passport_pgs + 1

                            doc_category = page["Category"]
                            if doc_category=="Photo":
                                if "isPass" in page.keys():
                                    # print("got ispass:::::::;", page.keys())
                                    response["document_validation"]["Photo"] = page["isPass"]
                                    page["validations"]={}
                                    page["validations"]["status"] = page["isPass"]
                                else:
                                    response["document_validation"]["Photo"] = False
                                    page["validations"] = {}
                                    page["validations"]["status"] = False
                            
                            if page_category == "Passport_front":
                                if not (page["data"]["mrz"] and ("<" in page["data"]["mrz"])):
                                    other_pgs = other_pgs + 1
                                    page["Category"]="other"
                                    page["page_name"]="other"
                                    page["data"]={}
                                    page["readabilityLevel"]="Poor"
                                    page["readabilityScore"]=-1
                                    passport_pgs = passport_pgs - 1
                                    if "readabilityLevel" in page.keys():
                                        page["validations"]={}
                                        page["validations"]["readability_status"] = True if page["readabilityLevel"]!="Poor" else False
                                        page["validations"]["status"] = page["validations"]["readability_status"]
                                        page["validations"]["readability_string"] = f"The readability score of the document is {page['readabilityLevel'].upper()} with Reading score of {int(max(page['readabilityScore'] , 0)*100)} %"

                                else:
                                    page["validations"] = {
                                        "status": True,
                                        "expiry_status": False,
                                        "readability_status": False
                                    }

                                    if page["data"]["passport_expiry_date"]:
                                        page["validations"]["expiry_status"]=is_six_months_ahead(page["data"]["passport_expiry_date"])
                                    else:
                                        page["validations"]["status"]=False

                                    page["validations"]["readability_string"] = f"The readability score of the document is {page['readabilityLevel'].upper()} with Reading score of {int(max(page['readabilityScore'] , 0)*100)} %"


                                    if page["readabilityLevel"]!="Poor":
                                        page["validations"]["readability_status"]=True
                                    else:
                                        page["validations"]["status"]=False

                            
                            elif page_category == "Passport_back":
                                page["validations"] = {
                                    "status": True,
                                    # "passport_number_status": False,
                                    "readability_status": False
                                }

                                if page["readabilityLevel"]!="Poor":
                                    page["validations"]["readability_status"]=True
                                else:
                                    page["validations"]["status"]=False
                                page["validations"]["readability_string"] = f"The readability score of the document is {page['readabilityLevel'].upper()} with Reading score of {int(max(page['readabilityScore'] , 0)*100)} %"
                            
                            else:
                                if "readabilityLevel" in page.keys():
                                    page["validations"]={}
                                    page["validations"]["readability_status"] = True if page["readabilityLevel"]!="Poor" else False
                                    page["validations"]["status"] = page["validations"]["readability_status"]
                                    page["validations"]["readability_string"] = f"The readability score of the document is {page['readabilityLevel'].upper()} with Reading score of {int(max(page['readabilityScore'] , 0)*100)} %"

                            if page_category=="other":
                                page["data"] = {}
                            
                            for key2,value2 in page.items():
                                if key2=="readabilityScore":
                                    if value2 and value2 !="":
                                        # print("value: ",str(value2))
                                        readabilityScore=round(float(value2),2)
                                        response[key][i][key2] = readabilityScore       
                if "DocCategory" in response.keys():
                    if isinstance(response["DocCategory"],list):

                        if passport_pgs==0 and "Passport" in response["DocCategory"]:

                            response["DocCategory"].remove("Passport")
                        if other_pgs>0 and "other" not in response["DocCategory"]:
                            print("other_pgs>0")        
                            response["DocCategory"].append("other")
                    if not isinstance(response["DocCategory"],list):
                        if (other_pgs>0) and (response["DocCategory"]!="other"):
                            response["DocCategory"]="other"

            return response
        
        else:
            return response
    except Exception as e:
        print(f"exception occured: {str(e)}, function: validations")
        return response


def is_six_months_ahead(given_date_str):
    try:
        print("function started function: is_six_months_ahead")
        # Parse date strings into datetime objects
        given_date = datetime.strptime(given_date_str, "%d/%m/%Y")
        current_date = datetime.now()
        # Calculate the difference (timedelta)
        six_months_ahead = current_date + timedelta(days=30 * 6)

        return given_date > six_months_ahead
    except Exception as e:
        print(f"exception occured: {str(e)} function: is_six_months_ahead")
        return False