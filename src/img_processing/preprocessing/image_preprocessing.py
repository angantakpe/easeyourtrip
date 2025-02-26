import cv2 , os , json , uuid , time
import numpy as np
from PIL import Image
from src.utils.util import getDPI
from src.utils.coordinates import adjust_coordinates_after_crop
from src.utils.logs import  append_csv
from datetime import datetime
from src.azure_services.cloud import upload_to_azure , get_img_url_with_blob_sas_token
from src.logging.logger import debug_log
try:#The standard json schema at the document level is predefined in assests/documents.json. Loading the schema for updating it.
    with open(os.path.join('assests', 'ocr_categories.json'), 'r') as f:
        docs = json.load(f)
        no_cropping = docs["no_cropping"]
    f.close()    
except Exception as e:        
    print("Exception in doc_schema loading as :", str(e))


#cropping the document by finding the counters of the document and cropping it. returning a numpy array of the cropped image
def crop_image(folder_path, image):# do not add "/" at the end in path
    try:
        #if not png to save in jpeg temperory and delete adter use
        # Load the image
        img = cv2.imread(f"{folder_path}/{image}")
        # img = cv2.imread(f"Test_Data/Docs/{image}")
        original_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Convert the image to grayscale
        gray_image = cv2.cvtColor(original_img, cv2.COLOR_RGB2GRAY)

        # Blurring
        blur = cv2.GaussianBlur(gray_image, (31, 31), 0)  # Gaussian Local Blur

        # Threshold
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11,
                                       2)  # Adaptive Threshold - Gaussian Weighted Sum

        # apply morphology
        kernel = np.ones((50,50), np.uint8)
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        kernel = np.ones((8,8), np.uint8)
        eroded = cv2.morphologyEx(closed, cv2.MORPH_ERODE, kernel)

        # get largest contour
        contours = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contours = contours[0] if len(contours) == 2 else contours[1]

        # Combined all contours
        collective_contour = np.concatenate(contours)

        # get bounding box
        x, y, w, h = cv2.boundingRect(collective_contour)

        # draw filled contour on black background
        mask = np.zeros_like(gray_image)
        mask = cv2.merge([mask, mask, mask])
        cv2.drawContours(mask, contours, -1, (255, 255, 255), cv2.FILLED)

        # apply mask to input
        result1 = original_img.copy()
        result1 = cv2.bitwise_and(result1, mask)

        # crop result
        maxh = len(original_img)
        maxw = len(original_img[0])
        result2 = original_img[(y - 4 if y >= 4 else y):(y + h + 4 if y + h + 4 <= maxh else y + h), (x - 4 if x >= 4 else x):(x + w + 4 if x + w + 4 <= maxw else x + w)]
        return result2
    except Exception as e:
        print("Exception occured in crop_image: ",e)
        raise e
# preprocessing the image to crop the main object(document) from the document
def preprocess_image(folder_path, image, destination_folder_path=None): # do not add "/" at the end in path
    try:
        # converting img format to png
        destination_folder_path = folder_path if destination_folder_path==None else destination_folder_path
        if image is not None:
            img_path = os.path.join(folder_path,image)
            new_image_name = image
            # cropping image
            cropped_image = crop_image(destination_folder_path, new_image_name)
            # numpy array to PIL format
            im = Image.fromarray(cropped_image)
            new_image_name = str(uuid.uuid4())+".jpeg"
            img_path = os.path.join(destination_folder_path, new_image_name)
            im.save(img_path)
        return img_path
    except Exception as e:
        print("Exception occured in preprocess_image: ",e)
        raise e
    
def rotate_image(image_path, angle , request_id):
    try:
        # Open the image file
        with Image.open(image_path) as img:
            # Rotate the image by the specified angle
            rotated_img = img.rotate(angle, expand=True)
            
            # Save the rotated image
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_rotated{ext}"
            
            # Save the rotated image
            rotated_img.save(output_path)
            # print(f"Image saved to {output_path}")
        img.close()    
        return   output_path  
    except Exception as e:
        debug_log(f"Exception in rotate_image as {str(e)} ", "rotate_image", request_id)
        return  image_path


def rotate_point(x, y, angle, image_center):
    """Rotate a point around the center by a given angle."""
    # Convert the angle to radians
    # print("started rotate angle")
    angle_rad = np.deg2rad(-angle)
    # print(" rotate angle", angle_rad)

    # Translate point to origin (center of rotation)
    x_shifted = x - image_center[0]
    y_shifted = y - image_center[1]

    # Apply rotation matrix
    x_rotated = x_shifted * np.cos(angle_rad) - y_shifted * np.sin(angle_rad)
    y_rotated = x_shifted * np.sin(angle_rad) + y_shifted * np.cos(angle_rad)

    # Translate back to the original center
    x_new = x_rotated + image_center[0]
    y_new = y_rotated + image_center[1]

    return x_new, y_new

def rotate_bounding_box(bbox, angle, original_image_size, rotated_image_size):
    """Rotate the bounding box by the given angle around the center of the image."""
    # print("bbox::",bbox )
    xmin, ymin, xmax, ymax = bbox
    if xmin!=None and ymin!=None and xmax!=None and ymax!=None :
        # print("coordiantes::",xmin, ymin, xmax, ymax )

    # Calculate the center of the original and rotated image
        rotated_image_center = (rotated_image_size[0] / 2, rotated_image_size[1] / 2)
        original_image_center = (original_image_size[0] / 2, original_image_size[1] / 2)

        # Rotate each corner of the bounding box based on the original image center
        top_left = rotate_point(xmin, ymin, angle, original_image_center)
        top_right = rotate_point(xmax, ymin, angle, original_image_center)
        bottom_left = rotate_point(xmin, ymax, angle, original_image_center)
        bottom_right = rotate_point(xmax, ymax, angle, original_image_center)

        # Adjust for the shift in center due to the rotated image's new size
        center_shift_x = rotated_image_center[0] - original_image_center[0]
        center_shift_y = rotated_image_center[1] - original_image_center[1]

        # Apply the shift to each rotated corner
        top_left = (top_left[0] + center_shift_x, top_left[1] + center_shift_y)
        top_right = (top_right[0] + center_shift_x, top_right[1] + center_shift_y)
        bottom_left = (bottom_left[0] + center_shift_x, bottom_left[1] + center_shift_y)
        bottom_right = (bottom_right[0] + center_shift_x, bottom_right[1] + center_shift_y)

        # Find the new bounding box by taking the min/max of the rotated coordinates
        xs = [top_left[0], top_right[0], bottom_left[0], bottom_right[0]]
        ys = [top_left[1], top_right[1], bottom_left[1], bottom_right[1]]

        new_xmin = min(xs)
        new_ymin = min(ys)
        new_xmax = max(xs)
        new_ymax = max(ys)

        return [new_xmin, new_ymin, new_xmax, new_ymax]
    else:
        return bbox
    


def rotate_coordinates(word_locations, angle, original_image_shape, rotated_image_shape , request_id):
    """Rotate word locations given an angle and the original image shape."""
    try:
        width, height = original_image_shape
        center = (width / 2, height / 2)  # Calculate the center of the original image
        # print("center::",center )

        rotated_locations = {}
        rotated_image_center = (rotated_image_shape[0] / 2, rotated_image_shape[1] / 2)  # New center after rotation
        # print("rotated_image_center::",rotated_image_center )
        for word, coords_list in word_locations.items():
            # if word == "REPUBLIC":
            #     print("coordinate coords_list" ,coords_list)

            rotated_coords = []
            for coords in coords_list:
                rotated_set = []
                for i in range(0, len(coords), 2):  # Iterate over pairs (x, y)
                    x = coords[i]
                    y = coords[i + 1]
                    rotated_coord = rotate_point(x, y, angle, center)
                    # Adjust for the center shift due to the rotated image's new size
                    center_shift_x = rotated_image_center[0] - center[0]
                    center_shift_y = rotated_image_center[1] - center[1]
                    
                    # Apply the shift to the rotated coordinates
                    adjusted_x = rotated_coord[0] + center_shift_x
                    adjusted_y = rotated_coord[1] + center_shift_y
                    # print("center_shift_x:::" , center_shift_x)
                    rotated_set.extend((int(adjusted_x), int(adjusted_y)))  # Extend to keep the format [x1, y1, x2, y2, ...]
     
                rotated_coords.append(rotated_set)  # Append the list of rotated coordinates
            rotated_locations[word] = rotated_coords

        return True , rotated_locations
    except Exception as e:
        debug_log(f"Exception in rotate_coordinates as {str(e)} ", "rotate_coordinates", request_id)
        return False , word_locations
    


def crop_passport(cropped_image_path ,  locs):
    try:
        org_img = cv2.imread(cropped_image_path)
        img_height, img_width = org_img.shape[:2]
        upper_coordinate = None
        # first_left_symbol = None
        # last_left_symbol = None
        xmax_r = 0
        xmin_l = img_width
        ymax_b = 0
        for word, val in locs.items():
            if "REPUBLIC" in word :
                upper_coordinate = val
                ymin_r = upper_coordinate[-1][1]  # ymin for top cropping from "REPUBLIC

            if "<" in word:
                for v in val:
                    xmin_l = min( v[0] , v[2] , v[4] , v[6] , xmin_l )
                    xmax_r = max( v[0] , v[2] , v[4] , v[6] , xmax_r )
                    ymax_b = max( v[1] , v[3] , v[5] , v[7] , ymax_b )
        # Ensure required coordinates are found
        if upper_coordinate :
            # Define boundaries
            pixcel_to_extend_horizontally , pixcel_to_extend_vertically  = get_crop_margin_from_text(xmin_l ,ymin_r ,xmax_r ,ymax_b , img_height ,img_width)
            y_start = int(max(ymin_r - int(pixcel_to_extend_vertically) , 0) ) # Top boundary from "REPUBLIC"
            xmin_l = int(max(xmin_l- int(pixcel_to_extend_horizontally), 0))  # Left boundary from first "<"        
            xmax_r = int(min(xmax_r + int(pixcel_to_extend_horizontally) , img_width))           # Right boundary from last "<"
            ymax_b = int(min(ymax_b + int(pixcel_to_extend_vertically), img_height))           # Bottom boundary from last "<"

            base, ext = os.path.splitext(cropped_image_path)
            output_path = f"{base}_cropped{ext}"
            # Save the rotated image
            cropped = org_img[y_start:ymax_b, xmin_l:xmax_r]
            cv2.imwrite(output_path, cropped)

            return (True ,  output_path   , xmin_l , y_start )
        else:
            return (False ,  cropped_image_path , None , None )          
    except Exception as e: 
        print("Exception in crop_passport  as ::", str(e))
        return  (False ,  cropped_image_path , None , None )            
    

def crop_img_text_locations( original_img_pil , original_img_path , word_coordinates , document_type , text_string , request_id):

    """
    original_img_pil : PIL object of the original image
    word_coordinates : Dict of Words
    returns : cropped PIL and adjusted coordinates
        
    """
    try:
        if document_type not in  no_cropping:
            if document_type == "passport_front" and ("REPUBLIC" and "<" in text_string.upper()):

                # pass_text_blob = get_passport_textblob(ocr_resp['text_blob'] , text_string)
                crop_paasport_status , crop_passport_path , x_top , y_top = crop_passport(original_img_path , word_coordinates )
                if crop_paasport_status:
                    crop_pass_coord =  adjust_coordinates_after_crop(word_coordinates , x_top , y_top)
                else:
                    crop_pass_coord = word_coordinates
                return   Image.open(crop_passport_path) ,   crop_pass_coord , list(crop_pass_coord.keys())


            img_width , img_height = original_img_pil.size

            min_x = img_width
            min_y = img_height
            max_x = 0
            max_y = 0
            
            for w, locations in (word_coordinates).items():
                for location in locations:
                    min_x = min( min_x , location[0])
                    min_y = min( min_y , location[1])
                    max_x = max( max_x , location[-2])
                    max_y = max( max_y , location[-1])

            pixcel_to_extend_horizontally , pixcel_to_extend_vertically = get_crop_margin_from_text(min_x ,min_y ,max_x ,max_y , img_height ,img_width)
            min_y = int(max(min_y - int(pixcel_to_extend_vertically) , 0) ) # Top boundary from "REPUBLIC"
            min_x = int(max(min_x- int(pixcel_to_extend_horizontally), 0))  # Left boundary from first "<"        
            max_x = int(min(max_x + int(pixcel_to_extend_horizontally) , img_width))           # Right boundary from last "<"
            max_y = int(min(max_y + int(pixcel_to_extend_vertically), img_height))  
            
            cropped_img_pil = original_img_pil.crop((min_x , min_y, max_x, max_y))
            cropped_img_coord =  adjust_coordinates_after_crop(word_coordinates , min_x , min_y)
            return cropped_img_pil , cropped_img_coord , list(cropped_img_coord.keys())
        
        else:
            return original_img_pil , word_coordinates ,list(word_coordinates.keys())

    except Exception as e:
        debug_log(f"Exception in crop_img_text_locations as {str(e)} ", "crop_img_text_locations", request_id)
        return original_img_pil , word_coordinates ,list(word_coordinates.keys())



def get_crop_margin_from_dpi(cropped_image_path):
    try:
        dpi = getDPI(cropped_image_path)
        if dpi<100:
            return 100
        pixels = (1 / 2.54) * dpi 
        return pixels
    except Exception as e:
        print("Exception in get_crop_margin_from_dpi as ::", str(e))
        return 100


def get_crop_margin_from_text(min_x , min_y , max_x , max_y  , img_height ,img_width):
    try:

        total_text_length_horz = int(max_x - min_x)
        total_text_length_vert = int(max_y - min_y)
        pixcel_to_extend_horizontally = 0.25 * total_text_length_horz
        pixcel_to_extend_vertically = 0.25 * total_text_length_vert

        return pixcel_to_extend_horizontally ,pixcel_to_extend_vertically
    except Exception as e:
        print("Exception in get_crop_margin_from_text as ::", str(e))
        return img_width , img_height




def crop_and_generate_image_url(new_image_name ,csv_row ,sql_dict , jsonObj  ):
    """Preprocess the given image and returns the cropped image path and the Azure blob url associated with it (cropped image url)
    Args:
        new_image_name (str): Path of the folder where we are temporarily saving the images (STATIC FOLDER)
        csv_row (list): Name of the original image
        sql_dict (dict): Dict for logging the actions in SQLDB
        jsonObj (dict/ JSON): JSON obj containing the reponse of that request

    Returns:
        cropped_image_path (str): local path of the cropped image 
        crop_image_blob_url (str): Blob url of the cropped image
    """

    try:    
        folder_path = os.path.join("static")+"/"

        try:#preprocessing the image to crop the main object(document) from the document
            start_pp = time.time()
            jsonObj["Time"]["preprocess_start"] = str(datetime.now())
            cropped_image_path = preprocess_image(folder_path,new_image_name,folder_path)
            end_pp = time.time()
            # tempFilePaths.append(cropped_image_path)
            crop_image_name = cropped_image_path.split("/")[-1]
            upload_to_azure(cropped_image_path,crop_image_name)
            append_csv(csv_row , end_pp - start_pp)
            append_csv(csv_row , crop_image_name)  
            sql_dict.update({"preprocessing_time":  end_pp - start_pp})           
            sql_dict.update({"preprocess_image":  crop_image_name})           
        except Exception as e:
            print("Exception in image preprocessing: ",e)
            cropped_image_path = os.path.join(folder_path,new_image_name)
            crop_image_name = new_image_name
            append_csv(csv_row , "Preprocessing Failed")
            append_csv(csv_row , crop_image_name)
            sql_dict.update({"preprocessing_time": "Failed"})           
            sql_dict.update({"preprocess_image":  crop_image_name})  

        crop_image_blob_url = get_img_url_with_blob_sas_token(crop_image_name)    
        # new_image_url = get_img_url_with_blob_sas_token(new_image_name)
        jsonObj["Time"]["preprocess_done"] = str(datetime.now())
        return cropped_image_path , crop_image_blob_url 
    
    except Exception as e:
        print("Exception in crop_and_generate_image_url: ",e)
        return None , None
