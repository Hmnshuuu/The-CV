import os
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

now = datetime.now()
current_month = now.month
current_month = datetime.now().strftime("%B %Y")  # Example: "May 2025"


PROMPT_TEMPLATE = """
You are an expert resume parser. Extract the following information from the resume text and return ONLY a valid JSON object with no additional text or markdown formatting.

Extract these fields:
{{
  "personalInfo": {{
    "name": "full name (required)",
    "email": "email address",
    "phone": "phone number", 
    "address": "full address"
  }},
  "education": [
    {{
      "degree": "degree name",
      "institution": "university/college name",
      "year": "graduation year or duration (e.g., 2020-2024)",
      "location": "city, country",
      "gpa": "GPA if mentioned"
    }}
  ],
  "experience": [
    {{
      "position": "job title",
      "company": "company name",
      "duration": "start date - end date (e.g., Jan 2022 - Present)",
      "durationCalculated": "calculated time (e.g., 2 years 3 months)",
      "location": "city, country",
      "description": "brief job description or key achievements"
    }}
  ],
  "skills": ["skill1", "skill2", "skill3"],
  "certifications": [
    {{
      "name": "certification name",
      "issuer": "issuing organization",
      "year": "year obtained",
      "expiryYear": "expiry year if applicable"
    }}
  ]
}}

Instructions:
1. Extract information accurately from the resume text
2. If information is not available, use null or empty array
3. If anyone write present as end date, consider {current_month} as end date and in this case add 1 in duration
4. For duration calculation, convert to human readable format (e.g., "2 years 3 months") via formula = end date - start date and here consider only years and months (for example end date is may 2025 and start date is aug 2024 so the experience duration is may 2025- aug 2024 which is 11 months with including both start end end date)
5. Group similar skills together (react js and react native are in frontend)
6. Return only the proper format, no explanations
7. Add skills which are only mentioned in skills section, dont take from projects section or any other section
8. Provide proper formats with bold section characters and light for normal text


Resume text:
\"\"\"
{resume_text}
\"\"\"
"""

def extract_resume_data(text):
    # prompt = PROMPT_TEMPLATE.format(resume_text=text)
    prompt = PROMPT_TEMPLATE.format(resume_text=text, current_month=current_month)

    # model = genai.GenerativeModel("gemini-pro")
    # response = model.generate_content(prompt)
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    response = model.generate_content([prompt])  # notice: [prompt] is a list

    return response.text
