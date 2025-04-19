from elevenlabs.client import ElevenLabs
import os
import speech_recognition as sr
from translate import Translator
import google.generativeai as genai

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

def process_with_gemini(english_text, medical_summary):
    """Process medical report with Gemini model"""
    prompt = f"""You are a medical assistant. Analyze the medical report and respond to the user's question in Tamil.

    User's question: {english_text}
    
    Requirements:
    1. Respond only if the question relates to the medical report
    2. Keep the response under 500 words
    3. Use simple, non-medical language
    4. Focus on answering the specific question
    5. Avoid greetings, signatures, and repetitive headers
    6. respond in tamil
    
    Medical Report:
    {medical_summary}
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

def get_medical_report():
    """Get the medical report from the user"""
    sample_medical_report =[{'test': 'HIGH SENSITIVITY C-REACTIVE PROTEIN (HS-CRP)',
  'value': '2.87',
  'reference': '< 3 mg/L'},
 {'test': 'HOMOCYSTEINE', 'value': '14.38', 'reference': '<15 µmol/L'},
 {'test': 'TRIG / HDL RATIO', 'value': '2.16', 'reference': '< 3.12 Ratio'},
 {'test': 'PLATELET DISTRIBUTION WIDTH(PDW)',
  'value': '9.9',
  'reference': '9.6-15.2 fL'},
 {'test': 'PLATELET TO LARGE CELL RATIO(PLCR)',
  'value': '20.2',
  'reference': '19.7-42.4 %'},
 {'test': 'HDL / LDL RATIO', 'value': '0.2', 'reference': '> 0.40 Ratio'},
 {'test': 'HDL CHOLESTEROL - DIRECT',
  'value': '35',
  'reference': '40-60 mg/dL'},
 {'test': 'LDL / HDL RATIO', 'value': '5', 'reference': '1.5-3.5 Ratio'},
 {'test': 'LDL CHOLESTEROL - DIRECT',
  'value': '176',
  'reference': '< 100 mg/dL'},
 {'test': 'NON-HDL CHOLESTEROL', 'value': '214.6', 'reference': '< 160 mg/dL'},
 {'test': 'TC/ HDL CHOLESTEROL RATIO',
  'value': '7.1',
  'reference': '3 - 5 Ratio'},
 {'test': 'TOTAL CHOLESTEROL', 'value': '250', 'reference': '< 200 mg/dL'},
 {'test': 'TRIGLYCERIDES', 'value': '182', 'reference': '< 150 mg/dL'},
 {'test': 'ASPARTATE AMINOTRANSFERASE (SGOT )',
  'value': '41',
  'reference': '< 35 U/L'},
 {'test': 'SERUM GLOBULIN', 'value': '3.41', 'reference': '2.5-3.4 gm/dL'},
 {'test': 'ERYTHROCYTE SEDIMENTATION RATE (ESR)',
  'value': '28',
  'reference': '/ hr 0 - 15 mm'},
 {'test': 'BLOOD UREA NITROGEN (BUN)',
  'value': '6.36',
  'reference': '7.94 - 20.07 mg/dL'},
 {'test': 'BUN / SR.CREATININE RATIO',
  'value': '8.15',
  'reference': '9:1-23:1 Ratio'},
 {'test': 'UREA (CALCULATED)',
  'value': '13.61',
  'reference': 'Adult : 17-43 mg/dL'},
 {'test': '25-OH VITAMIN D (TOTAL)',
  'value': '30.5',
  'reference': '30-100 ng/mL'}]
    return sample_medical_report
def main():
    # Step 1: Listen to Tamil speech
    tamil_text = listen_tamil()
    if not tamil_text:
        return
    
    # Step 2: Translate Tamil to English
    english_text = translate_tamil_to_english(tamil_text)
    print(f"Translated to English: {english_text}")
    
    #Step 3: Get the medical report
    medical_summary = get_medical_report()

    # Step 3: Process with Gemini Flash
    processed_english = process_with_gemini(english_text, medical_summary)
    print(f"Processed by Gemini: {processed_english}")
    
    # Step 4: Translate back to Tamil
    final_tamil = translate_english_to_tamil(processed_english)
    print(f"Translated back to Tamil: {final_tamil}")
    
    # Step 5: Convert to speech
    text_to_speech(final_tamil)

if __name__ == "__main__":
    main()