#file contains functions of Chromadb and clip
import clip , torch
from PIL import Image
from dotenv import load_dotenv

load_dotenv(override = True)

# <---------------clip----------------->
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
#<------------------------------------->


# Function to generate an embedding for an image
def get_embedding(img):
    try:
        query_image = preprocess(Image.fromarray(img)).unsqueeze(0).to(device)
        # Get the embedding from the CLIP model
        with torch.no_grad():
            query_embeddings = model.encode_image(query_image)
        return query_embeddings
    except Exception as e:
         print("Exception in get_embedding as: ", str(e))
         return []



