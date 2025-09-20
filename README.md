AI-Powered VC Due Diligence Assistant 🤖


Project Overview
The AI-Powered VC Due Diligence Assistant is a cutting-edge tool designed to help venture capital analysts, angel investors, and startup founders quickly and comprehensively analyze a company's pitch deck or deal note.

By leveraging Google's Gemini AI, the application goes beyond a simple summary, providing a deep-dive analysis, identifying key risks and opportunities, and even simulating a live pitch meeting. This project streamlines the initial screening process, allowing for faster and more informed investment decisions.

Key Features ✨
Core Analysis: Instantly generates a concise, investor-ready deal note covering financials, market opportunity, team, and technology.

Proactive Alerts: Provides a high-level summary of "🟢 Green Lights" (Strengths) and "🔴 Red Flags" (Risks) immediately after file upload.

Interactive Pitch Meeting Simulation: This is the unique feature. The AI adopts the persona of a startup founder, allowing investors to "Q&A" the pitch deck directly. This simulates a live meeting and helps in vetting the founder's narrative.

What-If Scenario Analysis: A powerful tool to model how changes in key metrics (e.g., increased burn rate or funding ask) would impact the investment case and runway.

Comprehensive Financial and Market Analysis: Conducts a detailed breakdown of the company's financial health, competitive landscape, and overall market position.

PDF and Text Support: Supports analysis of both .pdf and .txt files for maximum flexibility.


### 1. Clone the Repository

First, clone this repository to your local machine using the following commands:

```bash
git clone https://github.com/rakshitha1353/ai-vc-assistant.git
cd ai-vc-assistant

2. Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies.
'''bash
python -m venv .venv
.\.venv\Scripts\activate

3. Install Dependencies
With your virtual environment activated, install all the required libraries:
'''bash
pip install -r requirements.txt

4. Set Your Google API Key
For the application to function, you need a Google API key for the Gemini model. Do not hardcode your key in the script. Instead, create a .env file in your project directory and set the key as an environment variable.

Create a file named .env in the root of your project.

Add your key to the file in the following format:
'''bash
GOOGLE_API_KEY="your_api_key_here"

5. Run the Application
Now you can start the Streamlit application from your terminal:
'''bash
streamlit run app.py
