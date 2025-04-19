import streamlit as st
import json
from main import process_with_gemini, text_to_speech, translate_tamil_to_english
import google.generativeai as genai

# Configure Gemini
gemini_api_key = "xxx"
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-pro')

def parse_medical_report(text):
    """Parse medical report text into a list of key-value pairs"""
    try:
        # Try to parse as JSON first
        return json.loads(text)
    except json.JSONDecodeError:
        # If not JSON, parse as text
        lines = text.strip().split('\n')
        report = []
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                report.append({
                    'test': key.strip(),
                    'value': value.strip()
                })
        return report

st.title("Medical Report Analysis System")

# Input section
st.header("Input Medical Report")
report_input = st.text_area("Enter medical report (JSON or text format):", height=200)

# Process button
if st.button("Process Report"):
    if report_input:
        try:
            # Parse the report
            medical_report = parse_medical_report(report_input)
            
            # Display parsed report
            st.subheader("Parsed Medical Report")
            st.json(medical_report)
            
            # Input question
            question = st.text_input("Ask a question about the report (in Tamil):")
            
            if question:
                # Translate question to English
                english_question = translate_tamil_to_english(question)
                
                # Process with Gemini
                response = process_with_gemini(english_question, medical_report)
                
                # Display response
                st.subheader("Response")
                st.write(response)
                
                # Play audio
                if st.button("Play Response"):
                    text_to_speech(response)
        except Exception as e:
            st.error(f"Error processing report: {str(e)}")
    else:
        st.warning("Please enter a medical report") 