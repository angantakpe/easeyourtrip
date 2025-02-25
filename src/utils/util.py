import pycountry
import cv2
import dateparser 
from datetime import datetime 
import re , os , pdf2image , uuid , json
# from geosky import geo_plug
from src.azure_services.cloud import upload_to_azure
import requests as r
from dotenv import load_dotenv
from PIL import Image
import requests 
from urllib.parse import urlsplit
import numpy as np
load_dotenv(override=True)
Image.MAX_IMAGE_PIXELS = None

with open(os.path.join('assests', 'page_name_new.json'), 'r') as f:
    PAGENAME_DATA = json.load(f)
f.close()    



def findCountryCode_alpha3(word):
    try:
        nationalities = {'AD': 'Andorran', 'AE': 'Emirian', 'AF': 'Afghani', 'AG': 'Antiguan', 'AI': 'Anguillan', 'AL': 'Albanian', 'AM': 'Armenian', 'AO': 'Angolan', 'AQ': 'Antarctic', 'AR': 'Argentine', 'AS': 'Samoan', 'AT': 'Austrian', 'AU': 'Australian', 'AW': 'Arubian', 'AX': 'Ålandic', 'AZ': 'Azerbaijani', 'BA': 'Bosnian', 'BB': 'Barbadian', 'BD': 'Bangladeshi', 'BE': 'Belgian', 'BF': 'Burkinabe', 'BG': 'Bulgarian', 'BH': 'Bahrainian', 'BI': 'Burundian', 'BJ': 'Beninese', 'BL': 'Barthélemois', 'BM': 'Bermudan', 'BN': 'Bruneian', 'BO': 'Bolivian', 'BQ': '', 'BR': 'Brazilian', 'BS': 'Bahameese', 'BT': 'Bhutanese', 'BV': '', 'BW': 'Motswana', 'BY': 'Belarusian', 'BZ': 'Belizean', 'CA': 'Canadian', 'CC': 'Cocossian', 'CD': 'Congolese', 'CF': 'Central African', 'CG': 'Congolese', 'CH': 'Swiss', 'CI': 'Ivorian', 'CK': 'Cook Islander', 'CL': 'Chilean', 'CM': 'Cameroonian', 'CN': 'Chinese', 'CO': 'Colombian', 'CR': 'Costa Rican', 'CU': 'Cuban', 'CV': 'Cape Verdean', 'CW': 'Curaçaoan', 'CX': 'Christmas Islander', 'CY': 'Cypriot', 'CZ': 'Czech', 'DE': 'German', 'DJ': 'Djiboutian', 'DK': 'Danish', 'DM': 'Dominican', 'DO': 'Dominican', 'DZ': 'Algerian', 'EC': 'Ecuadorean', 'EE': 'Estonian', 'EG': 'Egyptian', 'EH': 'Western Saharan', 'ER': 'Eritrean', 'ES': 'Spanish', 'ET': 'Ethiopian', 'FI': 'Finnish', 'FJ': 'Fijian', 'FK': 'Falkland Islander', 'FM': 'Micronesian', 'FO': 'Faroese', 'FR': 'French', 'GA': 'Gabonese', 'GB': 'British', 'GD': 'Grenadian', 'GE': 'Georgian', 'GF': 'French Guianese', 'GG': '', 'GH': 'Ghanaian', 'GI': 'Gibraltarian', 'GL': 'Greenlander', 'GM': 'Gambian', 'GN': 'Guinean', 'GP': 'Guadeloupean', 'GQ': 'Equatorial Guinean', 'GR': 'Greek', 'GS': '', 'GT': 'Guatemalan', 'GU': 'Guamanian', 'GW': 'Guinean', 'GY': 'Guyanese', 'HK': 'Hong Konger', 'HM': '', 'HN': 'Honduran', 'HR': 'Croatian', 'HT': 'Haitian', 'HU': 'Hungarian', 'ID': 'Indonesian', 'IE': 'Irish', 'IL': 'Israeli', 'IM': 'Manx', 'IN': 'Indian', 'IO': '', 'IQ': 'Iraqi', 'IR': 'Iranian', 'IS': 'Icelander', 'IT': 'Italian', 'JE': '', 'JM': 'Jamaican', 'JO': 'Jordanian', 'JP': 'Japanese', 'KE': 'Kenyan', 'KG': 'Kyrgyzstani', 'KH': 'Cambodian', 'KI': 'I-Kiribati', 'KM': 'Comoran', 'KN': 'Kittian', 'KP': 'North Korean', 'KR': 'South Korean', 'KW': 'Kuwaiti', 'KY': 'Caymanian', 'KZ': 'Kazakhstani', 'LA': 'Laotian', 'LB': 'Lebanese', 'LC': 'Saint Lucian', 'LI': 'Liechtensteiner', 'LK': 'Sri Lankan', 'LR': 'Liberian', 'LS': 'Mosotho', 'LT': 'Lithunian', 'LU': 'Luxembourger', 'LV': 'Latvian', 'LY': 'Libyan', 'MA': 'Moroccan', 'MC': 'Monacan', 'MD': 'Moldovan', 'ME': 'Montenegrin', 'MF': '', 'MG': 'Malagasy', 'MH': 'Marshallese', 'MK': 'Macedonian', 'ML': 'Malian', 'MM': 'Myanmarese', 'MN': 'Mongolian', 'MO': 'Macanese', 'MP': 'Northern Mariana Islander', 'MQ': 'Martinican', 'MR': 'Mauritanian', 'MS': 'Montserratian', 'MT': 'Maltese', 'MU': 'Mauritian', 'MV': 'Maldivan', 'MW': 'Malawian', 'MX': 'Mexican', 'MY': 'Malaysian', 'MZ': 'Mozambican', 'NA': 'Namibian', 'NC': 'New Caledonian', 'NE': 'Nigerien', 'NF': 'Norfolk Islander', 'NG': 'Nigerian', 'NI': 'Nicaraguan', 'NL': 'Dutch', 'NO': 'Norwegian', 'NP': 'Nepalese', 'NR': 'Nauruan', 'NU': 'Niuean', 'NZ': 'New Zealander', 'OM': 'Omani', 'PA': 'Panamanian', 'PE': 'Peruvian', 'PF': 'French Polynesian', 'PG': 'Papua New Guinean', 'PH': 'Filipino', 'PK': 'Pakistani', 'PL': 'Polish', 'PM': 'Saint-Pierrais', 'PN': 'Pitcairn Islander', 'PR': 'Puerto Rican', 'PS': 'Palestinian', 'PT': 'Portuguese', 'PW': 'Palauan', 'PY': 'Paraguayan', 'QA': 'Qatari', 'RE': '', 'RO': 'Romanian', 'RS': 'Serbian', 'RU': 'Russian', 'RW': 'Rwandan', 'SA': 'Saudi Arabian', 'SB': 'Solomon Islander', 'SC': 'Seychellois', 'SD': 'Sudanese', 'SE': 'Swedish', 'SG': 'Singaporean', 'SH': 'Saint Helenian', 'SI': 'Slovenian', 'SJ': '', 'SK': 'Slovakian', 'SL': 'Sierra Leonean', 'SM': 'Sanmarinese', 'SN': 'Senegalese', 'SO': 'Somali', 'SR': 'Surinamer', 'SS': 'Sudanese', 'ST': 'São Tomean', 'SV': 'Salvadorean', 'SX': '', 'SY': 'Syrian', 'SZ': 'Swazi', 'TC': 'Turks and Caicos Islander', 'TD': 'Chadian', 'TF': '', 'TG': 'Togolese', 'TH': 'Thai', 'TJ': 'Tajikistani', 'TK': 'Tokelauan', 'TL': 'Timorese', 'TM': 'Turkmen', 'TN': 'Tunisian', 'TO': 'Tongan', 'TR': 'Turkish', 'TT': 'Trinidadian', 'TV': 'Tuvaluan', 'TW': 'Taiwanese', 'TZ': 'Tanzanian', 'UA': 'Ukrainian', 'UG': 'Ugandan', 'UM': '', 'US': 'American', 'UY': 'Uruguayan', 'UZ': 'Uzbekistani', 'VA': '', 'VC': 'Saint Vincentian', 'VE': 'Venezuelan', 'VG': 'Virgin Islander', 'VI': 'Virgin Islander', 'VN': 'Vietnamese', 'VU': 'Ni-Vanuatu', 'WF': 'Wallisian', 'WS': 'Samoan', 'YE': 'Yemeni', 'YT': 'Mahoran', 'ZA': 'South African', 'ZM': 'Zambian', 'ZW': 'Zimbabwean'}
        for country in pycountry.countries:
            if word.lower() == country.alpha_3.lower():
                return {"country":country.name, "countryCode":country.alpha_3, "Nationality":nationalities.get(country.alpha_2, country.name)}
        return None
    except Exception as e:
        print("Exception in findCountryCode_alpha3 as :", str(e))
        return None

def getSortedDates(dates, desc=True):
    try:
        date_objects = [datetime.strptime(date_str, '%d/%m/%Y') for date_str in dates]

        # Sort the date objects
        sorted_dates = sorted(date_objects,reverse=desc)

        # Convert the sorted date objects back to strings in 'dd/mm/yyyy' format
        sorted_date_strings = [date.strftime('%d/%m/%Y') for date in sorted_dates]

        # Print the resulting list
        return sorted_date_strings
    except Exception as e:
        print("exception in getSortedDates as :: ", str(e))
        return []
    

def save_uploadedfile(uploadedfile,filename,ext):
    try:
        filename_without_ext = os.path.splitext(os.path.basename(filename))[0]
        filepath = os.path.join("static",f'{filename_without_ext}.{ext}')
        with open(filepath,"wb") as f:
            f.write(uploadedfile)
        f.close()
    except Exception as e:
        print("Exception in save_uploadedfile as :", str(e))

     

#validatin API key , if invalid then saving the file on blob and returning error message
def validate_apikey(apikey ,image_name ,jsonObj ,tempFilePaths ):
    if apikey not in [os.environ.get('NURONAI_API_KEY') , os.environ.get('NURONAI_API_KEY2') , os.environ.get('NURONAI_API_KEY_LOCAL') ]:
        jsonObj["requestResponse"] = "Please provide a valid api key."
        with open("static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json", "w") as f:
            json.dump(jsonObj, f)
        f.close()
        file_path = "static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
        file_name = image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
        upload_to_azure(file_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)
        # print("temperory stored file: ",tempFilePaths)
        # deleteFiles(tempFilePaths)
        return False
    else:
        if apikey == str(os.getenv('NURONAI_API_KEY')) or apikey == str(os.getenv('NURONAI_API_KEY2')):
            jsonObj["user"] = "Nuronai"
        elif apikey == str(os.getenv('NURONAI_API_KEY_LOCAL')):
            jsonObj["user"] = "InteligenAI"
        return True

def findCountry(stringText):
    try:
        for country in pycountry.countries:
            if country.name.lower() in stringText.lower():
                return country.name.lower()
        for country in pycountry.countries:
            for w in stringText.split():
                if w.lower == country.alpha_3.lower():
                    return country.name.lower()
        for country in pycountry.countries:
            for w in stringText.split():
                if w.lower == country.alpha_2.lower():
                    return country.name.lower()
        return None
    except Exception as e:
        print("Exception in findCountry as :", str(e))
        return None

#The function splits the image name by periods (.) to separate the base name from the extension. 
# It then reconstructs the image name without any periods in between the name components, adds a specified suffix to the base name, and finally appends the original file extension. 
def generateName(img_name, suffix):
    try:
        names = img_name.split(".") # Split the image name by periods to separate the name from the file extension
        imagename = ""
        for (i,name) in enumerate(names):
            if i == (len(names)-1):
                break # Stop before the last element (which is the file extension)
            imagename += names[i]
        imagename = imagename +suffix+"."+names[-1] # Concatenate the name parts back together
        return imagename
    except Exception as e:
        print("Exception in generate names as:", str(e))


#calculates the average DPI of the image
def getDPI(image_path):
    try:
        def getFinalDPI(image_path):
            def getDimensions(height, width):
                #converting pixcels into millimeter
                height = height / 37.7952755906
                width = width / 37.7952755906
                #returning the diamentions into inches
                return height*0.393701 , width*0.393701

            image = cv2.imread(image_path)
            height, width, _ = image.shape
            
            height_in, width_in = getDimensions(height, width)
            #calculating dots per inch (DPI)
            dpiHeight = round(height / height_in)
            dpiWidth = round(width / width_in)
            return dpiHeight, dpiWidth
        
        image = Image.open(image_path)

        try:
            dpi = image.info["dpi"]
        except Exception as e:
            dpi = getFinalDPI(image_path)
        image.close()
        #returning average DPI of the image
        return round(sum(dpi)/2)
    except Exception as e:
        print("Exception in getDPI as:", str(e))



#returns array of PIL object of Pdf pages.
def pdf_to_jpeg(pdf_file):
    try:
        poppler_path = os.getenv('POPPLER_PATH')
        images = pdf2image.convert_from_path(pdf_file,poppler_path=poppler_path)
        return images
    except Exception as e:
        print("Exception in pdf_to_jpeg as :", str(e))
        return []

#takes PIL object of pdf images and checks if they are more than 10000 pixcels in height or width
def check_doc_pixels(pil_obj):
    try:
        """If a image or Pdf page is above 10000 pixcels in width or height Azure Ocr does not works on it. Resizing such 
        images to  a theosold so document quality does not gets altered."""
        width ,height= pil_obj.size
        aspect_ratio = float(width /height)
        max_dimension = 10000
        if height>max_dimension or width>max_dimension:
            if height>width:
                new_height = int(height/2.77)
                new_width = int(new_height * aspect_ratio)
            else:    
                new_width = int(width/2.77)              
                new_height = int(new_width * aspect_ratio) 
            resize_pil =  pil_obj.resize((new_width , new_height) )   
            res_width ,res_height = resize_pil.size
            if res_height> max_dimension or res_width> max_dimension :
                return check_doc_pixels(resize_pil)
            return resize_pil
        else:
            return pil_obj

    except Exception as e:
        print("Exception in check_pdf_pixels as::", str(e))
        return pil_obj


def deleteFiles(imagePaths):
    try:
        for path in imagePaths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print("exception while deleting file in error: ",e)
                    continue                        
                print("deleted temporary file")
    except Exception as e:
        print("Exception while deleting file in error: ",str(e))


def find_dates(text):
    try:
        date_patterns = [
            r'\b\d{1,2}(?:st|nd|rd|th)?\s+\w+,\s+\d{4}\b',  # 5th of June, 2024
            r'\b\w+\s+\d{1,2},\s+\d{4}\b',                      # June 5, 2024
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',                       # 05/06/2024
            r'\b\d{4}\s*-\s*\d{1,2}\s*-\s*\d{1,2}\b', 
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',           

            r'\b\d{1,2}\s*-\s*\d{1,2}\s*-\s*\d{4}\b',
            r'\b\d{1,2}\s*\.\s*\d{1,2}\s*\.\s*\d{4}\b',
            r'\b\d{1,2}\s*\d{1,2}\s*\d{4}\b',
            r'\b\d{1,2}.\d{1,2}.\d{4}\b',
            r'\d{2}s*[A-Z]{3}s*\d{4}',
            r'\d{2}-[A-Z]{3}-\d{4}',
            r'\b\d{1,2}\s*(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*\d{2}\b',
            r'\b\d{1,2}\s*(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*\d{4}\b',
            r'\b\d{1,2}\s*-\s*(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*-\s*\d{4}\b',
            r'\b\d{1,2}\s*(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s*\d{4}\b',
            r'\b\d{1,2}\s*(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s*\d{2}\b'
                                                                                                
        ]

        matches = []
        for pattern in date_patterns:
            matches.extend(re.findall(pattern, text))

        dates = []
        for match in matches:
            parsed_date = dateparser.parse(match )
            if parsed_date:
                dates.append(parsed_date)
                
        sorted_dates = sorted(dates, key=lambda x: (x.year, x.month, x.day))
        
        formatted_dates = [date.strftime('%d/%m/%Y') for date in sorted_dates]

        return formatted_dates
    
    except Exception as e:
        print("Exception in find_dates as ::", str(e))
        return []
    


def  pagecatname(image_schema , new_cat ):
    global PAGENAME_DATA
    try:
        if new_cat in PAGENAME_DATA["page_name"].keys():
            image_schema["page_name"] = PAGENAME_DATA["page_name"][new_cat]
            image_schema["Category"]=  PAGENAME_DATA["Category"][new_cat]
            # print("image schema::::::::" , image_schema)

        return image_schema    
    except Exception as e:
        print("Exception in pagecatname as::", str(e))
        image_schema =  image_schema.update({"page_name" : "other" , "Category" :  "other"} )
        return image_schema


def save_and_gen_filepath(uploaded_filename , file_content ,tempFilePaths ):
    try:
        file_extension = uploaded_filename.split(".")[-1]
        try:
            file_extension = file_extension.lower()
        except Exception as e:
            print(f"Exception in File extension:: {str(e)}")    
            file_extension = uploaded_filename.split(".")[-1]   
        file_docName = str(uuid.uuid4())
        save_uploadedfile(file_content,file_docName,file_extension)
        folder_path = os.path.join("static")+"/"
        filename_without_ext = os.path.splitext(os.path.basename(file_docName))[0]
        image_name = f'{filename_without_ext}.{file_extension}'
        img_path = folder_path+ image_name
        upload_to_azure(img_path, image_name)
        tempFilePaths.append(img_path)
        # print("img_path:::", img_path)
        return img_path ,image_name, file_extension
    except Exception as e:
        print("Exeption in save_and_gen_filepath as ::", str(e))
        return None , None , None

def is_colored_image(image_path):
    # Open the image and convert it to RGB if it's not already in that mode
    img = Image.open(image_path).convert('RGB')
    
    # Convert image to numpy array
    img_array = np.array(img)
    
    # Split into R, G, B channels
    R, G, B = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
    
    # Check if R == G == B for all pixels
    if np.array_equal(R, G) and np.array_equal(G, B):
        return "Black_and_white"
    else:
        return "Coloured"
    
def strip_fieldsvalues(resp):
    try:
        for k , v in resp.items():
            if v!=None or v!="None":
                resp[k] = v.strip()
        return resp        
    except Exception as e:
        print("Exception in strip_fieldsvalues as::", str(e))
        return resp



def save_url_file(url):
    try:
        response = requests.get(url)
        urlpath = urlsplit(url).path
        filename = os.path.basename(urlpath)
        if response.status_code == 200:
            content_bytes = response.content
            filename = filename
            return content_bytes , filename
        else:
            return None , None
    except Exception as e:
        print("Exception in save_url_filea as::", str(e))  
        return None , None

def rem_special_char(str_obj , flag):
    try:
        if str_obj!=None:
            if  flag == "alphabet":
                str_obj = re.sub(r'[^a-zA-Z\s]', ' ', str_obj)

            elif flag == 'digit':
                str_obj = re.sub(r'[^0-9\s]', ' ', str_obj)
            else:
                str_obj = re.sub(r'[^a-zA-Z0-9\s]', ' ', str_obj)
            str_obj = re.sub(r'\s+', ' ', str_obj).strip()  
            str_obj = str_obj.strip()  
            return str_obj
        else:
            return str_obj
    except Exception as e:
        print("Exception in rem_special_char as::" ,str(e))
        return str_obj



def make_photo_conclusion(response):
    try:

        test_list = response["tests"].copy()

        for i in range(len(test_list)):
            if test_list[i]["test"] == "Face Height Test":
                response["tests"].remove(response["tests"][i])
        for i in range(len(response["tests"])):
            if response["tests"][i]["test"] == "Face Detection Test":
                response["tests"][i]["conclusion"] = "Face is detected correctly"  if response['tests'][i]['data']['Number of Faces'] == 1  else "Face not detected" 
            elif response["tests"][i]["test"] == "Coloured Image Test":
                response["tests"][i]["conclusion"] = "Image is colored" if response['tests'][i]['status'] == "Pass" else "Image is in black and white"

            elif response["tests"][i]["test"] == "Face Tilt Test":
                response["tests"][i]["conclusion"] = "Detected Face is not tilted" if response["tests"][i]["status"] == "Pass" else "Detected Face is tilted"

            elif response["tests"][i]["test"] == "Face Facing Straight":
                response["tests"][i]["conclusion"] = "Detected Face is facing straight" if response["tests"][i]["status"] == "Pass" else "Detected Face is not facing straight"

            elif response["tests"][i]["test"] == "Occlusion Detection Test":
                if response["tests"][i]["status"] == "Pass":
                    response["tests"][i]["conclusion"] = "No Occlusion detected on Face"
            
                elif response["tests"][i]["status"] == "Fail" and response['tests'][i]['data']['Occlusion Eye'] and not response['tests'][i]['data']['Occlusion mouth']:
                    response["tests"][i]["conclusion"] = "Occlusion detected on Eyes"   

                else:
                    response["tests"][i]["conclusion"] = "Occlusion detected on Face"

            elif response["tests"][i]["test"] == "Face Alignment Test":
                response["tests"][i]["conclusion"] = "Face Alignment is correct" if response["tests"][i]["status"] =="Pass" else "Face Alignment is not correct"

            elif response["tests"][i]["test"] == "Background Check":
                response["tests"][i]["conclusion"] = "Image Background is Plain" if response["tests"][i]["status"] =="Pass" else "Image Background is not plain"

            elif response["tests"][i]["test"] == "Image Quality Check":
                response["tests"][i]["conclusion"] = "Image Quality is Good" if response["tests"][i]["status"] == "Pass" else "Image quality is not good"


        return response    

    except Exception as e:
        print("Exception in new_fun as :", str(e))
        return response
    
def sort_doc_pages(docuemnt_level_schema):
    try:
        sorted_pages = sorted(docuemnt_level_schema["pages"], key=lambda x: x["pg_no"])
        docuemnt_level_schema["pages"] = sorted_pages
        return docuemnt_level_schema
    except Exception as e:
        print("Exception in sort_doc_pages as" , str(e))    


