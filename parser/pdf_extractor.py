# import fitz 

# def extract_text_from_pdf(file):
#     doc = fitz.open(stream=file.read(), filetype="pdf")
#     text = ""
#     for page in doc:
#         text += page.get_text()
#     return text.strip()


# parser/pdf_extractor.py - Fixed version with better error handling
import fitz 
import streamlit as st

def extract_text_from_pdf(file):
    """Extract text from PDF with error handling and optimization"""
    try:
        # Reset file pointer to beginning
        file.seek(0)
        
        # Open PDF document
        doc = fitz.open(stream=file.read(), filetype="pdf")
        
        text = ""
        page_count = len(doc)
        
        # Limit pages for Streamlit Cloud performance
        max_pages = 10  # Process maximum 10 pages to prevent timeout
        
        if page_count > max_pages:
            st.info(f"📄 Large PDF detected ({page_count} pages). Processing first {max_pages} pages for optimal performance.")
        
        pages_to_process = min(page_count, max_pages)
        
        for page_num in range(pages_to_process):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                
                # Filter out empty or very short pages
                if len(page_text.strip()) > 10:
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page_text
                    
            except Exception as e:
                st.warning(f"⚠️ Could not extract text from page {page_num + 1}: {str(e)}")
                continue
        
        # Close document to free memory
        doc.close()
        
        # Clean up the extracted text
        cleaned_text = clean_extracted_text(text)
        
        if not cleaned_text.strip():
            raise Exception("No readable text found in PDF")
        
        return cleaned_text
        
    except Exception as e:
        error_msg = str(e)
        
        if "password" in error_msg.lower():
            st.error("🔒 This PDF is password-protected. Please upload an unlocked PDF.")
        elif "corrupted" in error_msg.lower() or "damaged" in error_msg.lower():
            st.error("📄 This PDF appears to be corrupted. Please try a different file.")
        elif "no readable text" in error_msg.lower():
            st.error("📄 This PDF doesn't contain readable text (might be scanned images). Please use OCR or a different PDF.")
        else:
            st.error(f"❌ Error extracting text from PDF: {error_msg}")
        
        # Return empty string instead of raising exception
        return ""

def clean_extracted_text(text):
    """Clean and optimize extracted text"""
    if not text:
        return ""
    
    # Remove excessive whitespace and normalize line breaks
    lines = []
    for line in text.split('\n'):
        cleaned_line = line.strip()
        if cleaned_line:
            lines.append(cleaned_line)
    
    # Join lines with single newlines
    cleaned_text = '\n'.join(lines)
    
    # Remove page markers
    cleaned_text = cleaned_text.replace('--- Page ', '\n--- Page ')
    
    # Limit total text length for Streamlit Cloud
    max_length = 8000  # 8KB limit for processing
    if len(cleaned_text) > max_length:
        st.info(f"📄 Large resume detected ({len(cleaned_text)} chars). Truncating to {max_length} characters for optimal processing.")
        cleaned_text = cleaned_text[:max_length] + "\n...[Content truncated for processing]"
    
    return cleaned_text

def validate_pdf_file(file):
    """Validate PDF file before processing"""
    if not file:
        return False, "No file provided"
    
    # Check file size (5MB limit for Streamlit Cloud)
    file_size = len(file.getvalue())
    max_size = 5 * 1024 * 1024  # 5MB
    
    if file_size > max_size:
        return False, f"File too large ({file_size / (1024*1024):.1f} MB). Please use a file smaller than 5MB."
    
    # Check if it's actually a PDF
    try:
        file.seek(0)
        header = file.read(4)
        file.seek(0)
        
        if header != b'%PDF':
            return False, "File doesn't appear to be a valid PDF"
        
        return True, "Valid PDF file"
        
    except Exception as e:
        return False, f"Error validating file: {str(e)}"

# Additional utility function for text preview
def get_text_preview(text, max_chars=500):
    """Get a preview of extracted text"""
    if not text:
        return "No text extracted"
    
    if len(text) <= max_chars:
        return text
    
    return text[:max_chars] + "..."