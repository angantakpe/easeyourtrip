from src.utils.util import *
from mrz.checker.td1 import TD1CodeChecker
from mrz.checker.td2 import TD2CodeChecker
from mrz.checker.td3 import TD3CodeChecker
from datetime import datetime
import os , json 
import re
 

with open(os.path.join('assests', 'country_states.json'), 'r') as f:
    country_state = json.load(f)
f.close()    
COUNTRY_LIST = country_state.keys()

def Passport_front(textdata,text_string , csv_row , PassportFrontBaseClass):
        try:
            DateofBirth = None
            Type = None
            Countrycode = None
            Country = None
            passportno = None
            Surname = None
            Firstname = None
            Nationality = None
            Sex = None
            PlaceofBirth = None
            CountryofBirth =  None
            PlaceofIssue = None
            DateofIssue = None
            DateofExpiry = None
            MRZ = None
            
            output2=[]
            for w in textdata:
                output2.append(w.upper())
            output3=[]
            for x in output2:
                if 'REPUBLIC' not in x and 'TYPE' not in x and 'GIVEN' not in x and 'COUNTRY' not in x and 'PASSPORT' not in x and 'NO.' not in x and 'NAME' not in x and 'NATIONALITY' not in x and 'SEX' not in x and 'DATE' not in x and 'PLACE' not in x:
                    output3.append(x)
            
            dates=[]
            for w in output3:
                #extract dates
                match = re.search('\d{2}\s*/\d{2}\s*/\d{4}', w)
                if match:
                    dates.append(match.group())

                    
            if len(dates)>0:
                dates = getSortedDates(dates, desc=False)

            if len(dates)==2:
                caldate=int(dates[1].split('/')[-1])-int(dates[0].split('/')[-1])
                if caldate==10:
                    DateofBirth=None
                    try:
                        DateofIssue=dates[0]
                    except:
                        DateofIssue=None
                    try:
                        DateofExpiry=dates[1]
                    except:
                        DateofExpiry=None
            else:
                try:
                    DateofBirth=dates[0]
                except:
                    DateofBirth=None
                try:
                    DateofIssue=dates[1]
                except:
                    DateofIssue=None

                try:
                    DateofExpiry=dates[2]
                except:
                    DateofExpiry=None

            try:
                #removes one date
                for x in output3:
                    if (DateofBirth is not None) and (DateofBirth == x):
                        output3.remove(x)
                    elif (DateofIssue is not None) and (DateofIssue == x):
                        output3.remove(x)
                    elif (DateofExpiry is not None) and (DateofExpiry == x):
                        output3.remove(x)

                #removes second date
                for x in output3:
                    if (DateofBirth is not None) and (DateofBirth == x):
                        output3.remove(x)
                    elif (DateofIssue is not None) and (DateofIssue == x):
                        output3.remove(x)
                    elif (DateofExpiry is not None) and (DateofExpiry == x):
                        output3.remove(x)

                #removes third date
                for x in output3:
                    if (DateofBirth is not None) and (DateofBirth == x):
                        output3.remove(x)
                    elif (DateofIssue is not None) and (DateofIssue == x):
                        output3.remove(x)
                    elif (DateofExpiry is not None) and (DateofExpiry == x):
                        output3.remove(x)

            except Exception as e:
                print("Exception in removing date from passport front: ",e)
            #getting single letters from ocr result
            single=[]
            for w in output3:
                if re.match(r'^[A-Z]{1}$',w):
                    single+=w

            #1st single letter will be type because oc gives output in serial order
            try:
                Type=single[0]
            except:
                Type=None

            #then the single letter should be geneder
            try:
                Sex=''.join([i for i in single if re.match(r'[M,F]$',i)])
            except:
                Sex=None

            #removing singles from ocr result
            for w in single:
                output3.remove(w)

            #removes patterns like [Upper case letters(zero or any) (zero or any white spaces) / (zero or any white spaces) upper case letters(zero or any)]
            wordsToRemove = []
            for w in output3:
                if re.match('[A-Z]*\s*/\s*[A-Z]*',w):
                    wordsToRemove.append(w)
                if not bool(re.match('[a-zA-Z\s]+$', w)):
                    if len(w)<=3:
                        wordsToRemove.append(w)
                        
            for w in wordsToRemove:
                if w in output3:
                    output3.remove(w)
            
            #finding passport number
            passportno=None
            startIdx = 0
            for i,w in enumerate(output3):
                if re.search(r'^[A-Z]*\s*[0-9]{7}$', w):
                    passportno=w
                    startIdx = i
                    break
                else:
                    passportno=None
            #removing passport number

            try:
                wordsToRemove = []
                for i in range(startIdx+1):
                    wordsToRemove.append(output3[i])
                for w in wordsToRemove:
                    if w in output3:
                        output3.remove(w)
            except Exception as e:
                print("Exception while removing words: ",e)

            #finding IND and INDIAN and remoing text part containing BIRTH
            for x in output3:
                    if 'BIRTH' in x:
                        output3.remove(x)
                    if ('IND' in x) or ('INDIAN' in x):
                        Nationality='INDIAN'
                        Countrycode='IND'
                        Country="INDIA"
                        break
                    else:
                        dict = findCountryCode_alpha3(x)
                        if dict==None:
                            Nationality=None
                            Countrycode=None
                        else:
                            Countrycode=dict["countryCode"]
                            Nationality=dict["Nationality"].upper()
                            Country=dict["country"].upper()
                            break
            
            #finding MRZ
            MRZ=''
            for w in output3:
                if '<' in w:
                    MRZ+=w

            try:
                indices=[i for i,s in enumerate(output3) if re.match(r'IND$',s)]
                if indices:
                    z=max(indices)
                    output4=output3[z+1:]
                else:
                    output4=output3
            except:
                indices=[i for i,s in enumerate(output3) if re.match(r'IND',s)]
                if indices:
                    z=max(indices)
                    output4=output3[z+1:]
                else:
                    output4=output3
            words_to_remove = []
            for i in output4:
                if 'INDIAN' in i:
                    words_to_remove.append(i)
                elif 'OF BIRTH' in i or 'OF EXPIRY' in i or 'OF ISSUE' in i:
                    words_to_remove.append(i)
                elif len(i)<=2:
                    words_to_remove.append(i)
                elif re.search(r'\d',i):
                    words_to_remove.append(i)
                elif '/' in i:
                    words_to_remove.append(i)
            
            for w in words_to_remove:
                if w in output4:
                    output4.remove(w)

            output5 = output4
            try:
                Sname=output4[0]
                Name=output4[1]
                Pob=output4[2]
                if(len(output4)>5):
                    Poi=output4[4]
                else:
                    Poi=output4[3] #Signature is getting here
                if '<' in Poi:
                    Poi = ""
            except:
                #making varibles as None
                if len(output4)==1:
                    Name=None
                    Pob=None
                    Poi=None
                elif len(output4)==2:
                    Pob=None
                    Poi=None
                elif len(output4)==3:
                    Poi=None
                elif len(output4)==4:
                    Poi=None
                else:
                    Sname = None
                    Name = None
                    Pob = None
                    Poi = None

            strings={ "Surname": Sname,
                    "FirstName": Name,
                    "PlaceofBirth": Pob,
                    "PlaceofIssue": Poi}

            #this part removes digits from the names fetched
            values=list(strings.values())
            strings2=[]
            try:
                for w in values:
                    string1=[]
                    for w1 in w.split(' '):
                        if re.match(r'^[0-9]*',w1):
                            string1.append(re.sub(r'[^A-Z]','',w1))
                    strings2.append(string1)
            except:
                strings2=[]
            
            strings3=[]
            for w in strings2:
                if len(w)>=2:
                    strings3.append(" ".join(map(str,w)))
                else:
                    strings3.append(w)

            try:
                str1 = ''.join(str(e) for e in strings3[0])
                Surname=str1
                str2 = ''.join(str(e) for e in strings3[1])
                Firstname=str2
                str3 = ''.join(str(e) for e in strings3[2])
                PlaceofBirth=str3
                str4 = ''.join(str(e) for e in strings3[3])
                PlaceofIssue=str4
                
            except:
                Surname=None
                Firstname=None
                PlaceofBirth=None
                PlaceofIssue=None

            #MRZ Logic
            #fetching data from MRZ and filling it in the fields that are None from above regex
            newMRZ = ""
            for i in MRZ:
                if len(newMRZ) == 44:
                    newMRZ+="\n"
                if i !=' ':
                    newMRZ+=i                

            try:   
                td1_check = TD1CodeChecker(newMRZ)
                if td1_check:
                    fields = td1_check.fields()
                    Type = fields.document_type                    
                    Countrycode = fields.country                    
                    passportno = fields.document_number
                    Surname = fields.surname                   
                    Firstname = fields.name
                    Sex = fields.sex
                    date_string = fields.birth_date
                    date_obj = datetime.strptime(date_string, '%y%m%d')
                    DateofBirth = date_obj.strftime('%d/%m/%Y')
                    date_string = fields.expiry_date
                    date_obj = datetime.strptime(date_string, '%y%m%d')
                    DateofExpiry = date_obj.strftime('%d/%m/%Y')
            except Exception as e:
                print("Exception in td1 check on mrz: ",e)
                try:
                    td2_check = TD2CodeChecker(newMRZ)
                    if td2_check:
                        fields = td2_check.fields()
                        Type = fields.document_type                    
                        Countrycode = fields.country                    
                        passportno = fields.document_number
                        Surname = fields.surname                   
                        Firstname = fields.name
                        Sex = fields.sex
                        date_string = fields.birth_date
                        date_obj = datetime.strptime(date_string, '%y%m%d')
                        DateofBirth = date_obj.strftime('%d/%m/%Y')
                        date_string = fields.expiry_date
                        date_obj = datetime.strptime(date_string, '%y%m%d')
                        DateofExpiry = date_obj.strftime('%d/%m/%Y')
                except Exception as e:
                    print("Exception in td2 check on mrz: ",e)
                    try:
                        td3_check = TD3CodeChecker(newMRZ)
                        if td3_check:
                            fields = td3_check.fields()
                            Type = fields.document_type                    
                            Countrycode = fields.country
                            dict = findCountryCode_alpha3(Countrycode)
                            if dict==None:
                                Nationality=None
                                Country=None
                            else:
                                Countrycode=dict["countryCode"]
                                Nationality=dict["Nationality"].upper()
                                Country=dict["country"].upper()                    
                            passportno = fields.document_number
                            Surname = fields.surname                   
                            Firstname = fields.name
                            Sex = fields.sex
                            sortedDates = getSortedDates(dates)
                            date_string = fields.birth_date
                            date_obj = datetime.strptime(date_string, '%y%m%d').date()
                            DateofBirth = date_obj.strftime('%d/%m/%Y')
                            current_year = datetime.now().year
                            if len(sortedDates)>0:
                                yy = sortedDates[-1][-4]+sortedDates[-1][-3]
                                year = yy[0]+yy[1]+DateofBirth[-2]+DateofBirth[-1]
                                if (int(year) > int(current_year)) :
                                    a = list(DateofBirth)
                                    a[-4] = '1'
                                    a[-3] = '9'
                                    DateofBirth = ''.join(a)
                                else:
                                    a = list(DateofBirth)
                                    a[-4] = yy[0]
                                    a[-3] = yy[1]
                                    DateofBirth = ''.join(a)
                            else:
                                if (int(''.join(DateofBirth[6:10]))>int(current_year)):
                                    a = list(DateofBirth)
                                    a[-4] = '1'
                                    a[-3] = '9'
                                    DateofBirth = ''.join(a)

                            date_string = fields.expiry_date
                            date_obj = datetime.strptime(date_string, '%y%m%d')
                            DateofExpiry = date_obj.strftime('%d/%m/%Y')
                    except Exception as e:
                        print("Exception in td3 check on mrz: ",e)

            # if Countrycode!="IND":
            #     return (getPassFrontOpenaiResponse(text_string.upper(), Countrycode , csv_row))
            # else:
            #     append_csv(csv_row , "no_openai_called")
            try:
                x = Surname.split()
                y = Firstname.split()
                for i in x:
                    if i in PlaceofIssue:
                        if len(output4)>5:
                            PlaceofIssue = output4[3]
                        else:    
                            PlaceofIssue = output4[4]

                for j in y:
                    if j in PlaceofIssue:
                        if len(output4)>5:
                            PlaceofIssue = output4[3]
                        else:    
                            PlaceofIssue = output4[4]
            except Exception as e:
                print("Exception while checking for signature in mrz: ",e)
            
            if Surname in [None,""," "]:
                if len(output5)>=3:
                    PlaceofBirth = output5[1]
                    PlaceofIssue = output5[2]
                elif len(output5)>=2:
                    PlaceofBirth = output5[0]
                    PlaceofIssue = output5[1]

            if Countrycode!="IND":    
                PlaceofBirth = ""
                PlaceofIssue = ""
                for i in dates:
                    if (i == DateofBirth) or (i == DateofExpiry):
                        continue
                    else:
                        DateofIssue = i
                if  DateofExpiry!= None:
                    all_dates = [] 
                    for word in textdata:
                        dates = find_dates(word) 
                        if len(dates)>0:
                            all_dates.extend(dates)
                    all_dates = (list(set(all_dates))) 
                    all_dates = getSortedDates(all_dates)   
                    if len(all_dates)>=3:
                        DateofIssue = all_dates[1]
                            
                    # doi_obj  = datetime.strptime(str(DateofExpiry) , '%d/%m/%Y') 
                    # DateofIssue = doi_obj.replace(year=date_obj.year - 10)
                    # DateofIssue = DateofIssue.strftime('%d/%m/%Y')

                start_poi = None
                end_poi = None
                for i in range(len(textdata)):

                    place_search  = re.search(r'\bPLACE\s*OF\s*BIRTH\b', textdata[i] , re.IGNORECASE)
                    if place_search  :
                        start_poi = i
                    if 'BIRTH' in textdata[i] and start_poi is None:
                        start_poi = i
                    if 'MOTHER' in textdata[i] or 'FATHER' in textdata[i] or 'HUSBAND' in textdata[i] or 'ISSUE' in textdata[i] or 'EXPIRY' in textdata[i]  and end_poi is None:
                        end_poi = i

                    if start_poi is not None and end_poi is not None:
                        break

                if start_poi!= None and end_poi!=None:    
                    pob_blob = textdata[start_poi : end_poi]
                    remove_words= ['MOTHER' ,'FATHER', 'BIRTH' , 'SEX' , 'CITIZENSHIP' , 'NUMBER', 'NAME', 'NATIONAL', 'FECHA' , 'OBSERVA', 'HOLDER' ]    
                    pob_blob = [item for item in pob_blob if not any(word in item for word in remove_words)]       
                    if Surname!= None:
                        Surname = re.sub(r'[^A-Za-z\s+]' ,'',  Surname)
                        pob_blob = [item for item in pob_blob if not any(sub_name in item for sub_name in Surname.split())]
                    place_of_birth = ' '.join(w for w in pob_blob)   
                    place_of_birth = re.sub(r'[^A-Za-z\s+]' , ' ' , place_of_birth) 
                    place_of_birth = re.sub(r'\b[F|M]\b', '', place_of_birth).strip()   
                    place_of_birth = re.sub(r'\s+', ' ', place_of_birth).strip()  
                    PlaceofBirth = place_of_birth

            if PlaceofBirth !=None: 
                for count in COUNTRY_LIST:
                    if count.lower() in PlaceofBirth.lower():
                        CountryofBirth =  count.upper()

            Type = rem_special_char(Type , "alphabet")
            Countrycode = rem_special_char(Countrycode, "alphabet")
            Country = rem_special_char(Country, "alphabet")
            Surname = rem_special_char(Surname, "alphabet")
            Firstname = rem_special_char(Firstname, "alphabet")
            Nationality = rem_special_char(Nationality, "alphabet")
            Sex = rem_special_char(Sex, "alphabet")
            PlaceofBirth = rem_special_char(PlaceofBirth, "alphabet")
            CountryofBirth = rem_special_char(CountryofBirth, "alphabet")
            PlaceofIssue = rem_special_char(PlaceofIssue, "alphabet")
            passportno = rem_special_char(passportno, None)
            if passportno!=None:
                passportno = passportno.replace(" ","")

            data={"type_passport":(Type.upper() if Type!=None else None),"country_code": (Countrycode.upper() if Countrycode!=None else None),"country":(Country.upper() if Country!=None else None),"passport_number": (passportno.upper() if passportno!=None else None),"last_name": (Surname.upper() if Surname!=None else None),"first_name": (Firstname.upper() if Firstname!=None else None),"citizenship": (Nationality.upper() if Nationality!=None else None),"sex": (Sex.upper() if Sex!=None else None),"dob": (DateofBirth.replace("-","/") if DateofBirth!=None else None),"place_of_birth": (PlaceofBirth.upper() if PlaceofBirth!=None else None),"country_of_birth" : (CountryofBirth.upper() if CountryofBirth!=None else None) , "place_of_issue": (PlaceofIssue.upper() if PlaceofIssue!=None else None),"passport_issue_date": (DateofIssue.replace("-","/") if DateofIssue!=None else None),"passport_expiry_date": (DateofExpiry.replace("-","/") if DateofExpiry!=None else None),"mrz": (MRZ.upper() if MRZ!=None else None)}

            data = PassportFrontBaseClass(**data)
            data =data.dict()
            return data 
        except Exception as e:
            print("Exception in Passport front as ::", str(e)) 
            data =  {"type_passport":None,"country_code": None,"country":None,"passport_number":None,"last_name": None,"first_name": None,"citizenship": None,"sex":None,"dob": None,"place_of_birth": None,"country_of_birth" : None,   "place_of_issue":None,"passport_issue_date": None,"passport_expiry_date":None,"mrz": None}
            data = PassportFrontBaseClass(**data)
            data =data.dict()
            return data 




def get_passport_textblob(text_blob , textstring):
    try:
        print("started get_passport_textblob")
        start_idx = 0
        end_idx = len(text_blob)

        if "REPUBLIC" and "<" in textstring.upper():
            for i in range(len(text_blob)):
                if "REPUBLIC" in text_blob[i]:
                    start_idx = i
                elif "<" in text_blob[i]:    
                    end_idx = i
            blob_endidx = min(int(end_idx) + 3 , len(text_blob))
            new_textblob = text_blob[start_idx:blob_endidx]
            return new_textblob
        elif "REPUBLIC" not in textstring.upper() and "<" in textstring.upper():
            for i in range(len(text_blob)):
                if "<" in text_blob[i]:    
                    end_idx = i
            blob_endidx = min(int(end_idx) + 3 , len(text_blob))
            new_textblob = text_blob[start_idx:blob_endidx]
            return new_textblob

        elif "REPUBLIC"  in textstring.upper() and "<" not in textstring.upper():
            for i in range(len(text_blob)):
                if "REPUBLIC" in text_blob[i]:    
                    start_idx = i
            new_textblob = text_blob[start_idx:end_idx]
            return new_textblob
        else:
            return text_blob

    except Exception as e:    
        print("Exception in get_passport_textblob as::" , str(e))
        return text_blob

