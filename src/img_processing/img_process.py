from src.utils.util import *
from src.azure_services.cloud import upload_to_azure
import base64
from PIL import Image
import os


def get_response_image(image_path):
    try:
        # for converting image into base64 by resizing it to half
        image_file = Image.open(image_path)
        if image_file.mode != "RGB":
            image_file = image_file.convert("RGB")

        # Resize the image to 50%.
        width, height = image_file.size
        new_size = (width // 2, height // 2)
        resized_image = image_file.resize(new_size)
        image_file.close()
        # Compress the image to the optimal size for webview.
        image_name = generateName(image_path.split("/")[-1], "compressed_image")
        image_name_split = image_name.split(".")
        image_name_split[-1] = ".jpg"
        image_name = "".join(image_name_split)
        # print("print path name as:::",os.path.join('static',image_name))
        resized_image.save(
            os.path.join("static", image_name), optimize=True, quality=50
        )
        # print("resize iamge:::", resized_image)
        with open(os.path.join("static", image_name), "rb") as im:
            # Convert the image to a base64 string.
            encoded_string = base64.b64encode(im.read()).decode("utf-8")
        im.close()
        if os.path.exists(os.path.join("static", image_name)):
            os.remove(os.path.join("static", image_name))
        # Get the mimetype of the image.
        mimetype = "image/jpeg"
        return encoded_string, mimetype
    except Exception as e:
        print("Exception in get_response_image as :", str(e))


def corr_img_extn(img, img_path, image_name, tempFilePaths, jsonObj):
    try:
        print("correcting image format")

        # Create a new path for the converted image
        # Fix the path handling to ensure consistent path separators
        img_dir = os.path.dirname(img_path)
        img_name = os.path.basename(img_path)
        base_name = os.path.splitext(img_name)[0]
        new_img_path = os.path.join(img_dir, f"{base_name}.jpeg")

        # Make a copy of the image before closing it
        try:
            #  Only convert if the image is still open
            if not getattr(img, 'closed', False):
                rgb_img = img.convert("RGB")
                rgb_img.save(new_img_path)
                rgb_img.close()

                # Close the original image after conversion
                if hasattr(img, 'close') and not getattr(img, 'closed', False):
                    img.close()
            else:
                # If image is already closed, reopen it
                print("Image was already closed, reopening")
                img = Image.open(img_path)
                rgb_img = img.convert("RGB")
                rgb_img.save(new_img_path)
                rgb_img.close()
                img.close()

            # Add the new path to tempFilePaths for cleanup later
            tempFilePaths.append(new_img_path)
            
            # Only try to delete the original file if it's different from the new file
            if img_path != new_img_path:
                try:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                except Exception as e:
                    print(f"Warning: Could not delete original file: {str(e)}")
            
            # Verify the new file exists before returning
            if os.path.exists(new_img_path):
                print(f"Successfully converted image to {new_img_path}")
                return Image.open(new_img_path)
            else:
                print(f"ERROR: Converted file {new_img_path} does not exist!")
                # If conversion failed, try to use the original image
                if os.path.exists(img_path):
                    print(f"Using original image: {img_path}")
                    return Image.open(img_path)
                else:
                    print("ERROR: Both converted and original images are missing!")
                    return None
        except Exception as e:
            print(f"Exception during image conversion: {str(e)}")
            # If conversion fails, try to use the original image
            if os.path.exists(img_path):
                print(f"Using original image: {img_path}")
                return Image.open(img_path)
            else:
                print("ERROR: Original image is missing after conversion error!")
                return None
    except Exception as e:
        print("Exception in corr_img_extn as ::", str(e))
        jsonObj["requestResponse"] = (
            "Invalid file format, current file format: " + img.format
        )
        with open(
            "static\\"
            + image_name.split(".")[0]
            + "_"
            + jsonObj["Timestamp"]
            + ".json",
            "w",
        ) as f:
            json.dump(jsonObj, f)
        f.close()
        file_path = (
            "static\\" + image_name.split(".")[0] + "_" + jsonObj["Timestamp"] + ".json"
        )
        file_name = image_name.split(".")[0] + "_" + jsonObj["Timestamp"] + ".json"
        upload_to_azure(file_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)
        # print("temperory stored file: ",tempFilePaths)
        deleteFiles(tempFilePaths)
        print("Invalid file format, current file format: " + img.format)
        return False


def img_size_check(width, height, image_name, jsonObj, tempFilePaths):
    try:
        if width < 50 or height < 50:
            jsonObj["requestResponse"] = (
                "Image is either too small in dimension . Reupload a right document"
            )
            with open(
                "static\\"
                + image_name.split(".")[0]
                + "_"
                + jsonObj["Timestamp"]
                + ".json",
                "w",
            ) as f:
                json.dump(jsonObj, f)
            f.close()
            file_path = (
                "static\\"
                + image_name.split(".")[0]
                + "_"
                + jsonObj["Timestamp"]
                + ".json"
            )
            file_name = image_name.split(".")[0] + "_" + jsonObj["Timestamp"] + ".json"
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
