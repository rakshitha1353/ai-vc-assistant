import os
import google.generativeai as genai

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY is not set.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("What is the capital of France?", stream=False)
        print("Successfully connected to Gemini API!")
        print("Response:", response.text)
        
except Exception as e:
    print("An error occurred:", e)