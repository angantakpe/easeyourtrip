from src.utils.util import *
from src.azure_services.cloud import upload_to_azure
import base64
from PIL import Image
import os


def get_response_image(image_path):
    try:
        #for converting image into base64 by resizing it to half
        image_file=Image.open(image_path)
        if image_file.mode != 'RGB':
            image_file = image_file.convert('RGB')
        
        # Resize the image to 50%.
        width, height = image_file.size
        new_size = (width//2, height//2)
        resized_image = image_file.resize(new_size)
        image_file.close()
        # Compress the image to the optimal size for webview.
        image_name = generateName(image_path.split('/')[-1],"compressed_image")
        image_name_split = image_name.split(".")
        image_name_split[-1] = ".jpg"
        image_name = "".join(image_name_split)
        # print("print path name as:::",os.path.join('static',image_name))
        resized_image.save(os.path.join('static',image_name), optimize=True, quality=50)
        # print("resize iamge:::", resized_image)
        with open(os.path.join('static',image_name), 'rb') as im:
            # Convert the image to a base64 string.
            encoded_string = base64.b64encode(im.read()).decode('utf-8')
        im.close()
        if os.path.exists(os.path.join('static',image_name)):
            os.remove(os.path.join('static',image_name))
        # Get the mimetype of the image.
        mimetype = "image/jpeg"
        return encoded_string,mimetype
    except Exception as e:
        print("Exception in get_response_image as :", str(e))



def corr_img_extn(img ,img_path ,image_name,  tempFilePaths , jsonObj):
    try:
        print("correcting image format")
        rgb_img = img.convert("RGB")
        os.remove(img_path)
        # print("image path part to change extension name: ",img_path.split('/')[-1].split(".")[-1])
        img_path = img_path.replace(img_path.split('/')[-1].split(".")[-1],"jpeg")
        tempFilePaths.append(img_path)
        # print("image_path becomes: ",img_path)
        rgb_img.save(img_path)
        img = Image.open(img_path)
        # print("image format becomes: ",img.format)
        return img
    except Exception as e:
        print("Exception in corr_img_extn as ::", str(e))
        jsonObj["requestResponse"] = "Invalid file format, current file format: "+img.format
        with open("static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json", "w") as f:
            json.dump(jsonObj, f)
        f.close()
        file_path = "static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
        file_name = image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
        upload_to_azure(file_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)
        # print("temperory stored file: ",tempFilePaths)
        deleteFiles(tempFilePaths)
        print("Invalid file format, current file format: "+img.format)
        return False
    
def img_size_check(width,height, image_name ,jsonObj , tempFilePaths):
    try:
        if width<50 or height<50 :
            jsonObj["requestResponse"] = "Image is either too small in dimension . Reupload a right document"
            with open("static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json", "w") as f:
                json.dump(jsonObj, f)
            f.close()
            file_path = "static\\"+image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
            file_name = image_name.split(".")[0]+"_"+jsonObj["Timestamp"]+".json"
            upload_to_azure(file_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
            # print("temperory stored file: ",tempFilePaths)
            deleteFiles(tempFilePaths)
            return False
        else:
            return True
    except Exception as e:
        print("Exception in img_size_check as ::", str(e))
        return False

