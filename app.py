# import streamlit as st
# import json
# from parser.pdf_extractor import extract_text_from_pdf
# from parser.llm_parser import extract_resume_data
# from parser.llm_parser import current_month

# st.set_page_config(page_title="THE CV", page_icon="📄", layout="centered")
# st.title("📄 THE CV ")

# uploaded_file = st.file_uploader("Upload a Resume", type=["pdf"])

# if uploaded_file:
#     with st.spinner("Extracting text from resume..."):
#         extracted_text = extract_text_from_pdf(uploaded_file)
    
#     # st.text_area("📄 Extracted Resume Text", extracted_text[:1000] + "...", height=200)
#     # st.text_area("current month is: ", {current_month})
#     if st.button("🔍 Parsing Details"):
#         with st.spinner("Generating response..."):
#             response = extract_resume_data(extracted_text)

#             # Clean the response (remove triple backticks and possible code block labels)
#             cleaned_response = response.strip().strip("```json").strip("```").strip()

#             try:
#                 parsed_json = json.loads(cleaned_response)
#                 st.success("✅ Resume Parsed Successfully!")
#                 # st.text_area("le bhai", response, height=340)
#                 st.json(parsed_json)
#             except Exception as e:
#                 st.error("❌ Failed to parse JSON from Gemini. Here's the raw output:")
#                 st.text_area("Raw Gemini Output", response, height=300)
#                 st.exception(e)
            
#             # try:
#             #     parsed_json = json.loads(response)
#             #     st.success("✅ Resume Parsed Successfully!")
#             #     st.text_area("le bhai",response, height = 340)
#             #     st.json(parsed_json)
#             # except:
#             #     st.error("❌ Failed to parse JSON from Gemini. Here's the raw output:")
#             #     st.text_area("Raw Gemini Output", response, height=300)
# app.py - Fixed version for Streamlit Cloud



import streamlit as st
import json
import time
import threading
import queue
from parser.pdf_extractor import extract_text_from_pdf
from parser.llm_parser import extract_resume_data
from parser.llm_parser import current_month

# Configure page
st.set_page_config(
    page_title="THE CV", 
    page_icon="📄", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Add custom CSS for better UX
st.markdown("""
<style>
    .stProgress .st-bo {
        background-color: #00ff00;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)

st.title("📄 THE CV Parser")
st.markdown("Upload your resume and get structured data extracted using AI")

# Add file size warning
st.info("💡 **Tip**: For best performance on Streamlit Cloud, keep your PDF under 2MB")

uploaded_file = st.file_uploader(
    "Upload a Resume", 
    type=["pdf"],
    help="Supported format: PDF files (Max 5MB recommended for Streamlit Cloud)"
)

def process_resume_with_timeout(file, timeout_seconds=25):
    """Process resume with timeout handling"""
    
    # Create a queue to get results from thread
    result_queue = queue.Queue()
    error_queue = queue.Queue()
    
    def process_resume():
        try:
            # Step 1: Extract text
            extracted_text = extract_text_from_pdf(file)
            
            # Step 2: Parse with LLM
            response = extract_resume_data(extracted_text)
            
            result_queue.put(response)
            
        except Exception as e:
            error_queue.put(str(e))
    
    # Start processing in a separate thread
    thread = threading.Thread(target=process_resume)
    thread.start()
    
    # Wait for completion with timeout
    thread.join(timeout=timeout_seconds)
    
    if thread.is_alive():
        return None, "TIMEOUT"
    
    # Check for errors
    if not error_queue.empty():
        error = error_queue.get()
        return None, f"ERROR: {error}"
    
    # Get result
    if not result_queue.empty():
        result = result_queue.get()
        return result, "SUCCESS"
    
    return None, "NO_RESULT"

def display_processing_status():
    """Display processing status with progress bar"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simulate progress updates
    steps = [
        (20, "📄 Extracting text from PDF..."),
        (40, "🔍 Preparing AI analysis..."),
        (60, "🤖 AI is parsing your resume..."),
        (80, "📊 Structuring data..."),
        (95, "✨ Almost done...")
    ]
    
    for progress, message in steps:
        status_text.text(message)
        progress_bar.progress(progress)
        time.sleep(0.5)
    
    return progress_bar, status_text

if uploaded_file:
    # Check file size
    file_size = len(uploaded_file.getvalue())
    file_size_mb = file_size / (1024 * 1024)
    
    st.success(f"📁 File uploaded: {uploaded_file.name} ({file_size_mb:.1f} MB)")
    
    if file_size_mb > 5:
        st.warning("⚠️ Large file detected. Processing may take longer or timeout on Streamlit Cloud.")
    
    if st.button("🔍 Parse Resume", type="primary"):
        
        # Show timeout warning
        with st.expander("⏰ Processing Information", expanded=True):
            st.info("""
            📋 **What to expect:**
            - Processing time: 15-25 seconds
            - Please don't refresh the page
            - If timeout occurs, try a smaller PDF file
            """)
        
        # Create containers for progress and results
        progress_container = st.container()
        result_container = st.container()
        
        with progress_container:
            # Start processing with progress indication
            progress_bar, status_text = display_processing_status()
            
            # Process with timeout
            start_time = time.time()
            response, status = process_resume_with_timeout(uploaded_file, timeout_seconds=25)
            processing_time = time.time() - start_time
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
        
        with result_container:
            if status == "SUCCESS" and response:
                st.success(f"✅ Resume parsed successfully in {processing_time:.1f} seconds!")
                
                # Clean and parse the response
                cleaned_response = response.strip().strip("```json").strip("```").strip()
                
                try:
                    parsed_json = json.loads(cleaned_response)
                    
                    # Display results in an organized way
                    st.markdown("### 📊 Parsed Resume Data")
                    
                    # Create tabs for better organization
                    tab1, tab2, tab3 = st.tabs(["📋 Structured View", "🔧 JSON Data", "📥 Download"])
                    
                    with tab1:
                        # Display structured data
                        if 'personalInfo' in parsed_json:
                            st.markdown("#### 👤 Personal Information")
                            col1, col2 = st.columns(2)
                            with col1:
                                if parsed_json['personalInfo'].get('name'):
                                    st.write(f"**Name:** {parsed_json['personalInfo']['name']}")
                                if parsed_json['personalInfo'].get('email'):
                                    st.write(f"**Email:** {parsed_json['personalInfo']['email']}")
                            with col2:
                                if parsed_json['personalInfo'].get('phone'):
                                    st.write(f"**Phone:** {parsed_json['personalInfo']['phone']}")
                                if parsed_json['personalInfo'].get('address'):
                                    st.write(f"**Address:** {parsed_json['personalInfo']['address']}")
                        
                        if 'experience' in parsed_json and parsed_json['experience']:
                            st.markdown("#### 💼 Work Experience")
                            for exp in parsed_json['experience']:
                                with st.expander(f"{exp.get('position', 'Position')} at {exp.get('company', 'Company')}"):
                                    st.write(f"**Duration:** {exp.get('duration', 'N/A')}")
                                    if exp.get('durationCalculated'):
                                        st.write(f"**Total Time:** {exp['durationCalculated']}")
                                    if exp.get('location'):
                                        st.write(f"**Location:** {exp['location']}")
                                    if exp.get('description'):
                                        st.write(f"**Description:** {exp['description']}")
                        
                        if 'skills' in parsed_json and parsed_json['skills']:
                            st.markdown("#### 🔧 Skills")
                            skills_cols = st.columns(3)
                            for i, skill in enumerate(parsed_json['skills']):
                                with skills_cols[i % 3]:
                                    st.write(f"• {skill}")
                    
                    with tab2:
                        st.json(parsed_json)
                    
                    with tab3:
                        # Download options
                        json_string = json.dumps(parsed_json, indent=2)
                        st.download_button(
                            label="📥 Download JSON",
                            data=json_string,
                            file_name=f"{uploaded_file.name.replace('.pdf', '')}_parsed.json",
                            mime="application/json"
                        )
                        
                        # Also provide CSV option for basic data
                        if 'personalInfo' in parsed_json:
                            csv_data = f"Name,Email,Phone,Address\n"
                            csv_data += f"{parsed_json['personalInfo'].get('name', '')},{parsed_json['personalInfo'].get('email', '')},{parsed_json['personalInfo'].get('phone', '')},{parsed_json['personalInfo'].get('address', '')}"
                            
                            st.download_button(
                                label="📊 Download CSV (Basic Info)",
                                data=csv_data,
                                file_name=f"{uploaded_file.name.replace('.pdf', '')}_basic.csv",
                                mime="text/csv"
                            )
                
                except json.JSONDecodeError as e:
                    st.error("❌ Failed to parse JSON from AI response")
                    
                    with st.expander("🔍 Debug Information", expanded=False):
                        st.text_area("Raw AI Response", response, height=200)
                        st.write(f"JSON Error: {str(e)}")
                    
                    st.info("💡 Try uploading the file again or use a different PDF")
            
            elif status == "TIMEOUT":
                st.error("⏰ Processing timeout!")
                st.markdown("""
                **Suggestions to fix timeout:**
                1. 📄 Try a smaller PDF file (< 2MB)
                2. 🔄 Refresh and try again
                3. ✂️ Use a shorter resume (1-2 pages)
                4. 📱 Try during off-peak hours
                """)
                
                # Offer alternative processing
                if st.button("🔄 Try Quick Processing"):
                    st.info("Attempting quick processing with reduced analysis...")
                    # This could trigger a simpler parsing approach
            
            elif status.startswith("ERROR"):
                st.error(f"❌ Processing failed: {status}")
                
                if "API" in status:
                    st.info("🔑 This might be an API key issue. Please contact support.")
                else:
                    st.info("💡 Try uploading a different PDF file or try again later.")
            
            else:
                st.error("❌ Unknown error occurred during processing")

# Add footer with tips
st.markdown("---")
st.markdown("""
**💡 Tips for better results:**
- Use clear, well-formatted PDFs
- Ensure text is selectable (not scanned images)
- Keep resume under 2MB for optimal performance
- Standard resume formats work best
""")

# Add system status check
if st.sidebar.button("🔍 Check System Status"):
    with st.sidebar:
        st.write("**System Status:**")
        try:
            from parser.llm_parser import genai
            # Quick API test
            model = genai.GenerativeModel(model_name="gemini-2.0-flash")
            test_response = model.generate_content(["Hello"])
            st.success("✅ AI Service: Online")
        except Exception as e:
            st.error(f"❌ AI Service: {str(e)[:50]}...")
        
        st.write(f"**Current Month:** {current_month}")
        st.write("**File Upload:** ✅ Ready")