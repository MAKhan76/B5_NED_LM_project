import streamlit as st
import requests
import os

def send_file_to_api(file):
    # URL of your FastAPI endpoint
    url = 'http://localhost:8000/extract/{path_to_file}'
    
    # Temporary save file to disk to mimic file handling
    with open(file.name, "wb") as f:
        f.write(file.getbuffer())
    
    # Full path to the saved file
    full_path = os.path.abspath(file.name)

    # Update the URL with the actual file path
    full_url = url.format(path_to_file=full_path)

    # Make the GET request to FastAPI
    response = requests.get(full_url)

    # Remove the file after sending it to the API
    os.remove(full_path)
    
    return response.json()

st.title('PDF Data Extractor')

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
if uploaded_file is not None:
    if st.button('Extract Data'):
        result = send_file_to_api(uploaded_file)
        st.write(result)
else:
    st.write("Upload a PDF file to extract data.")
