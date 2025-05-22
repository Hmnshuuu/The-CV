# import os
# from datetime import datetime
# from dotenv import load_dotenv
# import google.generativeai as genai

# load_dotenv()
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# now = datetime.now()
# current_month = now.month
# current_month = datetime.now().strftime("%B %Y")  # Example: "May 2025"


# PROMPT_TEMPLATE = """
# You are an expert resume parser. Extract the following information from the resume text and return ONLY a valid JSON object with no additional text or markdown formatting.

# Extract these fields:
# {{
#   "personalInfo": {{
#     "name": "full name (required)",
#     "email": "email address",
#     "phone": "phone number", 
#     "address": "full address"
#   }},
#   "education": [
#     {{
#       "degree": "degree name",
#       "institution": "university/college name",
#       "year": "graduation year or duration (e.g., 2020-2024)",
#       "location": "city, country",
#       "gpa": "GPA if mentioned"
#     }}
#   ],
#   "experience": [
#     {{
#       "position": "job title",
#       "company": "company name",
#       "duration": "start date - end date (e.g., Jan 2022 - Present)",
#       "durationCalculated": "calculated time (e.g., 2 years 3 months)",
#       "location": "city, country",
#       "description": "brief job description or key achievements"
#     }}
#   ],
#   "skills": ["skill1", "skill2", "skill3"],
#   "certifications": [
#     {{
#       "name": "certification name",
#       "issuer": "issuing organization",
#       "year": "year obtained",
#       "expiryYear": "expiry year if applicable"
#     }}
#   ]
# }}

# Instructions:
# 1. Extract information accurately from the resume text
# 2. If information is not available, use null or empty array
# 3. If anyone write present as end date, consider {current_month} as end date and in this case add 1 in duration
# 4. For duration calculation, convert to human readable format (e.g., "2 years 3 months") via formula = end date - start date and here consider only years and months (for example end date is may 2025 and start date is aug 2024 so the experience duration is may 2025- aug 2024 which is 11 months with including both start end end date)
# 5. Group similar skills together (react js and react native are in frontend)
# 6. Return only the proper format, no explanations
# 7. Add skills which are only mentioned in skills section, dont take from projects section or any other section
# 8. Provide proper formats with bold section characters and light for normal text


# Resume text:
# \"\"\"
# {resume_text}
# \"\"\"
# """

# def extract_resume_data(text):
#     # prompt = PROMPT_TEMPLATE.format(resume_text=text)
#     prompt = PROMPT_TEMPLATE.format(resume_text=text, current_month=current_month)

#     # model = genai.GenerativeModel("gemini-pro")
#     # response = model.generate_content(prompt)
#     model = genai.GenerativeModel(model_name="gemini-2.0-flash")
#     response = model.generate_content([prompt])  # notice: [prompt] is a list

#     return response.text

# parser/llm_parser.py - Fixed version with timeout handling
import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import time

load_dotenv()

# Configure Gemini API
def configure_gemini():
    """Configure Gemini with proper error handling"""
    try:
        # Try to get API key from Streamlit secrets first, then from environment
        if hasattr(st, 'secrets') and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        else:
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in secrets or environment variables")
        
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Failed to configure Gemini API: {str(e)}")
        return False

# Initialize date
now = datetime.now()
current_month = now.strftime("%B %Y")  # Example: "May 2025"

# Optimized prompt template - shorter and more focused
PROMPT_TEMPLATE = """
Extract resume information in JSON format. Be precise and return ONLY valid JSON:

{{
  "personalInfo": {{
    "name": "full name",
    "email": "email address",
    "phone": "phone number", 
    "address": "address"
  }},
  "education": [
    {{
      "degree": "degree name",
      "institution": "institution name",
      "year": "year/duration",
      "location": "location"
    }}
  ],
  "experience": [
    {{
      "position": "job title",
      "company": "company name",
      "duration": "start - end date",
      "durationCalculated": "calculated duration",
      "location": "location",
      "description": "brief description"
    }}
  ],
  "skills": ["skill1", "skill2"],
  "certifications": [
    {{
      "name": "cert name",
      "issuer": "issuer",
      "year": "year"
    }}
  ]
}}

Rules:
1. If "Present" mentioned, use {current_month} as end date
2. Calculate duration in "X years Y months" format
3. Extract skills ONLY from skills section
4. Use null for missing data
5. Return ONLY JSON, no markdown

Resume:
{resume_text}
"""

def extract_resume_data(text, max_retries=3):
    """Extract resume data with timeout and retry logic"""
    
    if not configure_gemini():
        return '{"error": "API configuration failed"}'
    
    # Truncate text if too long to prevent timeout
    max_text_length = 4000
    if len(text) > max_text_length:
        text = text[:max_text_length] + "\n... (truncated for processing)"
        st.info("📄 Large resume detected. Using optimized processing.")
    
    prompt = PROMPT_TEMPLATE.format(resume_text=text, current_month=current_month)
    
    for attempt in range(max_retries):
        try:
            # Configure model with timeout settings
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Generate content with optimized settings
            response = model.generate_content(
                [prompt],
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 20,
                    "max_output_tokens": 2048,  # Limit response size
                    "stop_sequences": [],
                }
            )
            
            if response.text:
                return response.text
            else:
                raise Exception("Empty response from Gemini")
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Handle specific error types
            if "quota" in error_msg or "limit" in error_msg:
                st.error("🔑 API quota exceeded. Please try again later.")
                return '{"error": "API quota exceeded"}'
            
            elif "timeout" in error_msg or "deadline" in error_msg:
                if attempt < max_retries - 1:
                    st.warning(f"⏳ Timeout on attempt {attempt + 1}, retrying...")
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    st.error("⏰ Multiple timeouts. Please try a shorter resume.")
                    return '{"error": "Processing timeout"}'
            
            elif "safety" in error_msg:
                st.warning("⚠️ Content safety filter triggered. Using fallback extraction.")
                return extract_resume_data_fallback(text)
            
            else:
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ Attempt {attempt + 1} failed: {str(e)[:100]}... Retrying...")
                    time.sleep(1)
                    continue
                else:
                    st.error(f"❌ All attempts failed. Error: {str(e)[:100]}...")
                    return extract_resume_data_fallback(text)
    
    return '{"error": "Max retries exceeded"}'

def extract_resume_data_fallback(text):
    """Fallback extraction using simple regex patterns"""
    import re
    
    st.info("🔄 Using fallback extraction method...")
    
    # Simple regex patterns
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
    
    # Extract basic information
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    
    # Extract name (first non-empty line, basic heuristic)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    name = lines[0] if lines else "Could not extract"
    
    # Extract skills using keyword matching
    common_skills = [
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
        'sql', 'mysql', 'postgresql', 'mongodb', 'aws', 'azure', 'docker',
        'kubernetes', 'git', 'html', 'css', 'php', 'c++', 'c#', '.net'
    ]
    
    found_skills = []
    text_lower = text.lower()
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    # Basic education extraction
    education_keywords = ['university', 'college', 'bachelor', 'master', 'phd', 'degree']
    education_lines = []
    for line in lines:
        if any(keyword in line.lower() for keyword in education_keywords):
            education_lines.append(line)
    
    # Create fallback JSON
    fallback_data = {
        "personalInfo": {
            "name": name,
            "email": emails[0] if emails else None,
            "phone": phones[0] if phones else None,
            "address": None
        },
        "education": [
            {
                "degree": edu_line,
                "institution": "Could not extract",
                "year": "Could not extract",
                "location": None
            } for edu_line in education_lines[:2]  # Limit to 2 entries
        ],
        "experience": [
            {
                "position": "Could not extract details",
                "company": "Please check original resume",
                "duration": "Unknown",
                "durationCalculated": "Unknown",
                "location": None,
                "description": "Fallback extraction used"
            }
        ],
        "skills": found_skills[:10],  # Limit to 10 skills
        "certifications": [],
        "note": "Fallback extraction used due to processing limitations"
    }
    
    return json.dumps(fallback_data, indent=2)

# Quick API test function
def test_gemini_connection():
    """Test Gemini API connection"""
    try:
        if not configure_gemini():
            return False
        
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(
            ["Hello"],
            generation_config={"max_output_tokens": 10}
        )
        return response.text is not None
    except:
        return False

# Import json for fallback function
import json