from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import  datetime

class Address(BaseModel):
    address_string: Optional[str]
    country: Optional[str]
    state:Optional[str]
    district: Optional[str]
    city: Optional[str]
    street_name: Optional[str]
    apartment: Optional[str]
    street_number: Optional[str]
    postal_code: Optional[int]
    @field_validator('address_string' ,"country" ,"state" , "district" , "city","street_name" , "apartment" , "street_number" , mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator('postal_code', mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, int) else None 
            return validation
        return v




class NationalIdSchema(BaseModel):
    name: Optional[str]
    dob: Optional[str]
    date_of_expiry: Optional[str]
    national_id_number: Optional[str]
    country_of_issue: Optional[str]
    @field_validator('name' ,"national_id_number" , "country_of_issue"  , mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator('dob' , 'date_of_expiry' ,  mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 



class PassportBackSchema(BaseModel):
    father_legal_guardian: Optional[str]
    name_of_mother: Optional[str]
    spouse_last_name: Optional[str]
    spouse_first_name:Optional[str]
    marital_status:Optional[str]
    old_passport_no: Optional[str]
    old_date_of_issue: Optional[str]
    old_place_of_issue: Optional[str]
    file_no: Optional[str]
    passport_number:Optional[str]
    address: Optional[Address]
    @field_validator('father_legal_guardian' ,"name_of_mother" ,"spouse_last_name" , "spouse_first_name",'marital_status' ,"old_passport_no" ,"old_date_of_issue" , "old_place_of_issue"  , "file_no"  , "passport_number"   , mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator('old_date_of_issue',  mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 
class PassportFrontSchema(BaseModel):
    type_passport: Optional[str]
    country_code: Optional[str]
    country: Optional[str]
    passport_number:Optional[str]
    last_name:Optional[str]
    first_name: Optional[str]
    citizenship: Optional[str]
    sex: Optional[str]
    dob: Optional[str]
    place_of_birth:Optional[str]
    country_of_birth: Optional[str]
    place_of_issue: Optional[str]
    passport_issue_date: Optional[str]
    passport_expiry_date: Optional[str]
    mrz: Optional[str]
    @field_validator('type_passport' ,"country_code" ,"country" , "passport_number",'last_name' ,"first_name" ,"citizenship" , "sex"  , "place_of_birth"  , "country_of_birth", "place_of_issue" , "mrz", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator('passport_issue_date' , "passport_expiry_date" , "dob",  mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 



class TravelDetails(BaseModel):
    departure_date: Optional[str]
    origin_airport_code: Optional[str]
    origin_country_name:Optional[str]
    arrival_date: Optional[str]
    destination_airport_code: Optional[str]
    destination_country_name: Optional[str]
    @field_validator('origin_airport_code' ,"destination_airport_code", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator('departure_date','arrival_date' ,  mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 
    
from typing import Dict
class FlightTicketSchema(BaseModel):
    passenger: Optional[Dict[str, str]]
    journey_details:  Optional[list[TravelDetails]]   
    @field_validator('passenger', mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            # Ensure that the dictionary contains valid string keys and values
            validated_dict = {key: value if isinstance(value, str) else None for key, value in v.items()}
            return validated_dict
        return v



class SalarySlipSchema(BaseModel):
    name: Optional[str]
    amount: Optional[str]
    currency: Optional[str]
    date: Optional[str]
    @field_validator('name' ,"amount","currency", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator('date',  mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 

class AccountStatementSchema(BaseModel):
    name: Optional[str]
    date: Optional[str]
    balance: Optional[str]
    currency: Optional[str]
    bank_name: Optional[str]
    @field_validator('name',"balance","bank_name","currency", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator('date',  mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 

class BalanceCertificateSchema(BaseModel):
    name: Optional[str]
    date: Optional[str]
    balance: Optional[str]
    currency: Optional[str]
    bank_name: Optional[str]
    @field_validator('name',"balance","bank_name", "currency", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator('date',  mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 
    
class FixedDepositSummarySchema(BaseModel):
    name: Optional[str]
    deposit_date: Optional[str]
    maturity_date: Optional[str]
    deposit_amount: Optional[str]
    currency: Optional[str]
    bank_name: Optional[str]
    @field_validator('name',"deposit_amount","bank_name" , "currency", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator('maturity_date', 'deposit_date',  mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 
    
class BookingDetails(BaseModel):
    checkin_date: Optional[str]
    checkout_date: Optional[str]
    address: Optional[str]
    @field_validator("address", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator('checkin_date','checkout_date' ,  mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 
                
class HotelTicketSchema(BaseModel):
    guest: Optional[Dict[str, str]]
    booking_details:  Optional[list[BookingDetails]]
    @field_validator('guest', mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            # Ensure that the dictionary contains valid string keys and values
            validated_dict = {key: value if isinstance(value, str) else None for key, value in v.items()}
            return validated_dict
        return v
    

class PersonDetails(BaseModel):
    name: Optional[str]
    passport_number: Optional[str]
    @field_validator("name","passport_number", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
                
class LettersSchema(BaseModel):
    list_of_people: Optional[list[PersonDetails]]


class TravelInsuranceSchema(BaseModel):
    name: Optional[str] 
    policy_number:  Optional[str]
    passport_number:  Optional[str]
    dob:  Optional[str]
    @field_validator('name', 'policy_number', 'passport_number', mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            return v if isinstance(v, str) and len(v.strip()) > 0 else None
        return v
    @field_validator('dob',  mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v
    

class StayDetails(BaseModel):
    country: Optional[str]
    num_of_days: Optional[str]
    arrival_date: Optional[str]
    departure_date: Optional[str]
    @field_validator("num_of_days", "country", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator('arrival_date','departure_date' ,  mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v
                

class ItinerarySchema(BaseModel):
    visitor: Optional[Dict[str, str]]
    country_stay_list: Optional[list[StayDetails]]
    @field_validator('visitor', mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            # Ensure that the dictionary contains valid string keys and values
            validated_dict = {key: value if isinstance(value, str) else None for key, value in v.items()}
            return validated_dict
        return v
    



class StatementOfPurpose(BaseModel):
    name: Optional[str]
    @field_validator('name' , mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v


class EmploymentLetter(BaseModel):
    name: Optional[str]
    employer_name: Optional[str]
    address: Optional[Address]
    @field_validator('name' , "employer_name", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v


class MarriageCertificate(BaseModel):
    male_spouse: Optional[str]
    female_spouse: Optional[str]
    date: Optional[Address]
    @field_validator('male_spouse' , "female_spouse", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator("date",mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 

class UsPrCard(BaseModel):
    name: Optional[str]
    date_of_issuance: Optional[str]
    date_of_expiry: Optional[str]
    date_of_birth: Optional[str]
    @field_validator('name' , mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator("date_of_issuance" , "date_of_expiry" , "date_of_birth",mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 

class UtilityBills(BaseModel):
    name: Optional[str]
    address: Optional[Address]
    @field_validator('name' , mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v

class PropertyOwnership(BaseModel):
    name: Optional[str]
    @field_validator('name' , mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v


class BuissnessRegistration(BaseModel):
    name: Optional[str]
    registration_no: Optional[str]
    date_of_registration: Optional[str]
    date_of_birth: Optional[str]
    @field_validator('name' , "registration_no", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator("date_of_registration"  , "date_of_birth",mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 


class BirthCertificate(BaseModel):
    name: Optional[str]
    date_of_birth: Optional[str]
    father_name: Optional[str]
    mother_name: Optional[str]
    country_of_birth: Optional[str]
    @field_validator('name' , "father_name" , "mother_name" , "country_of_birth", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator("date_of_birth" ,mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 
class BusinessBalanceSheet(BaseModel):
    name: Optional[str]
    closing_date: Optional[str]
    closing_amount: Optional[str]
    currency: Optional[str]
    address: Optional[Address]
    @field_validator('name' , "closing_amount" , "currency", mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator("closing_date" ,mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 

class IncomeTaxReturn(BaseModel):
    name: Optional[str]
    itr_amount: Optional[str]
    currency: Optional[str]
    date_of_filing: Optional[str]
    @field_validator('name' , "itr_amount", "currency" , mode='before')
    def replace_invalid_values(cls, v):
        if v is not None:
            validation = v if isinstance(v, str) else None 
            return validation
        return v
    @field_validator("date_of_filing" ,mode='before')
    def validate_date_format(cls, v):
        if v:
            try:# Try to parse the date in DD/MM/YYYY format
                datetime.strptime(v, "%d/%m/%Y")  # This checks the format
                return v  # If valid, return the date string
            except ValueError:
                print(f"Invalid date format: {v}")
                return None
        return v 