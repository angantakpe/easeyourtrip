import streamlit as st
import requests
import json
import os
import datetime
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from utils import die

# Load environment variables
load_dotenv()

# Set up the API URL
API_URL = os.getenv("API_URL", "http://localhost:5321")
# Use the development API key for local testing
DEV_API_KEY = "dev-key-123"
API_KEY = os.getenv("NURONAI_API_KEY_LOCAL", DEV_API_KEY)

st.set_page_config(
    page_title="EaseYourTrip Document AI",
    page_icon="✈️",
    layout="wide",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        text-align: center;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>EaseYourTrip Document AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Upload and analyze travel documents</p>", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Options")
endpoint = st.sidebar.selectbox(
    "Select API Endpoint",
    ["/process", "/validImage", "/extract_with_category"]
)

# Add a checkbox for bypassing the cache
bypass_cache = st.sidebar.checkbox("Bypass Cache (Force Reprocessing)", help="Enable this to skip cache lookup and force document reprocessing. Useful for testing classification improvements.")

# Add a section for viewing detailed logs
with st.sidebar.expander("Debug Options", expanded=False):
    st.write("These options help with debugging document classification")
    show_logs = st.checkbox("Show Detailed Logs", help="Display detailed logs after processing")
    log_lines = st.number_input("Number of Log Lines", min_value=10, max_value=100, value=20, help="Number of recent log lines to display")

# Main content
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("Upload Document")
uploaded_file = st.file_uploader("Choose a file (PDF, JPG, PNG)", type=["pdf", "jpg", "jpeg", "png"])
st.markdown("</div>", unsafe_allow_html=True)

# Additional options based on endpoint
if endpoint == "/validImage":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Image Processing Options")
    crop_img = st.checkbox("Crop Image", value=True)
    custom_crop = st.checkbox("Custom Crop")
    
    if custom_crop:
        col1, col2 = st.columns(2)
        with col1:
            height = st.number_input("Height", min_value=100, max_value=2000, value=500)
        with col2:
            width = st.number_input("Width", min_value=100, max_value=2000, value=500)
    else:
        height = None
        width = None
    st.markdown("</div>", unsafe_allow_html=True)

elif endpoint == "/extract_with_category":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Category Options")
    updated_cat = st.selectbox(
        "Select Document Category",
        ["passport", "id_card", "visa", "boarding_pass", "hotel_reservation", "travel_insurance"]
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Process button
process_button = st.button("Process Document")

# Display results
if uploaded_file is not None and process_button:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Processing Document...")
    
    # Progress bar for visual feedback
    progress_bar = st.progress(0)
    for i in range(100):
        # Update progress bar
        progress_bar.progress(i + 1)
    
    # Prepare the files and data for the API request
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), f"application/{uploaded_file.type.split('/')[1]}")}
    
    data = {"apikey": API_KEY}
    
    # Add bypass_cache parameter if checked
    if bypass_cache:
        data["bypass_cache"] = "True"
    
    # Add additional parameters based on the endpoint
    if endpoint == "/validImage":
        data["crop_img"] = str(crop_img)
        data["custom_Crop"] = str(custom_crop)
        if custom_crop:
            data["height"] = str(height)
            data["width"] = str(width)
    
    elif endpoint == "/extract_with_category":
        data["updated_cat"] = updated_cat
    
    try:
        # Make the API request
        response = requests.post(f"{API_URL}{endpoint}", files=files, data=data)
        
        # Check if the request was successful
        if response.status_code == 200:


            # Try to parse the response as JSON, but handle text responses as well
            try:
                result = response.json()
                die(result, exit_program=False)  # Debug output without exiting
                
                # Display the result
                st.subheader("Results")
                
                # Pretty print the JSON response
                st.json(result)
                
                # If there's an image URL in the response, display it
                if isinstance(result, dict) and "image_url" in result:
                    st.subheader("Document Image")
                    st.image(result["image_url"])
                
                # If there's face data, display it
                if isinstance(result, dict) and "face_data" in result and result["face_data"]:
                    st.subheader("Face Detection")
                    face_data = result["face_data"]
                    if isinstance(face_data, list) and len(face_data) > 0 and "face_url" in face_data[0]:
                        for face in face_data:
                            st.image(face["face_url"])
            except json.JSONDecodeError:
                # Handle plain text responses
                st.subheader("Results")
                st.error(f"API Response: {response.text}")
                st.warning("The API returned a text response instead of JSON. This might indicate an error or validation issue.")
        else:
            # Try to parse error response as JSON first, if it fails, display as text
            try:
                error_json = response.json()
                st.error(f"Error: {response.status_code}")
                st.json(error_json)
            except json.JSONDecodeError:
                # If parsing as JSON fails, display as plain text
                st.error(f"Error: {response.status_code} - {response.text}")
    
    except Exception as e:
        error_message = str(e)
        # Try to parse error message as JSON if it looks like JSON
        if error_message.strip().startswith('{') and error_message.strip().endswith('}'):
            try:
                error_json = json.loads(error_message)
                st.error("Error processing document:")
                st.json(error_json)
            except json.JSONDecodeError:
                st.error(f"Error processing document: {error_message}")
        else:
            st.error(f"Error processing document: {error_message}")
    
    # Display logs if requested
    if show_logs:
        st.subheader("Detailed Logs")
        try:
            # Get the current date for the log file
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            log_file_path = os.path.join("..", "logs", f"Log_{current_date}.log")
            
            if os.path.exists(log_file_path):
                with open(log_file_path, "r") as log_file:
                    # Read the last N lines from the log file
                    log_lines_content = log_file.readlines()[-log_lines:]
                    log_text = "".join(log_lines_content)
                    st.code(log_text)
            else:
                st.warning(f"Log file not found: {log_file_path}")
        except Exception as e:
            st.error(f"Error reading logs: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# API Information
with st.expander("API Information"):
    st.write("""
    ### API Endpoints
    
    - **/process**: General document processing and classification
    - **/validImage**: Validates and processes images, with options for cropping
    - **/extract_with_category**: Extracts information with a specified category
    
    ### Document Types Supported
    
    - Passports
    - ID Cards
    - Visas
    - Boarding Passes
    - Hotel Reservations
    - Travel Insurance Documents
    """)

# Footer
st.markdown("""
---
<p style="text-align: center;">EaseYourTrip Document AI - Powered by Azure Cognitive Services and OpenAI</p>
""", unsafe_allow_html=True)
