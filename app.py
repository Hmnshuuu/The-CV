import streamlit as st
import json
from parser.pdf_extractor import extract_text_from_pdf
from parser.llm_parser import extract_resume_data
from parser.llm_parser import current_month

st.set_page_config(page_title="THE CV", page_icon="📄", layout="centered")
st.title("📄 THE CV ")

uploaded_file = st.file_uploader("Upload a Resume", type=["pdf"])

if uploaded_file:
    with st.spinner("Extracting text from resume..."):
        extracted_text = extract_text_from_pdf(uploaded_file)
    
    # st.text_area("📄 Extracted Resume Text", extracted_text[:1000] + "...", height=200)
    # st.text_area("current month is: ", {current_month})
    if st.button("🔍 Parsing Details"):
        with st.spinner("Generating response..."):
            response = extract_resume_data(extracted_text)

            # Clean the response (remove triple backticks and possible code block labels)
            cleaned_response = response.strip().strip("```json").strip("```").strip()

            try:
                parsed_json = json.loads(cleaned_response)
                st.success("✅ Resume Parsed Successfully!")
                # st.text_area("le bhai", response, height=340)
                st.json(parsed_json)
            except Exception as e:
                st.error("❌ Failed to parse JSON from Gemini. Here's the raw output:")
                st.text_area("Raw Gemini Output", response, height=300)
                st.exception(e)
            
            # try:
            #     parsed_json = json.loads(response)
            #     st.success("✅ Resume Parsed Successfully!")
            #     st.text_area("le bhai",response, height = 340)
            #     st.json(parsed_json)
            # except:
            #     st.error("❌ Failed to parse JSON from Gemini. Here's the raw output:")
            #     st.text_area("Raw Gemini Output", response, height=300)
