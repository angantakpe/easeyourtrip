from PIL import Image 
import os , cv2 
import numpy as np
from src.utils.util import *
from src.azure_services.cloud import upload_to_azure , get_img_url_with_blob_sas_token
from src.azure_services.computerVision import face_api_request
from src.img_processing.img_process import get_response_image 
# from src.classifier.chroma import get_embedding
# import face_recognition
try:
    with open(os.path.join('assests', 'photoparams.json'), 'r') as f:
        photoparam = json.load(f)
    f.close()    
except Exception as e:
    print("Exception in openning photoparams.json as ::", str(e))


def cropImage(result,img_path,filename):
    try:
        #if the height  of the face detetced is less than 44% of the standard height then cropping is not needed. 
        if ((result["face_height"]/photoparam["params"]["image_height"])*100)<44:
            return False
        #if theactual height or width of the image is less than the standard image size, cropping  is not needed. 
        if (result["image_width"]<=photoparam["params"]["image_width"] or result["image_height"]<=photoparam["params"]["image_height"]):
            return False
        img = Image.open(img_path)

        # img.show()
        # faceRectangle : width (The width of the rectangle, in pixels ) , height	(The height of the rectangle, in pixels) , left(The distance from the left edge if the image to the left edge of the rectangle, in pixels.), top(The distance from the top edge if the image to the top edge of the rectangle, in pixels.)
        length = result["azure_response"][0]['faceRectangle']['width']
        height = result["azure_response"][0]['faceRectangle']['height']
        #calculating centre of the face by detecting the starting point of the face rectangle and adding half of the bbox length
        center = (result["azure_response"][0]['faceRectangle']['left']+(length/2), result["azure_response"][0]['faceRectangle']['left']+(height/2))
        if result["face_orientation_roll"]<=-2 or result["face_orientation_roll"]>4:
            img = img.rotate(result["face_orientation_roll"],center=center)

        if ((result["face_height"]/photoparam["params"]["image_height"])*100)>55:   #55 = 80 -25(80: minimum percentage of the face area required , 25: The assumed percentage distance skipped by the face api while detetecting face )
            # print("checking face height inside if block", (result["face_height"]/photoparam["params"]["image_height"])*100)
            scale_factor = photoparam["params"]["cropImage_scale_factor"] / result["face_height"]    
        else:
            scale_factor = 1
        #new height and width of the resized image
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)
        #takes input as pixcel (width, height) and resize the image
        resizedImg = img.resize((new_width, new_height))   

        img.close()
        newName = "resized_image.jpg"                   #Hardcoded name of resize_image file
        folder_path = os.path.join("static")+"/"
        resizedImg.save(os.path.join(folder_path,newName))

        length = int(result["azure_response"][0]['faceRectangle']['width'] * scale_factor)
        height = int(result["azure_response"][0]['faceRectangle']['height'] * scale_factor)

        #calculating the afce coordinates according to the new scaled image, as all the coordinates has been shifted in the same ratio as the scale factor
        faceCoord = [
            (int(result["azure_response"][0]['faceRectangle']['left'] * scale_factor),int(result["azure_response"][0]['faceRectangle']['top'] * scale_factor)),
            (int((result["azure_response"][0]['faceRectangle']['left']+result["azure_response"][0]['faceRectangle']['width']) * scale_factor), int((result["azure_response"][0]['faceRectangle']['top']) * scale_factor)),
            (int((result["azure_response"][0]['faceRectangle']['left']+result["azure_response"][0]['faceRectangle']['width']) * scale_factor), int((result["azure_response"][0]['faceRectangle']['top'] + result["azure_response"][0]['faceRectangle']['height']) * scale_factor)),
            (int((result["azure_response"][0]['faceRectangle']['left']) * scale_factor), int((result["azure_response"][0]['faceRectangle']['top'] + result["azure_response"][0]['faceRectangle']['height']) * scale_factor))
        ]
        #calculating coordinates to crop the face from the scaled image
        top = 0
        bottom = 0
        left = 0
        right = 0
        center = (faceCoord[0][0]+(length/2),faceCoord[0][1]+(height/2))
        if new_height >= photoparam["params"]["image_height"]:
            diffH = photoparam["params"]["image_height"] +1  - height
            #Moving upward by 75% of th height difference ,from the top left of the face coordinate, to cover the whole face
            top = faceCoord[0][1] - (0.75 * diffH)   
            diff = 0
            if top<0:
                #if the face top reaches above the height of the image  then consider top (top of the image) as the starting of the face coordinates.
                diff = 0 - top   
                top = 0 
            #Moving downward by 25% of th height difference ,from the buttom of the face coordinate, to cover the whole face
            bottom = (faceCoord[2][1]) + (0.25 * diffH) + diff
            if bottom > new_height:
                #if the buttom y coordinate is more than the image length then calcualting the extrafactor and adding it to both bottom and top of the image to get full bbox
                extra = bottom - new_height
                bottom = bottom - extra
                top = top - extra
                if top<0:
                    top = 0
        #if the current image has width more than standard width of the image then calculating coordinates of the the iamge to crop from side ways to capture face accuractely
        if new_width >= photoparam["params"]["image_width"]:
            diffW = photoparam["params"]["image_width"] + 1  - length
            #calculated the width difference successfully and then adding half of it to the leftb and right of the face centre to get accuarate coordinats for left and right crop
            left = (faceCoord[0][0]) - (0.50 * diffW)
            diff = 0
            if left<0:
                diff = 0 - left
                left = 0
            right = (faceCoord[1][0]) + (0.50 * diffW) + diff
            if right > new_width:
                extra = right - new_width
                right = right - extra
                left = left - extra
                if left<0:
                    left = 0
        if left>0 or right>0 or top>0 or bottom>0:
            #cropping the image with the resized coordinates
            cropImage = resizedImg.crop((left,top,right,bottom))
            imagename = generateName(filename,"_cropped")
            folder_path = os.path.join("static")+"/"
            cropImage.save(os.path.join(folder_path,imagename))
            return True
        return False
    except Exception as e:
        print('Exception in cropInmage as::', str(e))
        return False



#rescale the image according to the cropHeight and cropWidth then crops the face image and saves it.
def customCropImage(result, img_path, filename, cropHeight, cropWidth):
    try:
        img = Image.open(img_path)
        length, height = img.size
        faceLength = result["azure_response"][0]['faceRectangle']['width']
        faceHeight = result["azure_response"][0]['faceRectangle']['height']
        #calculating the centre of the face by calculating the edge of the bbox and travelling half of the distance from the side edges and top edges.
        center = (result["azure_response"][0]['faceRectangle']['left']+(faceLength/2), result["azure_response"][0]['faceRectangle']['left']+(faceHeight/2))
        if height<=cropHeight and length<=cropWidth:
            #if the image height is already is than the custom crop height and width then cropping cannot be performed. In such cases just check 'ROLL' orientation and save the image. 
            if result["face_orientation_roll"]<=-2 or result["face_orientation_roll"]>4:
                img = img.rotate(result["face_orientation_roll"],center=center)
            imagename = generateName(filename,"_cropped")
            folder_path = os.path.join("static")+"/"
            img.save(os.path.join(folder_path,imagename))
        else:
            faceLength = result["azure_response"][0]['faceRectangle']['width']
            faceHeight = result["azure_response"][0]['faceRectangle']['height']
            center = (result["azure_response"][0]['faceRectangle']['left']+(faceLength/2), result["azure_response"][0]['faceRectangle']['left']+(faceHeight/2))
            if result["face_orientation_roll"]<=-2 or result["face_orientation_roll"]>4:
                img = img.rotate(result["face_orientation_roll"],center=center)

            print("scaling down image to crop")
            scale_factor = 1
            #making facecoordinates from the top, left, width and height of the face rectangle.
            faceCoord = [
            (int(result["azure_response"][0]['faceRectangle']['left'] * scale_factor),int(result["azure_response"][0]['faceRectangle']['top'] * scale_factor)),
            (int((result["azure_response"][0]['faceRectangle']['left']+result["azure_response"][0]['faceRectangle']['width']) * scale_factor), int((result["azure_response"][0]['faceRectangle']['top']) * scale_factor)),
            (int((result["azure_response"][0]['faceRectangle']['left']+result["azure_response"][0]['faceRectangle']['width']) * scale_factor), int((result["azure_response"][0]['faceRectangle']['top'] + result["azure_response"][0]['faceRectangle']['height']) * scale_factor)),
            (int((result["azure_response"][0]['faceRectangle']['left']) * scale_factor), int((result["azure_response"][0]['faceRectangle']['top'] + result["azure_response"][0]['faceRectangle']['height']) * scale_factor))
            ]

            face_left = faceCoord[0][0]
            face_top = faceCoord[0][1]
            face_right = faceCoord[1][0]
            face_bottom = faceCoord[2][1]
            # Calculate the width and height of the face
            #adding 50% to the face height and width to cover the whole face image
            face_width = (face_right - face_left) + (faceLength * 0.50)
            face_height = (face_bottom - face_top) + (faceHeight * 0.50)

            # Calculate the scaling factor for the image
        
            required_dimensions = [cropWidth,cropHeight]
            scale_factor_width = required_dimensions[0] / face_width
            scale_factor_height = required_dimensions[1] / face_height
            scale_factor = min(scale_factor_width, scale_factor_height)

            # Calculate the new dimensions for the image
            new_width = int(img.size[0] * scale_factor)
            
            if new_width<cropWidth:
                scale_factor = 1
                #if the new_width is less then cropwidth then new width of the image remains unchanged
                new_width = int(img.size[0] * scale_factor)
            new_height = int(img.size[1] * scale_factor)
            if new_height<cropHeight:
                #if the new_height is less then cropHeight then new width and height of the image remains unchanged
                scale_factor = 1
                new_width = int(img.size[0] * scale_factor)
                new_height = int(img.size[1] * scale_factor)
            resizedImg = img.resize((new_width, new_height))
            # Calculate the position of the face in the scaled image
            center = [center[0]*scale_factor, center[1]*scale_factor]
            new_face_left = center[0] - (cropWidth/2)
            # print("new_face_left: ",new_face_left)
            diff = 0
            if new_face_left < 0:
                diff = new_face_left*-1
                new_face_left = 0
            new_face_right = center[0] + (cropWidth/2) + diff
            # print("new_face_right: ",new_face_right)
            # print("newImage Width: ",(new_face_right-new_face_left))
            if new_face_right>new_width:
                diff = new_face_right - new_width
                new_face_right = new_width
                if new_face_left>0:
                    new_face_left = new_face_left - diff
                if new_face_left < 0:
                    new_face_left = 0
            new_face_top = center[1] - (0.4 * cropHeight)
            # print("new_face_top: ",new_face_top)
            diff = 0
            if new_face_top<0:
                diff = new_face_top*-1
                new_face_top = 0
            new_face_bottom = center[1] + (0.6 * cropHeight) + diff
            # print("new_face_bottom: ",new_face_bottom)
            # print("newImage Height: ",(new_face_bottom - new_face_top))
            if new_face_bottom>new_height:
                diff = new_face_bottom - new_height
                new_face_bottom = new_height
                if new_face_top > 0:
                    new_face_top  = new_face_top - diff
                if new_face_top<0:
                    new_face_top = 0
            newImageHeight = (new_face_bottom-new_face_top)
            newImageWidth = (new_face_right-new_face_left)
            if newImageHeight<350:
                new_face_bottom = new_face_bottom + 1
                # new_face_top = new_face_top - 1
                newImageHeight = newImageHeight + 1
            if newImageWidth<350:
                # new_face_left = new_face_left - 1
                new_face_right = new_face_right + 1
                newImageWidth = newImageWidth + 1
            # print("newImage Height: ",newImageHeight)
            # print("newImage Width: ",newImageWidth)

            # Crop the face from the original image
            face_image = resizedImg.crop((new_face_left, new_face_top, new_face_right, new_face_bottom))

            # Save the scaled image
            # cropImage = resizedImg.crop((left,top,right,bottom))
            imagename = generateName(filename,"_cropped")
            folder_path = os.path.join("static")+"/"
            face_image.save(os.path.join(folder_path,imagename))
        return True

    except Exception as e:
        print("Exception occured in customCropImage: ",e)
        img = Image.open(img_path)
        imagename = generateName(filename,"_cropped")
        folder_path = os.path.join("static")+"/"
        img.save(os.path.join(folder_path,imagename))
    


#analyses the image's different aspect like image_width, height,exposure ,noise, occulance ,Face Detection Test, Background Check, Expression , Height test,Tilt test,alignment test, face area test  
# and makes a list as ["Test name", "ok/detected" , "status(pass , fail)" , "data(data regarding that test)"] passes "Pass", "Fail" for all the different cases.  
def getImageAnalysis(result, img_path, img_name):
    try:    
        img_dpi = int(photoparam["params"]["dpi"])
        data1=[["Image Dimension Test","35*45 mm min.",(str(round((result["image_width"]*25.4)/img_dpi,2)))+"*"+(str(round((result["image_height"]*25.4)/img_dpi,2)))+" mm"]]
        convert_to_mm = lambda x: [round((float(el) * 25.4) / img_dpi,2) for el in x]   #converting pixcels to mm, 
        # print("convert_to_mm:::", convert_to_mm)
        # print("image_width:::", result["image_width"])
        # print("image_height:::", result["image_height"])
        #This Python expression is converting the width and height of the image from pixels to millimeters (mm), assuming the image's resolution is 300 DPI(img_dpi)
        dict = {"image_width":(str(round((result["image_width"]*25.4)/img_dpi,2))+" mm"), "image_height":(str(round((result["image_height"]*25.4)/img_dpi,2))+" mm"), "aspect_ratio":(result["image_width"]/result["image_height"])}
        if result["image_width"]<photoparam["params"]["image_width"] or result["image_height"]<photoparam["params"]["image_height"] or result["image_width"]/result["image_height"]<0.77 or result["image_width"]/result["image_height"]>0.78:
        #checking image width and image height according to CANADA  portal.(413, 531) as required diamentions are 35 mm and 45 mm so checkig the pixel value of the 35(413) and 45(531).
            data1[0].append("Fail")
            data1[0].append(dict)
        else:
            data1[0].append("Pass")
            data1[0].append(dict)
    
        dict = {"Exposure Level": result["exposure_level"],"exposure_value":result["exposure_value"], "Noise Level": result["noise_level"],"noise_value":result["noise_value"], "Blur Level": result["blur_level"],"blur_value":result["blur_value"]}
        data1.append(["Image Quality Check", "Ok", "", None])  #checking Image Quality parameter with params like Noise level, exposure, blur.
        if result["exposure_level"]=="goodExposure" and (result["noise_level"]=="low" or result["noise_level"]=="medium") and result["blur_level"]=="low":
            data1[1][2] = "Ok"
            data1[1][3] = "Pass"
            data1[1].append(dict)
        else:
            data1[1][2] = "Not Ok"
            data1[1][3] = "Fail"
            data1[1].append(dict)
        
        data1.append(["Face Detection Test","Detected"]) #checking if there is a face detected in the image or not. If multiple faces are detected then Detection is considered as Failed.
        if result["number_of_faces"]!=1:
            data1[2].append("Not Detected")
            data1[2].append("Fail")
            data1[2].append({"Number of Faces": result["number_of_faces"]})
            return data1
        else:  #only if One face is detected
            displayFace(result, img_path, img_name) #This function circles the eyes , nose , lips(upppr and lower) total 9 points on the image and saves it on the cloud.
            data1[2].append("Detected")
            data1[2].append("Pass")
            data1[2].append({"Number of Faces": result["number_of_faces"]})

        if data1[2][3]=="Pass":                 #calculating the centre of the Image and centre of the detected face.
            imgW = result["image_width"]
            imgH = result["image_height"]
            faceW = result["face_width"]
            result["faceCenter"] = ((result["azure_response"][0]["faceRectangle"]["left"]+(result["face_width"]/2)), (result["azure_response"][0]["faceRectangle"]["top"]-(result["face_height"]/2)))
            result["imageCenter"] = (imgW/2, imgH/2)

            data1.append(["Background Check", "Plain", "", None])   #checking for background type plain or non plain.
            if result["image_background"] == "Plain":
                data1[3][2] = "Plain"
                data1[3][3] = "Pass"
                data1[3].append({"Image Background": result["image_background"]})
            else:
                data1[3][2] = "Not Plain"
                data1[3][3] = "Fail"
                data1[3].append({"Image Background": result["image_background"]})
            #detecting and marking Occulance and accesories in the image
            data1.append(["Occlusion Detection Test", "No Occlusion", "", None])   
            dict={"accessories": result["accessories"], "Occlusion Eye":result["occlusion_eye"], "Occlusion mouth":result["occlusion_mouth"], "Occlusion forehead":result["occlusion_forehead"], "Eyes Identified":result["eyes_identified"], "Glasses": result["glasses_present"]}
            if result["occlusion_eye"]==False and result["occlusion_mouth"]==False and result["eyes_identified"]==True and (result["glasses_present"]=="NoGlasses" or result["glasses_present"]=="ReadingGlasses"):
                if result["accessories"]!="None":  
                    if len(result["accessories"])>1:
                        data1[4][2] = "Occlusion detected"
                        data1[4][3] = "Fail"
                    elif ((result["accessories"][0]["type"]=="headwear" and result["accessories"][0]["confidence"]<0.9) or (result["accessories"][0]["type"]=="ReadingGlasses" and result["accessories"][0]["confidence"]<0.9) or (result["accessories"][0]["type"]!="headwear" and result["accessories"][0]["type"]!="ReadingGlasses")):
                        data1[4][2] = "Occlusion detected"
                        data1[4][3] = "Fail"
                    
                    elif (result["accessories"][0]["type"]=="headwear" and result["accessories"][0]["confidence"]>=0.9 and result["occlusion_forehead"]==True):
                        data1[4][2] = "No Occlusion"
                        data1[4][3] = "Pass"

                data1[4][2] = "No Occlusion"
                data1[4][3] = "Pass"
                data1[4].append(dict)
            else:
                data1[4][2] = "Occlusion detected"
                data1[4][3] = "Fail"
                data1[4].append(dict)

            # data1.append(["Facial Expression Test", "neutral", "", "To be done"])
            #standard face height according to canada portal is 31- 36 mm
            data1.append(["Face Height Test","Between 31 - 36 mm"])   
            #if the detetcted face height is less than 44% it means the face is not considered to be 69-80% of the total image , indicates the face height is less than 31 mm for the standaed 45mm image size.
            if ((result["face_height"]/result["image_height"])*100)<44 or ((result["face_height"]/result["image_height"])*100)>55:
                data1[5].append("Outside (31 - 36 mm)")
                data1[5].append("Fail")
                #The Face detected by face api is not excatly the full face but a more cropped version of the face. To cover the full face of the person we adding 25% of the face height. 
                face_height = ((((result["face_height"]/result["image_height"])*100)+25)/100)*result["image_height"]
                data1[5].append({"Face Height":str(round((face_height*25.4)/img_dpi,2))+" mm", "Image Height":str(round((result["image_height"]*25.4)/img_dpi,2))+" mm"})
            else:
                data1[5].append("Between 31 - 36 mm")
                data1[5].append("Pass")
                #The Face detected by face api is not excatly the full face but a more cropped version of the face. To cover the full face of the person we adding 25% of the face height. 
                face_height = ((((result["face_height"]/result["image_height"])*100)+25)/100)*result["image_height"]   
                data1[5].append({"Face Height":str(round((face_height*25.4)/img_dpi,2))+" mm", "Image Height":str(round((result["image_height"]*25.4)/img_dpi,2))+" mm"})
            #checking if the face in the image is roll(face tilted towards shoulder)
            data1.append(["Face Tilt Test","(-10) - (10)"])  
            # print("face_orientation_roll::::",result["face_orientation_roll"] )
            if  result["face_orientation_roll"]<=-10 or result["face_orientation_roll"]>10:
                data1[6].append(result["face_orientation_roll"])
                data1[6].append("Fail")
                data1[6].append({"Face Roll": round(result["face_orientation_roll"] , 2)})
            else:
                data1[6].append(result["face_orientation_roll"])
                data1[6].append("Pass")
                data1[6].append({"Face Roll": round(result["face_orientation_roll"] , 2)})
            #checking for face alignment and calculating facecentre and image centre in millimeter.
            data1.append(["Face Alignment Test", "In Center"])    
            if (result["faceCenter"][0] < (result["imageCenter"][0]+((10/100)*faceW)) and result["faceCenter"][0] > (result["imageCenter"][0]-((10/100)*faceW))):
                data1[7].append("In Center")
                data1[7].append("Pass")
                data1[7].append({"Face Center": convert_to_mm(result["faceCenter"]), "Image Center":convert_to_mm(result["imageCenter"])})
            else:
                data1[7].append("Not in center")
                data1[7].append("Fail")
                data1[7].append({"Face Center": convert_to_mm(result["faceCenter"]), "Image Center":convert_to_mm(result["imageCenter"])})

            data1.append(["Face Facing Straight", "Straight"])  #checking if the face in the image is looking straight or not. (checks if the person is looking straight forward or in any other direction)
            # print("face_orientation_yaw::::",result["face_orientation_yaw"] , "face_orientation_pitch::::",result["face_orientation_pitch"])
            if ((result["face_orientation_yaw"]<-10 or result["face_orientation_yaw"]>10) or (result["face_orientation_pitch"]<-10 or result["face_orientation_pitch"]> 10)):
                data1[8].append("Not Straight")
                data1[8].append("Fail")#person not looking straight
                data1[8].append({"Face Yaw": round(result["face_orientation_yaw"] , 2), "Face Pitch":  round(result["face_orientation_pitch"] , 2)})
            else:
                data1[8].append("Straight")
                data1[8].append("Pass")
                data1[8].append({"Face Yaw": round(result["face_orientation_yaw"] , 2), "Face Pitch":  round(result["face_orientation_pitch"] , 2)})
            
            data1.append(["Face Area Test","69-80 %"])  
            if (round(result["face_area"]*100) < 24.0 or round(result["face_area"]*100) > 69.0):
                data1[9].append(result["face_area"]*100)
                data1[9].append("Fail")
                data1[9].append({"Face Area": result["face_area"]*100})
            else:
                data1[9].append(result["face_area"]*100)
                data1[9][2] = "covers 69 - 80 %"
                data1[9].append("Pass")
                if (result["face_area"]*100)<45:    #assumming the detected area of the face (The azure face api detects face as a small part of the original face, so assuming it to be 45% of the total image if the person face is 69-80% of the image.)
                    data1[9].append({"Face Area": str(70)+" %"})
                else:
                    data1[9].append({"Face Area": str(80)+" %"})

            colour_of_image = is_colored_image(img_path)
            data1.append(["Coloured Image Test", "Coloured"])  
            if colour_of_image == "Black_and_white":
                data1[10].append("Black And White")
                data1[10].append("Fail")
                data1[10].append({"Colour Status":"Black And White"})
            else:
                data1[10].append("Coloured")
                data1[10].append("Pass")
                data1[10].append({"Colour Status":"Coloured"})

        # print("data1 final:::", data1)
        return data1
    except Exception as e:
        print("Exception in getImageanlysis as :", str(e))
        return data1
    


#the function is used to return the result dictionary with its 'file_path', binary data(pil object) of the original and the RGB converted images. Also its adds the 'remarks' and 'process status' of the process. 
#result is a dictionary with  :::["file_size", "file_size_pass" , "monochrome" ,"contrast","image_height","image_width" ,"img_frame_pass", .....]
def make_images(result,file_path):
    #use only in Valid Image route
    try:
        result["file_path"] = file_path
        result["pil_image"] = Image.open(result["file_path"])
        temp = Image.open(result["file_path"])
        result["pil_image_converted"] = temp.convert('RGB')
        temp.close()
        return result
    except:
        result["pil_image"] = None
        result["pil_image_converted"] = None
        result["remarks"] = result["remarks"] + " FAILURE DURING MAKING PIL IMAGES. "
        result["process_status"] = "EXCEPTION OCCURRED"
        return result
    
#use for static evaluations of the image like 'height' , 'width', checking if the Image is Monochromatic , 
# aspect_ratio and image frame pass(ratio of image width and height) along with the 'remarks' and process status
def static_evaluation(result , file_path): 
    try:
        result["pil_image"] = Image.open(file_path)

        result["image_width"], result["image_height"] = result["pil_image"].size
        result["image_width"] = result["image_width"]
        result["image_height"] = result["image_height"]
        #image_width = 413 and image_height = 531 for canada visa requireemnt(35 mm and 45 mm)
        if result["image_width"] >= photoparam["params"]["image_width"] and result["image_height"] >= photoparam["params"]["image_height"] and ((result["image_width"]/result["image_height"])>=0.77 or (result["image_width"]/result["image_height"])<=0.78):
            result["img_frame_pass"] = True
        else:
            result["img_frame_pass"] = False
    except:
        result["image_width"], result["image_height"] = 0, 0
        result["img_frame_pass"] = False
        # result["remarks"] = result["remarks"] + " FAILURE AT DETERMINING IMAGE DIMENSIONS. "
        # result["process_status"] = "EXCEPTION OCCURRED"
    try:
        to_break = False
        result["monochrome"] = True
        w, h = result["pil_image_converted"].size
        for i in range(w):
            for j in range(h):
                r, g, b = result["pil_image_converted"].getpixel((i, j))
                if r != g != b:
                    result["monochrome"] = False
                    to_break = True
                    break
            if to_break:
                break
    except:
        result["monochrome"] = False
        # result["remarks"] = result["remarks"] + " FAILURE AT MONOCHROME DETERMINATION. "
        # result["process_status"] = "EXCEPTION OCCURRED"

    try:
        result["contrast"] = round(np.mean(result["pil_image"]), 2)
    except:
        result["contrast"] = 0.0
        # result["remarks"] = result["remarks"] + " FAILURE AT CONTRAST CALCULATION. "
        # result["process_status"] = "EXCEPTION OCCURRED"

    try:
        if result["image_height"] > 0 and result["image_width"] > 0:
            result["aspect_ratio"] = result["image_width"]/result["image_height"]
        # else:
        #     result["aspect_ratio"] = 0.0
        return result
    except:
        result["remarks"] = result["remarks"] + " ASPECT RATIO FAILED TO CALCULATE"
        result["process_status"] = "EXCEPTION OCCURED"
        return result
        

#marks the facial features on the face image like eye, nose, mouth , lips and saves the image to the blob. 
def displayFace(result, img_path, img_name):
    try:
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        leftEyex = result["azure_response"][0]["faceLandmarks"]["pupilLeft"]["x"]
        leftEyey = result["azure_response"][0]["faceLandmarks"]["pupilLeft"]["y"]
        rightEyex = result["azure_response"][0]["faceLandmarks"]["pupilRight"]["x"]
        rightEyey = result["azure_response"][0]["faceLandmarks"]["pupilRight"]["y"]
        nosex = result["azure_response"][0]["faceLandmarks"]["noseTip"]["x"]
        nosey = result["azure_response"][0]["faceLandmarks"]["noseTip"]["y"]
        mouthLeftx = result["azure_response"][0]["faceLandmarks"]["mouthLeft"]["x"]
        mouthLefty = result["azure_response"][0]["faceLandmarks"]["mouthLeft"]["y"]
        mouthRightx = result["azure_response"][0]["faceLandmarks"]["mouthRight"]["x"]
        mouthRighty = result["azure_response"][0]["faceLandmarks"]["mouthRight"]["y"]
        upperLipTopx = result["azure_response"][0]["faceLandmarks"]["upperLipTop"]["x"]
        upperLipTopy = result["azure_response"][0]["faceLandmarks"]["upperLipTop"]["y"]
        upperLipBottomx = result["azure_response"][0]["faceLandmarks"]["upperLipBottom"]["x"]
        upperLipBottomy = result["azure_response"][0]["faceLandmarks"]["upperLipBottom"]["y"]
        underLipTopx = result["azure_response"][0]["faceLandmarks"]["underLipTop"]["x"]
        underLipTopy = result["azure_response"][0]["faceLandmarks"]["underLipTop"]["y"]
        underLipBottomx = result["azure_response"][0]["faceLandmarks"]["underLipBottom"]["x"]
        underLipBottomy = result["azure_response"][0]["faceLandmarks"]["underLipBottom"]["y"]

        cv2.circle(img,center=(round(leftEyex),round(leftEyey)),color=(255,0,0),thickness=3,radius=2)
        cv2.circle(img,center=(round(rightEyex),round(rightEyey)),color=(255,0,0),thickness=3,radius=2)
        cv2.circle(img,center=(round(nosex),round(nosey)),color=(255,0,0),thickness=3,radius=2)
        cv2.circle(img,center=(round(mouthLeftx),round(mouthLefty)),color=(255,0,0),thickness=3,radius=2)
        cv2.circle(img,center=(round(mouthRightx),round(mouthRighty)),color=(255,0,0),thickness=3,radius=2)
        cv2.circle(img,center=(round(upperLipTopx),round(upperLipTopy)),color=(255,0,0),thickness=3,radius=2)
        cv2.circle(img,center=(round(upperLipBottomx),round(upperLipBottomy)),color=(255,0,0),thickness=3,radius=2)
        cv2.circle(img,center=(round(underLipTopx),round(underLipTopy)),color=(255,0,0),thickness=3,radius=2)
        cv2.circle(img,center=(round(underLipBottomx),round(underLipBottomy)),color=(255,0,0),thickness=3,radius=2)
        cv2.rectangle(img,pt1=(result["azure_response"][0]["faceRectangle"]["left"],result["azure_response"][0]["faceRectangle"]["top"]),pt2=(result["azure_response"][0]["faceRectangle"]["left"]+result["azure_response"][0]["faceRectangle"]["width"],result["azure_response"][0]["faceRectangle"]["top"]+result["azure_response"][0]["faceRectangle"]["height"]),color=(255,0,0),thickness=3)
        folder_path = os.path.join("static")+"/"
        img = Image.fromarray(img, 'RGB')
        imagename = generateName(img_name,"_output")
        img.save(os.path.join(folder_path,imagename))
        upload_to_azure(os.path.join(folder_path,imagename), imagename)

    except Exception as e:    
        print("Exception in displayFace as :", str(e))

# Here the different aspects of the face like width , height , area , exposure , noise , blur , eyes , occlusion ..etc are collected from the faceapi response.  
#function is use to collect some required fields from the azurefaceapi response. 
def digest_azure_response(result, img_path, imageName):
        try:
            if result["azure_response"] is not None:
                if result["azure_response"] == []:
                    result["face_width"] = 0.0
                    result["face_height"] = 0.0
                    result["face_area"] = 0.0
                    result["exposure_value"] = 0.0
                    result["exposure_level"] = "None"
                    result["noise_value"] = 0.0
                    result["noise_level"] = "None"
                    result["blur_value"] = 0.0
                    result["blur_level"] = "None"
                    result["eyes_identified"] = False
                    result["glasses_present"] = "None"
                    result["face_orientation_pitch"] = 0.0
                    result["face_orientation_yaw"] = 0.0
                    result["face_orientation_roll"] = 0.0
                    result["accessories"] = "None"
                    result["occlusion_forehead"] = False
                    result["occlusion_mouth"] = False
                    result["occlusion_eye"] = False
                    result["number_of_faces"] = 0
                else:

                    if result["azure_response"][0]["faceRectangle"]["width"]:
                        result["face_width"] = result["azure_response"][0]["faceRectangle"]["width"]
                    else:
                        result["face_width"] = 0.0

                    if result["azure_response"][0]["faceRectangle"]["height"]:
                        result["face_height"] = result["azure_response"][0]["faceRectangle"]["height"]
                    else:
                        result["face_height"] = 0.0
                        
                    image_area = int(result["image_width"] * result["image_height"])
                    result["face_area"] = float((result["face_height"] * result["face_width"])/image_area)

                    if result["azure_response"][0]["faceAttributes"]["exposure"]["exposureLevel"]:
                        result["exposure_level"] = result["azure_response"][0]["faceAttributes"]["exposure"]["exposureLevel"]
                    else:
                        result["exposure_level"] = "None"

                    if result["azure_response"][0]["faceAttributes"]["exposure"]["value"]:
                        result["exposure_value"] = result["azure_response"][0]["faceAttributes"]["exposure"]["value"]
                    else:
                        result["exposure_value"] = 0.0

                    if result["azure_response"][0]["faceAttributes"]["noise"]["noiseLevel"]:
                        result["noise_level"] = result["azure_response"][0]["faceAttributes"]["noise"]["noiseLevel"]
                    else:
                        result["noise_level"] = "None"

                    if result["azure_response"][0]["faceAttributes"]["noise"]["value"]:
                        result["noise_value"] = result["azure_response"][0]["faceAttributes"]["noise"]["value"]
                    else:
                        result["noise_value"] = 0.0

                    if result["azure_response"][0]["faceAttributes"]["blur"]["blurLevel"]:
                        result["blur_level"] = result["azure_response"][0]["faceAttributes"]["blur"]["blurLevel"]
                    else:
                        result["blur_level"] = "None"
                    
                    if result["azure_response"][0]["faceAttributes"]["blur"]["value"]:
                        result["blur_value"] = result["azure_response"][0]["faceAttributes"]["blur"]["value"]
                    else:
                        result["blur_value"] = 0.0

                    if result["azure_response"][0]["faceAttributes"]["glasses"]:
                        result["glasses_present"] = result["azure_response"][0]["faceAttributes"]["glasses"]
                    else:
                        result["glasses_present"] = "None"

                    if result["azure_response"][0]["faceAttributes"]["headPose"]["pitch"]:
                        result["face_orientation_pitch"] = result["azure_response"][0]["faceAttributes"]["headPose"]["pitch"]
                    else:
                        result["face_orientation_pitch"] = 0.0
                    # Pitch is the up-and-down tilt of the head.
                    if result["azure_response"][0]["faceAttributes"]["headPose"]["yaw"]:
                        result["face_orientation_yaw"] = result["azure_response"][0]["faceAttributes"]["headPose"]["yaw"]
                    else:
                        result["face_orientation_yaw"] = 0.0
                    #Yaw is the rotation of the head from side to side (left to right).
                    if result["azure_response"][0]["faceAttributes"]["headPose"]["roll"]:
                        result["face_orientation_roll"] = result["azure_response"][0]["faceAttributes"]["headPose"]["roll"]
                    else:
                        result["face_orientation_roll"] = 0.0
                    #Roll refers to the tilt of the head sideways, as if tilting the head to one shoulder.    
                    if result["azure_response"][0]["faceAttributes"]["accessories"]:
                        result["accessories"] = str(result["azure_response"][0]["faceAttributes"]["accessories"])
                    else:
                        result["accessories"] = "None"
                        
                    if result["azure_response"][0]["faceAttributes"]["occlusion"]["foreheadOccluded"]:
                        result["occlusion_forehead"] = True
                    else:
                        result["occlusion_forehead"] = False

                    if result["azure_response"][0]["faceAttributes"]["occlusion"]["eyeOccluded"]:
                        result["occlusion_eye"] = True
                    else:
                        result["occlusion_eye"] = False

                    if result["azure_response"][0]["faceAttributes"]["occlusion"]["mouthOccluded"]:
                        result["occlusion_mouth"] = True
                    else:
                        result["occlusion_mouth"] = False

                    if result["azure_response"][0]["faceLandmarks"]["pupilLeft"]["x"] != 0.0 or result["azure_response"][0]["faceLandmarks"]["pupilLeft"]["y"] != 0.0 or result["azure_response"][0]["faceLandmarks"]["pupilRight"]["x"] != 0.0 or result["azure_response"][0]["faceLandmarks"]["pupilRight"]["y"] != 0.0:
                        result["eyes_identified"] = True
                    else:
                        result["eyes_identified"] = False
                    
                    if result["azure_response"] is not None:
                        if len(result["azure_response"]) > 0:
                            height = result["image_height"]
                            width = result["image_width"]
                            ftop = result["azure_response"][0]['faceRectangle']['top']      ## face api bounding box parameters
                            fleft = result["azure_response"][0]['faceRectangle']['left']
                            fwidth = result["azure_response"][0]['faceRectangle']['width']
                            fheight = result["azure_response"][0]['faceRectangle']['height']
                            diffwidth = width - fwidth
                            diffheight = height - fheight
                            if diffwidth >= 50:                            ## checking if only face is there i.e no background (threshold is 50)
                                height = height                    ## cut bottom area by 30%
                                q1 = (0,0,(fleft - (fwidth * 0.14)),ftop)  
                                cropq1 = Image.open(img_path).convert('RGB').crop(q1)
                                folder_path = os.path.join("static")+"/"
                                cropq1Path = folder_path+generateName(imageName,'cropq1')
                                cropq1.save(os.path.join(folder_path,generateName(imageName,'cropq1')))
                                crop2top = fleft + fwidth + (fwidth * 0.14)
                                q2 = (crop2top,0,width,ftop)
                                cropq2 = Image.open(img_path).convert('RGB').crop(q2)
                                cropq2.save(os.path.join(folder_path,generateName(imageName,'cropq2')))
                                cropq2Path = folder_path+generateName(imageName,'cropq2')

                                if check_background(cropq1Path) and check_background(cropq2Path):      ## threshold is 10 to coverup the margin ratio
                                    result["image_background"] = "Plain"
                                else:
                                    result["image_background"] = "Textured"
                                try:
                                    os.remove(cropq1Path) 
                                    os.remove(cropq2Path) 
                                except Exception as e:
                                    print("Exception in deleteing croppedQ's files: ",e)
                            else:
                                result["image_background"] = "Undetermined"
                        else:
                            result["image_background"] = "Undetermined"
                    else:
                        result["image_background"] = "Undetermined"
                        
                    result["number_of_faces"] = len(result["azure_response"])
                return result
        except:
            result["remarks"] = result["remarks"] + " FAILURE AT DIGESTING THE AZURE RESPONSE. "
            result["process_status"] = "EXCEPTION OCCURRED"
            return result

#checks if there is any fail results in the result of getImageAnalysis. Return True if there is a fail parameter.
def isPhotoValid(result):
    try:
        anyFail = False
        for i in result:
            # print("I in result:::", i[3])
            
            if i[3]=="To be done" or i[3]==None:
                continue
            elif i[3]!="Pass":
                anyFail = True
        return anyFail
    except Exception as e:
        print("Exception in isPhotoValid as :", str(e))
        return False


def check_background(img_path):  
    try:  
        img = cv2.imread(img_path)
        color = ['b','g','r']
        std_dev = []
        for i,color in enumerate(color):
            hist = cv2.calcHist([img],[i],None,[256],[0,256])
            std_dev.append(np.std(hist))

        for i in range(len(std_dev)-1):
            diff = (std_dev[i]-std_dev[i+1])
            if diff<0:
                diff = diff * -1
            if diff>150:
                return False
        for i in std_dev:
            if i<100:
                return False
        return True
    except Exception as e:
        print("Exeption in check_background as :", str(e))
        return True

#makes the final output with adding all the tests performed during the 'getImageAnalysis' method, and 
#adds this into the final output of the API. and adds "outputImgPath" (final image path dereived from the original filename.)
def getJson(result2,filename,uploadFileName,final):
    try:
        result = {"DocCategory":"Photo", "filename":uploadFileName, "isPass":(not final)}
        testResults = []
        for i in result2:
            data = {"test":"", "status":"", "data":""}
            if(i[3]=="To be done"):
                continue
            data["test"] = i[0]
            data["status"] = i[3]
            data["data"] = i[4]
            testResults.append(data)
        result["tests"] = testResults
        if result2[2][4]["Number of Faces"]==1:
            imagename = generateName(filename,"_output")
            imagepath = os.path.join("static")+"/"+imagename
            result["outputImgPath"] = imagepath
        return result
    except Exception as e:
        print("Exception in getJson as :", str(e))


def get_face_landmarks(uploadFileName, img_path ,image_name,customCrop , cropHeight ,cropWidth ,cropImg, jsonObj , tempFilePaths):
    try:
        print("inside get_face_landmarks")
        result = {
                    "file_size" : None,
                    "file_size_pass" : False,
                    "monochrome" : False,
                    "contrast" : 0.0,
                    "image_height" : 0.0,
                    "image_width" : 0.0,
                    "img_frame_pass" : False,
                    "remarks" : "",
                    "process_status" : None,
                    "pil_image" : None,
                    "pil_image_converted" : None,
                    "file_path" : "",
                    "aspect_ratio" : 0.0
                        }
        
        # result = make_images(result,img_path)  #returns 'file_path', binary data(pil object) of the original and the RGB converted images. Also its adds the 'remarks' and 'process status' of the process. 
        result = static_evaluation(result ,img_path )
        result = face_api_request(result, img_path)  #calls the AZURE FACEAPI endpoint
        
        #checking if azureFaceDetection_Raw_Response present in the result dictionary. If present then removing it from it.
        if "azureFaceDetection_Raw_Response" in result:
            jsonObj["azureFaceDetection_Parsed_Response"] = result["azureFaceDetection_Parsed_Response"]
            jsonObj["azureFaceDetection_Raw_Response"] = result["azureFaceDetection_Raw_Response"]
            del result["azureFaceDetection_Raw_Response"]
            del result["azureFaceDetection_Parsed_Response"]
        
        result =  digest_azure_response(result, img_path, image_name)  #collecting  all necessary deatils from the faceapi response like:: width , height , area , exposure , noise , blur , eyes , occlusion ..etc are collected from the faceapi response.  
        digResp = result
        del digResp["pil_image"]
        del digResp["pil_image_converted"]
        jsonObj["digest_Azure_Response"] = digResp

        # print("result of digest resp::::",digResp )
        #analyses the image's different aspect like image_width, height,exposure ,noise, occulance ,Face Detection Test, Background Check, Expression , Height test,Tilt test,alignment test, face area test  
        result2 = getImageAnalysis(result, img_path, image_name)
        # print("result2::::::::::", result2)
        jsonObj["image_Analysis_Response"] = result2
        
        final = isPhotoValid(result2)  #getImageAnalysis gives a  list of validation s on differents aspects like::image_width, height,exposure ,noise, occulance ,Face Detection Test, Background Check, Expression , Height test,Tilt test,alignment test, face area test. This function checks if there is a failed entity and returns false if there is else True.
        jsonObj["photoValid"] = not final
        crop_img_path = None
        # if final:
        if result["number_of_faces"]==1:
            # print("customCrop variable outside if block: ",customCrop)
            # print("cropImg variable outside if block: ",cropImg)
            #customCrop and cropImage works only when parameters regarding them are passed through the API headers.
            if customCrop:
                # print("customCrop inside if block: ",customCrop)
                #
                if customCropImage(result, img_path, image_name, cropHeight, cropWidth):
                    folder_path = os.path.join("static")+"/"
                    imagename = generateName(image_name,"_cropped")
                    crop_img_path = folder_path+ imagename
                    upload_to_azure(crop_img_path, imagename)
                    jsonObj["croppedImageName"] = imagename
            elif cropImg:
                if cropImage(result, img_path, image_name):
                    folder_path = os.path.join("static")+"/"
                    imagename = generateName(image_name,"_cropped")
                    crop_img_path = folder_path+ imagename
                    print("crop_img_path::::",crop_img_path)
                    upload_to_azure(crop_img_path, imagename)
                    jsonObj["croppedImageName"] = imagename
        apiResponse = getJson(result2,image_name,uploadFileName,final)
        outputImgPath = apiResponse.get("outputImgPath",None)
        # print("outputImgPath is: ",outputImgPath)

        if outputImgPath!=None:
            jsonObj["outputImageName"] = generateName(image_name,"_output")
            outputImgPath = os.path.join(outputImgPath)
            outputImgname = outputImgPath.split("/")[-1]
            upload_to_azure(outputImgPath,outputImgname)
            base64img, mimetype = get_response_image(outputImgPath)
            tempFilePaths.append(outputImgPath) 
            # with open(outputImgPath, 'rb') as im:
            #     # Convert the image to a base64 string.
            #     encoded_string2 = base64.b64encode(im.read()).decode('utf-8')
            # im.close()
            outputImg_url  = get_img_url_with_blob_sas_token(outputImgname)
            apiResponse["base64img"] = outputImg_url
            apiResponse.pop('outputImgPath')
            apiResponse["mimetype"] = mimetype
            jsonObj["outputImageMimetype"] = mimetype
        else:
            base64img, mimetype = get_response_image(img_path)
            tempFilePaths.append(img_path)
            # with open(img_path, 'rb') as im:
            #     # Convert the image to a base64 string.
            #     encoded_string2 = base64.b64encode(im.read()).decode('utf-8')
            # im.close()
            outputImg_url  = get_img_url_with_blob_sas_token(image_name)
            apiResponse["base64img"] = outputImg_url
            apiResponse["mimetype"] = mimetype
            
        if crop_img_path!=None:
            outputImgPath = os.path.join(crop_img_path)
            outputImgname = outputImgPath.split("/")[-1]
            upload_to_azure(outputImgPath, outputImgname)
            tempFilePaths.append(outputImgPath)
            # with open(outputImgPath, 'rb') as im:
            #     # Convert the image to a base64 string.
            #     encoded_string = base64.b64encode(im.read()).decode('utf-8')
            # im.close()
            # Get the mimetype of the image.
            outputImg_url  = get_img_url_with_blob_sas_token(outputImgname)
            mimetype = "image/jpeg"
            apiResponse["base64cropImg"] = outputImg_url
            apiResponse["mimetype_cropImg"] = mimetype
            jsonObj["croppedImageMimetype"] = mimetype
            apiResponse["croppedImage"] = True
        else:
            apiResponse["croppedImage"] = False
        jsonObj["requestResponse"] = apiResponse
        
        return apiResponse
    except Exception as e:
        print("Exception in get_face_landmarks as ::", str(e))    
        return {}



