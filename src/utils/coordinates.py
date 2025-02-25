import math , re
from datetime import datetime
import copy


def get_coordinates(data2, words_loc):
    try:
        values_cord = {}
        response = {}

        # Handle special character replacements in words_loc keys
        words_loc = {re.sub(r"[,]", " ", key): value for key, value in words_loc.items()}
        words_loc = {re.sub(r"[-/]", "#", key): value for key, value in words_loc.items()}

        dates = ['dob', 'date', 'Date']
        data = copy.deepcopy(data2)

        # Format dates in the data based on words_loc coordinates
        for d in dates:
            for key in data.keys():
                if d in key:
                    try:
                        date_val = datetime.strptime(data[key], "%d/%m/%Y")
                        formatted_date = date_val.strftime("%d %b %Y")
                        if all(part.upper() in words_loc for part in formatted_date.split()):
                            data[key] = formatted_date
                    except Exception as e:
                        print("exception in date in get_coordinates:", str(e))

        # Helper function to extract coordinates for a given value
        def get_value_coordinates(value):
            xmin = math.inf
            xmax = -math.inf
            ymin = math.inf
            ymax = -math.inf

            # If the value is a string, split it into words and look for coordinates
            if isinstance(value, str):
                for val in value.split():
                    for word in words_loc.keys():
                        val = re.sub(r"[,]", " ", val).upper()
                        val = re.sub(r"[-/]", "#", val).upper()
                        if len(val) < 4:  # Short words
                            if val == word:
                                if len(words_loc[word]) > 0:

                                    xmin = int(min(words_loc[word][0][0],words_loc[word][0][2],words_loc[word][0][4],words_loc[word][0][6], xmin))
                                    xmax = int(max(words_loc[word][0][0],words_loc[word][0][2],words_loc[word][0][4],words_loc[word][0][6], xmax))
                                    ymin = int(min(words_loc[word][0][1],words_loc[word][0][3],words_loc[word][0][5],words_loc[word][0][7], ymin))
                                    ymax = int(max(words_loc[word][0][1],words_loc[word][0][3],words_loc[word][0][5],words_loc[word][0][7], ymax))
                                    words_loc[word].pop(0)
                                    break
                        else:
                            if val in word:
                                if len(words_loc[word]) > 0:    
                                    xmin = int(min(words_loc[word][0][0],words_loc[word][0][2],words_loc[word][0][4],words_loc[word][0][6], xmin))
                                    xmax = int(max(words_loc[word][0][0],words_loc[word][0][2],words_loc[word][0][4],words_loc[word][0][6], xmax))
                                    ymin = int(min(words_loc[word][0][1],words_loc[word][0][3],words_loc[word][0][5],words_loc[word][0][7], ymin))
                                    ymax = int(max(words_loc[word][0][1],words_loc[word][0][3],words_loc[word][0][5],words_loc[word][0][7], ymax))
                                    words_loc[word].pop(0)
                                    break

            # Return coordinates
            if xmin == math.inf: xmin = None
            if xmax == -math.inf: xmax = None
            if ymin == math.inf: ymin = None
            if ymax == -math.inf: ymax = None
            return [xmin, ymin, xmax, ymax]

        # Traverse through data to extract coordinates
        for key, values in data.items():
            if isinstance(values, dict):
                response[key] = {}
                for sub_key, sub_value in values.items():
                    if sub_key in ['passenger', 'journey_details']:
                        if isinstance(sub_value, dict):
                            response[key][sub_key] = {sub_key2: get_value_coordinates(sub_value[sub_key2]) for sub_key2 in sub_value}
                        elif isinstance(sub_value, list):
                            response[key][sub_key] = [get_value_coordinates(item) for item in sub_value]
                    else:
                        response[key][sub_key] = get_value_coordinates(sub_value)

            elif isinstance(values, list):
                response[key] = [get_value_coordinates(item) for item in values]
            else:
                response[key] = get_value_coordinates(values)

        return response
    except Exception as e:
        print(f"Exception occurred in get_coordinates: {str(e)}")
        return {}



def adjust_coordinates_after_crop(word_locations, crop_x, crop_y):
    """
    Adjust coordinates for word locations on a cropped image.

    Parameters:
    - word_locations (dict): A dictionary where keys are words and values are lists of coordinates,
                              each in the format [[x1, y1, x2, y2, ...]].
    - crop_x (int): The x-coordinate of the top-left corner of the crop box.
    - crop_y (int): The y-coordinate of the top-left corner of the crop box.

    Returns:
    - adjusted_locations (dict): A dictionary with adjusted coordinates.
    """
    try:
        adjusted_locations = {}

        for word, coords_list in word_locations.items():
            adjusted_coords = []
            for coords in coords_list:
                adjusted_set = []
                for i in range(0, len(coords), 2):  # Iterate over pairs (x, y)
                    x = coords[i]
                    y = coords[i + 1]
                    # Adjust coordinates by subtracting the crop's top-left corner
                    adjusted_x = x - crop_x
                    adjusted_y = y - crop_y
                    adjusted_set.extend((int(adjusted_x), int(adjusted_y)))
                adjusted_coords.append(adjusted_set)
            adjusted_locations[word] = adjusted_coords

        return adjusted_locations

    except Exception as e:
        print("Exception in adjust_coordinates_after_crop as e:", str(e))
        return word_locations
        



