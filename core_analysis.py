import google.generativeai as genai
import re
from textblob import TextBlob
import os
import ast
import streamlit as st
import fitz # PyMuPDF
from io import BytesIO
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Centralized function to get the Gemini model ---
def get_gemini_model():
    if "gemini_model" not in st.session_state:
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                st.error("Error: GOOGLE_API_KEY is not set.")
                return None
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Test the API key
            model.generate_content("test", stream=False)
            
            st.session_state["gemini_model"] = model
            return model
            
        except Exception as e:
            st.error(f"Error during AI analysis. Please check your API key or try again. Details: {e}")
            return None
    
    return st.session_state["gemini_model"]

def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "text/plain":
        try:
            return uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            return uploaded_file.read().decode("latin-1")
    elif uploaded_file.type == "application/pdf":
        try:
            pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = ""
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text += page.get_text()
            return text
        except Exception as e:
            st.error(f"Error extracting text from PDF: {e}")
            return ""
    return ""

def extract_dynamic_metrics(data):
    model = get_gemini_model()
    if model is None: return None
    
    extraction_prompt = f"""
    You are an expert financial analyst. Read the following startup data and extract the key metrics as a Python dictionary. Be precise and provide only the dictionary. If a metric is not found, use None as the value.

    Startup Data:
    {data}

    Expected Output Dictionary:
    {{
      "company_name": "String",
      "founding_year": "Integer",
      "funding_ask": "Float (in Cr)",
      "valuation_post_money": "Float (in Cr)",
      "projected_arr": "Float (in Cr)",
      "burn_rate_monthly": "Float",
      "runway_months": "Integer",
      "patents_filed": "Integer",
      "ltv_to_cac_ratio": "Float"
    }}
    """
    try:
        response = model.generate_content(extraction_prompt)
        dict_string = re.search(r'\{.*?\}', response.text, re.DOTALL).group(0)
        return ast.literal_eval(dict_string)
    except Exception as e:
        print(f"Error extracting dynamic metrics: {e}")
        return None

def get_risk_score_components(metrics):
    components = {'Runway Score': 0, 'Burn Rate Score': 0, 'Patents Score': 0, 'LTV:CAC Score': 0}
    
    try:
        runway_months = float(metrics.get('runway_months') or 0)
        burn_rate_monthly = float(metrics.get('burn_rate_monthly') or 0)
        patents_filed = int(metrics.get('patents_filed') or 0)
        ltv_to_cac_ratio = float(metrics.get('ltv_to_cac_ratio') or 0)
    except (ValueError, TypeError):
        runway_months = burn_rate_monthly = patents_filed = ltv_to_cac_ratio = 0

    if runway_months >= 12:
        components['Runway Score'] = 5
    elif runway_months >= 6:
        components['Runway Score'] = 3
        
    if burn_rate_monthly > 0 and burn_rate_monthly < 50000:
        components['Burn Rate Score'] = 2
        
    if patents_filed > 0:
        components['Patents Score'] = 3
        
    if ltv_to_cac_ratio >= 3:
        components['LTV:CAC Score'] = 2
    elif ltv_to_cac_ratio >= 1:
        components['LTV:CAC Score'] = 1

    return components

def get_sentiment_score(text):
    if not text.strip(): return 0.0
    analysis = TextBlob(text)
    return analysis.sentiment.polarity
    
def generate_deal_note(data):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    deal_note_prompt = f"""
    You are an AI-powered analyst for startup evaluation. Your task is to review the following founder material and generate a concise, investor-ready deal note.

    Focus on these key sections:
    1.  **Executive Summary:** A brief overview of the startup, its mission, and its market.
    2.  **Product & Technology:** Describe the core product, its key features, and any proprietary technology like patents.
    3.  **Team:** Evaluate the founding team's experience and expertise.
    4.  **Market Opportunity:** Analyze the market size (TAM, SAM, SOM) and the startup's growth potential within it.
    5.  **Financials:** Summarize key financial metrics (e.g., ARR, runway, burn rate, funding ask).
    6.  **Key Highlights:** List 3-5 positive takeaways.

    Founder Material:
    {data}
    """
    try: response = model.generate_content(deal_note_prompt); return response.text
    except Exception as e: return f"Error generating deal note: {e}"

def generate_risk_summary(risk_score, sentiment_score, metrics):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    risk_summary_prompt = f"""
    You are an expert risk analyst. Based on the following metrics, provide a comprehensive risk assessment.

    - Total Risk Score: {risk_score} (out of 12)
    - Sentiment Score: {sentiment_score} (from -1 to 1)
    - Key Metrics: {metrics}

    Your assessment should include:
    - An overall risk rating (e.g., High, Medium, Low).
    - A brief explanation of the key risk factors (e.g., short runway, high burn rate).
    - A summary of potential red flags.
    """
    try: response = model.generate_content(risk_summary_prompt); return response.text
    except Exception as e: return f"Error generating risk summary: {e}"

def generate_financial_health_analysis(data):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    financial_prompt = f"""
    You are a financial auditor. Perform a detailed financial health analysis of the startup based on the following data.

    Your analysis should include:
    1.  **Revenue Streams:** Describe how the company makes money.
    2.  **Burn Rate & Runway:** Evaluate the company's cash burn and how long its capital will last.
    3.  **Funding Ask & Valuation:** Comment on the reasonableness of the funding ask relative to the valuation.
    4.  **Key Financial Ratios:** Discuss metrics like LTV:CAC if available.

    **Instructions:**
    - Perform a best-effort analysis.
    - If information is not present, state that fact rather than asking for the data.

    Startup Data:
    {data}
    """
    try: response = model.generate_content(financial_prompt); return response.text
    except Exception as e: return f"Error generating financial health analysis: {e}"

def generate_competitive_analysis(data):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    competitive_prompt = f"""
    You are a market strategist. Analyze the following startup data and generate a detailed competitive landscape analysis.

    Your response should include:
    1.  **Primary Competitors:** Identify the main rivals mentioned or implied in the text.
    2.  **Competitive Advantage:** Explain what makes this startup unique.
    3.  **Market Position:** Describe where the startup fits in the current market.

    **Instructions:**
    - Perform a best-effort analysis.
    - If the information is not present, state that fact rather than asking for the data.

    Startup Data:
    {data}
    """
    try: response = model.generate_content(competitive_prompt); return response.text
    except Exception as e: return f"Error generating competitive analysis: {e}"

def generate_customer_supplier_analysis(data):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    customer_supplier_prompt = f"""
    You are an operations expert. Based on the following startup data, analyze the customer and supplier relationships.

    Your response should cover:
    1.  **Customer Profile:** Describe the target customer segment.
    2.  **Supplier Dependencies:** Identify any critical suppliers or partners.
    3.  **Key Relationships:** Summarize the startup's key business relationships.
    """
    try: response = model.generate_content(customer_supplier_prompt); return response.text
    except Exception as e: return f"Error generating customer/supplier analysis: {e}"

def generate_founder_analysis(data):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    founder_prompt = f"""
    You are a human resources specialist. Analyze the founding team based on the following startup data.

    Your analysis should include:
    1.  **Experience:** Comment on the founders' relevant experience.
    2.  **Skills:** Highlight key skills and expertise.
    3.  **Potential Red Flags:** Mention any potential risks related to the team.

    **Instructions:**
    - Perform a best-effort analysis.
    - If the information is not present, state that fact rather than asking for the data.
    - Example: "Based on the provided data, the founders' experience is strong in technology development. No information was provided regarding their education or previous roles."

    Startup Data:
    {data}
    """
    try: response = model.generate_content(founder_prompt); return response.text
    except Exception as e: return f"Error generating founder analysis: {e}"

def generate_risk_mitigation_strategies(data):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    risk_mitigation_prompt = f"""
    You are a strategic advisor. Based on the following startup data, propose clear, actionable risk mitigation strategies for a potential investor.

    Your suggestions should address key risks identified in the document and be specific.
    
    **Instructions:**
    - Perform a best-effort analysis.
    - If the information is not present, state what risks cannot be addressed due to lack of data rather than asking for the data.

    Startup Data:
    {data}
    """
    try: response = model.generate_content(risk_mitigation_prompt); return response.text
    except Exception as e: return f"Error generating risk mitigation strategies: {e}"

def generate_swot(data):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    swot_prompt = f"""
    You are a business strategist. Perform a detailed SWOT analysis (Strengths, Weaknesses, Opportunities, Threats) based on the following startup data.

    Provide a clear bulleted list for each section.

    **Instructions:**
    - Perform a best-effort analysis.
    - If the information is not present, state that fact rather than asking for the data.

    Startup Data:
    {data}
    """
    try: response = model.generate_content(swot_prompt); return response.text
    except Exception as e: return f"Error generating SWOT analysis: {e}"

def generate_market_analysis(data):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    market_prompt = f"""
    You are a market analyst. Based on the following startup data, provide an analysis of the market sizing and opportunity.

    Your analysis should include:
    1.  **Market Size:** Provide estimates for TAM (Total Addressable Market), SAM (Serviceable Addressable Market), and SOM (Serviceable Obtainable Market) if possible, or describe the market size qualitatively.
    2.  **Growth Potential:** Explain the potential for the startup to grow within this market.
    3.  **Industry & Market Trends:** Analyze broader industry trends and the regulatory landscape.

    **Instructions:**
    - Perform a best-effort analysis.
    - If the information is not present, state that fact rather than asking for the data.
    
    Startup Data:
    {data}
    """
    try: response = model.generate_content(market_prompt); return response.text
    except Exception as e: return f"Error generating market analysis: {e}"

def generate_customizable_recommendation(data, risk_appetite, investment_focus):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    recommendation_prompt = f"""
    You are an experienced venture capital investor. Based on the following startup data and the investment criteria:
    - Risk Appetite: {risk_appetite} (on a scale of 1-10)
    - Investment Focus: {investment_focus}

    Provide a concise, investor-ready recommendation. State your final verdict (e.g., "Pass," "Revisit," or "Invest") and provide a clear rationale based on the provided data and investment criteria.

    Startup Data:
    {data}
    """
    try:
        response = model.generate_content(recommendation_prompt); return response.text
    except Exception as e: return f"Error generating recommendation: {e}"

def refine_analysis(data, user_query):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    refine_prompt = f"""
    You are an expert financial analyst. A user has provided a query to refine the analysis of a startup.
    User's Query: {user_query}
    Startup Data: {data}
    
    Refine the analysis based on the user's query and the provided data.
    """
    try:
        response = model.generate_content(refine_prompt); return response.text
    except Exception as e: return f"Error refining analysis: {e}"

def analyze_historical_data(df):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."
    
    # Convert DataFrame to a string format for the AI
    df_string = df.to_string()
    
    prompt = f"""
    You are an expert financial analyst. Analyze the following historical financial data for a startup.
    
    Historical Data:
    {df_string}
    
    Provide a concise analysis focusing on:
    1.  **Growth Trends:** Is revenue or user count accelerating or decelerating?
    2.  **Unit Economics:** How have key metrics like LTV, CAC, or churn changed over time?
    3.  **Seasonality:** Are there any consistent patterns or spikes in the data?
    4.  **Overall Health:** Provide a summary of the company's historical financial health.
    """
    try:
        response = model.generate_content(prompt); return response.text
    except Exception as e: return f"Error analyzing historical data: {e}"

def run_scenario_analysis(burn_rate_increase, funding_ask_increase, dynamic_metrics):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."

    try:
        original_burn = dynamic_metrics.get('burn_rate_monthly') or 0
        original_funding = dynamic_metrics.get('funding_ask') or 0
        original_runway = dynamic_metrics.get('runway_months') or 0
        
        # Calculate new metrics
        new_burn = original_burn * (1 + burn_rate_increase)
        new_funding = original_funding * (1 + funding_ask_increase)
        # Simplified runway calculation: new_runway = (new_funding * 10,00,000) / new_burn
        # Assuming funding ask is in Cr and burn rate is in some unit
        new_runway = (new_funding * 10000000) / new_burn if new_burn > 0 else "N/A"
        
        prompt = f"""
        You are a strategic advisor. The user is performing a what-if scenario analysis for a startup with the following original metrics:
        - Original Monthly Burn Rate: ${original_burn}
        - Original Funding Ask: {original_funding} Cr
        - Original Runway: {original_runway} months
        
        The user wants to analyze a new scenario with the following changes:
        - Monthly Burn Rate increases by {burn_rate_increase * 100}% to ${new_burn:.2f}
        - Funding Ask increases by {funding_ask_increase * 100}% to {new_funding:.2f} Cr
        - New Estimated Runway: {new_runway} months
        
        Based on this new scenario, provide an updated assessment of:
        1.  **Investment Viability:** How does this scenario impact the overall investment viability?
        2.  **Risk Profile:** Does this change the risk profile (e.g., higher burn = higher risk)?
        3.  **Key Considerations:** What should an investor consider given these new metrics?
        """
        response = model.generate_content(prompt); return response.text
    except Exception as e: return f"Error running scenario analysis: {e}"

def get_proactive_alerts(data):
    model = get_gemini_model()
    if model is None: return None
    
    prompt = f"""
    You are an expert VC analyst. Analyze the following startup data and provide a concise summary of the top 3 strengths and top 3 risks.

    Provide the output in the following structured format only:
    ### 🟢 Green Lights (Strengths)
    - [Strength 1]
    - [Strength 2]
    - [Strength 3]

    ### 🔴 Red Flags (Risks)
    - [Risk 1]
    - [Risk 2]
    - [Risk 3]

    Startup Data:
    {data}
    """
    try:
        response = model.generate_content(prompt); return response.text
    except Exception as e: return f"Error generating proactive alerts: {e}"

def generate_presentation_highlights(data):
    model = get_gemini_model()
    if model is None: return None
    
    prompt = f"""
    You are an expert pitch deck designer. Analyze the following startup data and generate key highlights in a bullet-point format suitable for a presentation.

    Structure the content into three distinct slides/sections.
    
    ### Slide 1: Executive Summary
    - [Brief overview of the company]
    - [Key product/technology]
    - [Main market opportunity]

    ### Slide 2: Key Highlights & Traction
    - [Highlight 1: E.g., Strong Revenue Growth]
    - [Highlight 2: E.g., Experienced Founding Team]
    - [Highlight 3: E.g., Patented Technology]

    ### Slide 3: Risks & Proposed Mitigation
    - [Risk 1: E.g., High Burn Rate] - [Proposed Mitigation]
    - [Risk 2: E.g., Competitive Market] - [Proposed Mitigation]
    - [Risk 3: E.g., Short Runway] - [Proposed Mitigation]

    Startup Data:
    {data}
    """
    try:
        response = model.generate_content(prompt); return response.text
    except Exception as e: return f"Error generating presentation highlights: {e}"

def simulate_pitch_meeting(data, user_query):
    model = get_gemini_model()
    if model is None: return None
    
    prompt = f"""
    You are a startup founder in a live pitch meeting. The investor has just asked you a question. Respond in the persona of a founder, using the provided data as your source of truth. If the data does not contain the answer, give a plausible, confident, but non-committal answer.

    Investor Question: {user_query}
    Pitch Deck Data: {data}
    """
    try:
        response = model.generate_content(prompt); return response.text
    except Exception as e: return f"Error simulating pitch meeting: {e}"

def generate_risk_opportunity_matrix(data):
    model = get_gemini_model()
    if model is None: return "Error: Gemini model not available. Please check your API key."

    prompt = f"""
    You are a venture capital expert. Analyze the following startup data and generate a detailed risk and opportunity matrix.

    Your response should be structured clearly with two main sections:
    1.  **Risk Matrix:**
        - **Market Risk:** (e.g., "High," "Medium," "Low") and a brief justification.
        - **Execution Risk:** (e.g., "High," "Medium," "Low") and a brief justification.
        - **Financial Risk:** (e.g., "High," "Medium," "Low") and a brief justification.
        - **Technology Risk:** (e.g., "High," "Medium," "Low") and a brief justification.
    
    2.  **Key Opportunities:**
        - List 3-5 major opportunities for the startup to grow and scale.
        - Justify each opportunity with a short explanation.
    
    Startup Data:
    {data}
    """
    try:
        response = model.generate_content(prompt); return response.text
    except Exception as e: return f"Error generating risk/opportunity matrix: {e}"