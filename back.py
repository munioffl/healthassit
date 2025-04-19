from elevenlabs.client import ElevenLabs
import os
import speech_recognition as sr
from translate import Translator
import google.generativeai as genai
import streamlit as st
import PyPDF2
import io
import json

# Get API keys from environment variables
api_key = os.getenv('ELEVENLABS_API_KEY')
gemini_api_key = "xxx"

if not api_key:
    raise ValueError("Please set the ELEVENLABS_API_KEY environment variable")
if not gemini_api_key:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

# Initialize ElevenLabs client
client = ElevenLabs(api_key=api_key)

# Configure Gemini
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-pro')

def listen_tamil():
    """Listen to Tamil speech and convert to text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for Tamil speech...")
        audio = recognizer.listen(source)
    
    try:
        # Using Google's speech recognition with Tamil language
        tamil_text = recognizer.recognize_google(audio, language='ta-IN')
        print(f"Recognized Tamil text: {tamil_text}")
        return tamil_text
    except sr.UnknownValueError:
        print("Could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return None

def translate_tamil_to_english(tamil_text):
    """Translate Tamil text to English while preserving numbers"""
    # Extract numbers from the text
    import re
    numbers = re.findall(r'\d+\.?\d*', tamil_text)
    
    # Replace numbers with placeholders
    for i, num in enumerate(numbers):
        tamil_text = tamil_text.replace(num, f'__NUM_{i}__')
    
    # Split text into chunks of 400 characters (leaving room for placeholders)
    chunk_size = 400
    chunks = [tamil_text[i:i+chunk_size] for i in range(0, len(tamil_text), chunk_size)]
    
    # Translate each chunk
    translator = Translator(to_lang="en", from_lang="ta")
    translated_chunks = []
    for chunk in chunks:
        try:
            # Clean up the chunk before translation
            chunk = chunk.strip()
            if not chunk:
                continue
                
            translation = translator.translate(chunk)
            # Clean up the translation
            translation = translation.strip()
            translated_chunks.append(translation)
        except Exception as e:
            print(f"Translation error: {e}")
            translated_chunks.append(chunk)  # Keep original if translation fails
    
    # Join translated chunks with proper spacing
    translation = ' '.join(filter(None, translated_chunks))
    
    # Restore numbers
    for i, num in enumerate(numbers):
        translation = translation.replace(f'__NUM_{i}__', num)
    
    # Clean up any double spaces
    translation = re.sub(r'\s+', ' ', translation)
    
    return translation.strip()

def translate_english_to_tamil(english_text):
    """Translate English text to Tamil while preserving numbers"""
    # Extract numbers from the text
    import re
    numbers = re.findall(r'\d+\.?\d*', english_text)
    
    # Replace numbers with placeholders
    for i, num in enumerate(numbers):
        english_text = english_text.replace(num, f'__NUM_{i}__')
    
    # Split text into chunks of 400 characters (leaving room for placeholders)
    chunk_size = 400
    chunks = [english_text[i:i+chunk_size] for i in range(0, len(english_text), chunk_size)]
    
    # Translate each chunk
    translator = Translator(to_lang="ta", from_lang="en")
    translated_chunks = []
    for chunk in chunks:
        try:
            # Clean up the chunk before translation
            chunk = chunk.strip()
            if not chunk:
                continue
                
            translation = translator.translate(chunk)
            # Clean up the translation
            translation = translation.strip()
            translated_chunks.append(translation)
        except Exception as e:
            print(f"Translation error: {e}")
            translated_chunks.append(chunk)  # Keep original if translation fails
    
    # Join translated chunks with proper spacing
    translation = ' '.join(filter(None, translated_chunks))
    
    # Restore numbers
    for i, num in enumerate(numbers):
        translation = translation.replace(f'__NUM_{i}__', num)
    
    # Clean up any double spaces
    translation = re.sub(r'\s+', ' ', translation)
    
    return translation.strip()

def process_with_gemini(english_text, medical_report, conversation_history=None):
    """Process medical report with Gemini model"""
    # Prepare the conversation history
    history_text = ""
    if conversation_history:
        history_text = "\nPrevious conversation:\n" + "\n".join(conversation_history)
    
    prompt = f"""You are a medical assistant. Analyze the medical report and respond to the user's question in Tamil.

    User's question: {english_text}
    {history_text}
    
    Requirements:
    1. Respond only if the question relates to the medical report
    2. Keep the response under 500 words
    3. Use simple, non-medical language
    4. Focus on answering the specific question
    5. Avoid greetings, signatures, and repetitive headers
    6. respond in tamil
    
    Medical Report:
    {medical_report}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error processing with Gemini: {e}")
        return english_text  # Fallback to original text if there's an error

def text_to_speech(tamil_text):
    """Convert Tamil text to speech using ElevenLabs"""
    audio = client.generate(
        text=tamil_text,
        voice="Kathiravan - Social Media Voice - Youthful & Pleasant",
        model="eleven_multilingual_v2",
        voice_settings={
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    )
    
    # Save audio to file
    with open("output.mp3", "wb") as f:
        for chunk in audio:
            f.write(chunk)
    print("Audio saved as output.mp3")
    
    # Play the generated audio
    print("Playing audio...")
    os.system("afplay output.mp3")  # Using afplay for macOS

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def parse_medical_report(text):
    """Parse medical report text into a list of key-value pairs"""
    # Split text into lines
    lines = text.strip().split('\n')
    report = []
    
    for line in lines:
        # Look for patterns like "Test: Value" or "Test - Value"
        if ':' in line or '-' in line:
            separator = ':' if ':' in line else '-'
            parts = line.split(separator, 1)
            if len(parts) == 2:
                test = parts[0].strip()
                value = parts[1].strip()
                
                # Extract reference range if present
                reference = None
                if '(' in value and ')' in value:
                    ref_start = value.find('(')
                    ref_end = value.find(')')
                    reference = value[ref_start+1:ref_end]
                    value = value[:ref_start].strip()
                
                report.append({
                    'test': test,
                    'value': value,
                    'reference': reference
                })
    
    return report

def get_medical_report():
    """Get the medical report from the user using Streamlit file upload"""
    st.header("Upload Medical Report")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        try:
            # Extract text from PDF
            pdf_text = extract_text_from_pdf(uploaded_file)
            
            # Parse the medical report
            medical_report = parse_medical_report(pdf_text)
            
            # Show success message without displaying the data
            st.success("Medical report successfully processed!")
            
            return medical_report
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return None
    else:
        st.info("Please upload a PDF file containing the medical report")
        return None

def main():
    # Initialize Streamlit
    st.title("Medical Report Analysis System")
    
    # Initialize session state for conversation history
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    # Get the medical report
    medical_report = get_medical_report()
    
    if medical_report:
        # Create two columns for input methods
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Text Input")
            # Text input for English questions
            english_question = st.text_input("Enter your question in English:")
            if english_question:
                with st.spinner('Processing your question...'):
                    # Process the English question
                    processed_english = process_with_gemini(english_question, medical_report, st.session_state.conversation_history)
                    
                    with st.spinner('Translating response...'):
                        # Translate response to Tamil
                        tamil_response = translate_english_to_tamil(processed_english)
                        st.write(f"Answer: {tamil_response}")
                        
                        with st.spinner('Converting to speech...'):
                            # Convert to speech
                            text_to_speech(tamil_response)
                            
                            # Store the conversation in history
                            st.session_state.conversation_history.append(f"Q: {english_question}")
                            st.session_state.conversation_history.append(f"A: {processed_english}")
                            
                            # Add a button to replay the answer
                            if st.button("Replay Answer"):
                                with st.spinner('Converting to speech...'):
                                    text_to_speech(tamil_response)
        
        with col2:
            st.subheader("Voice Input")
            # Add a button for voice interaction
            if st.button("Interact"):
                st.write("Listening... Please speak your question in Tamil")
                
                with st.spinner('Listening for speech...'):
                    # Step 1: Listen to Tamil speech
                    tamil_text = listen_tamil()
                    if not tamil_text:
                        st.error("Could not understand the speech. Please try again.")
                        return
                
                with st.spinner('Translating speech to text...'):
                    # Step 2: Translate Tamil to English
                    english_text = translate_tamil_to_english(tamil_text)
                    st.write(f"Your question: {english_text}")
                
                with st.spinner('Processing with AI...'):
                    # Step 3: Process with Gemini
                    processed_english = process_with_gemini(english_text, medical_report, st.session_state.conversation_history)
                
                with st.spinner('Translating response...'):
                    # Step 4: Translate back to Tamil
                    final_tamil = translate_english_to_tamil(processed_english)
                    st.write(f"Answer: {final_tamil}")
                
                with st.spinner('Converting to speech...'):
                    # Step 5: Convert to speech
                    text_to_speech(final_tamil)
                    
                    # Store the conversation in history
                    st.session_state.conversation_history.append(f"Q: {english_text}")
                    st.session_state.conversation_history.append(f"A: {processed_english}")
                    
                    # Add a button to replay the answer
                    if st.button("Replay Voice Answer"):
                        with st.spinner('Converting to speech...'):
                            text_to_speech(final_tamil)
        
        # Add a button for follow-up question
        if st.button("Ask Follow-up Question"):
            st.write("Listening... Please speak your follow-up question in Tamil")
            
            with st.spinner('Listening for speech...'):
                # Listen for follow-up question
                followup_tamil = listen_tamil()
                if not followup_tamil:
                    st.error("Could not understand the speech. Please try again.")
                    return
            
            with st.spinner('Translating speech to text...'):
                # Translate follow-up question
                followup_english = translate_tamil_to_english(followup_tamil)
                st.write(f"Your follow-up question: {followup_english}")
            
            with st.spinner('Processing with AI...'):
                # Process follow-up with conversation history
                followup_response = process_with_gemini(followup_english, medical_report, st.session_state.conversation_history)
            
            with st.spinner('Translating response...'):
                # Translate response
                followup_tamil_response = translate_english_to_tamil(followup_response)
                st.write(f"Answer: {followup_tamil_response}")
            
            with st.spinner('Converting to speech...'):
                # Convert to speech
                text_to_speech(followup_tamil_response)
                
                # Store the follow-up in history
                st.session_state.conversation_history.append(f"Q: {followup_english}")
                st.session_state.conversation_history.append(f"A: {followup_response}")
                
                # Add a button to replay the follow-up answer
                if st.button("Replay Follow-up Answer"):
                    with st.spinner('Converting to speech...'):
                        text_to_speech(followup_tamil_response)

if __name__ == "__main__":
    main()