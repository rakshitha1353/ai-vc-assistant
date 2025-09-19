import streamlit as st
import core_analysis
import matplotlib.pyplot as plt
import numpy as np
import os
import io
import pandas as pd

# --- Custom Styling ---
st.markdown("""
    <style>
    .stApp {
        background-color: #f5f7fa;
    }
    .main .block-container {
        padding: 2rem 3rem;
    }
    h1, h2, h3 {
        color: #333333;
        font-weight: 600;
    }
    .stApp > header {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        padding: 30px;
        margin-top: 20px;
    }
    .main > .block-container {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        padding: 30px;
        margin-top: 20px;
    }
    .stFileUploader {
        border: 2px dashed #999999;
        border-radius: 8px;
        padding: 20px;
    }
    .stFileUploader label {
        color: #555555;
        font-weight: bold;
    }
    .st-emotion-cache-1d391kg {
        background-color: #f0f2f6;
    }
    .st-emotion-cache-121bd7z {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Page Configuration ---
st.set_page_config(
    page_title="AI-Powered VC Due Diligence",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Session State Management ---
def clear_all_state():
    """Clears all keys in the session state."""
    st.session_state.clear()
    
if 'analysis_done' not in st.session_state:
    st.session_state['analysis_done'] = False
if 'last_uploaded_file_name' not in st.session_state:
    st.session_state['last_uploaded_file_name'] = None

st.title("AI-Powered VC Due Diligence Assistant")
st.write("Upload a pitch deck or deal note to get an instant analysis.")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['txt', 'pdf'],
        label_visibility="hidden"
    )

# --- Main App Logic ---
# Check if a new file has been uploaded
if uploaded_file is not None and uploaded_file.name != st.session_state.get('last_uploaded_file_name'):
    # Clear the state and re-analyze for the new file
    st.session_state.clear()
    st.session_state['last_uploaded_file_name'] = uploaded_file.name
    st.session_state['analysis_done'] = False

    with st.spinner('Extracting text from file...'):
        startup_data = core_analysis.extract_text_from_file(uploaded_file)
    
    if startup_data:
        with st.spinner('Analyzing data...'):
            dynamic_metrics = core_analysis.extract_dynamic_metrics(startup_data)
            if dynamic_metrics is None:
                st.stop()
            
            st.session_state['dynamic_metrics'] = dynamic_metrics
            st.session_state['risk_score_components'] = core_analysis.get_risk_score_components(dynamic_metrics)
            st.session_state['risk_score'] = sum(st.session_state['risk_score_components'].values())
            st.session_state['sentiment_score'] = core_analysis.get_sentiment_score(startup_data)
            st.session_state['startup_data'] = startup_data
            
        st.session_state['analysis_done'] = True
        st.rerun()

# Display analysis results if a file has been processed
if st.session_state['analysis_done']:
    st.success("Analysis complete!")
    startup_data = st.session_state['startup_data']
    dynamic_metrics = st.session_state['dynamic_metrics']
    risk_score_components = st.session_state['risk_score_components']
    risk_score = st.session_state['risk_score']
    sentiment_score = st.session_state['sentiment_score']

    # --- Proactive Alerts ---
    with st.expander("🚨 AI's Instant Highlights", expanded=True):
        proactive_alerts = core_analysis.get_proactive_alerts(startup_data)
        st.markdown(proactive_alerts)

    st.markdown("---")
    st.subheader("Key Metrics Extracted by AI")
    metrics_cols = st.columns(4)
    if dynamic_metrics:
        with metrics_cols[0]: st.metric(label="Funding Ask", value=f"{dynamic_metrics.get('funding_ask', 'N/A')}")
        with metrics_cols[1]: st.metric(label="Valuation", value=f"{dynamic_metrics.get('valuation_post_money', 'N/A')}")
        with metrics_cols[2]: st.metric(label="Monthly Burn", value=f"${dynamic_metrics.get('burn_rate_monthly', 'N/A')}")
        with metrics_cols[3]: st.metric(label="Runway", value=f"{dynamic_metrics.get('runway_months', 'N/A')} months")

    # --- Automated Presentation Button ---
    if st.button("Generate Pitch Deck Highlights 🖼️"):
        with st.spinner("Generating presentation slides..."):
            presentation = core_analysis.generate_presentation_highlights(startup_data)
            st.markdown(presentation)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Core Analysis", "🤝 Team", "💰 Financials", "📈 Historical & What-If", "🔍 Deep Dives", "🤖 Interactive AI"])

    with tab1:
        st.header("1. Deal Note")
        deal_note = core_analysis.generate_deal_note(startup_data)
        st.markdown(deal_note)
        
        st.header("2. Risk Assessment")
        risk_summary = core_analysis.generate_risk_summary(risk_score, sentiment_score, dynamic_metrics)
        st.markdown(risk_summary)
        
        st.subheader("Risk Score Breakdown")
        total_risk_score = sum(risk_score_components.values())
        if total_risk_score > 0:
            labels = list(risk_score_components.keys())
            sizes = list(risk_score_components.values())
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = plt.cm.get_cmap('Paired', len(labels))
            bars = ax.bar(labels, sizes, color=colors(range(len(labels))))
            ax.set_ylabel('Score Contribution')
            ax.set_title('Individual Factor Contribution to Total Risk Score')
            ax.set_ylim(0, max(sizes) + 1)
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')
            st.pyplot(fig)
        else:
            st.info("No data available to generate a risk breakdown chart.")
        
        st.header("3. AI-Powered Recommendation")
        st.write("Adjust the sliders below to get a customized recommendation.")
        col_rec1, col_rec2 = st.columns(2)
        with col_rec1:
            risk_appetite = st.slider("Risk Appetite", min_value=1, max_value=10, value=5)
        with col_rec2:
            investment_focus = st.selectbox("Investment Focus", ["High Growth", "Stable Returns", "Social Impact"])
        
        if st.button("Generate Customized Recommendation"):
            with st.spinner("Generating recommendation..."):
                recommendation = core_analysis.generate_customizable_recommendation(startup_data, risk_appetite, investment_focus)
                st.markdown(recommendation)

    with tab2:
        st.header("4. Founder & Team Analysis")
        founder_analysis = core_analysis.generate_founder_analysis(startup_data)
        st.markdown(founder_analysis)
        
        st.header("5. Risk Mitigation Strategies")
        risk_mitigation_strategies = core_analysis.generate_risk_mitigation_strategies(startup_data)
        st.markdown(risk_mitigation_strategies)

    with tab3:
        st.header("6. Financial Health Analysis")
        financial_health = core_analysis.generate_financial_health_analysis(startup_data)
        st.markdown(financial_health)

        st.header("7. Customer & Supplier Analysis")
        cust_sup_analysis = core_analysis.generate_customer_supplier_analysis(startup_data)
        st.markdown(cust_sup_analysis)

    with tab4:
        st.header("8. Historical Data Analysis")
        st.write("Upload a CSV file with historical data to analyze trends. (e.g., columns: Date, Revenue, Expenses)")
        historical_file = st.file_uploader("Upload Historical CSV", type=['csv'], key="historical_uploader")
        if historical_file is not None:
            try:
                historical_df = pd.read_csv(historical_file)
                st.write("### Uploaded Data")
                st.dataframe(historical_df)
                
                with st.spinner("Analyzing historical trends..."):
                    historical_analysis = core_analysis.analyze_historical_data(historical_df)
                    st.markdown(historical_analysis)
            except Exception as e:
                st.error(f"Error reading CSV file. Please ensure it's a valid CSV. Details: {e}")

        st.header("9. What-If Scenario Analysis")
        st.write("Adjust the sliders to see how changes to key metrics affect the investment case.")
        col_if1, col_if2 = st.columns(2)
        with col_if1:
            burn_rate_increase = st.slider("Monthly Burn Rate Increase (%)", 0, 100, 20) / 100
        with col_if2:
            funding_ask_increase = st.slider("Funding Ask Increase (%)", 0, 100, 10) / 100

        if st.button("Run Scenario Analysis"):
            with st.spinner("Running what-if analysis..."):
                scenario_result = core_analysis.run_scenario_analysis(burn_rate_increase, funding_ask_increase, dynamic_metrics)
                st.markdown(scenario_result)
        
    with tab5:
        st.header("10. Competitive Landscape Analysis")
        competitive_analysis = core_analysis.generate_competitive_analysis(startup_data)
        st.markdown(competitive_analysis)

        st.header("11. SWOT Analysis")
        swot_analysis = core_analysis.generate_swot(startup_data)
        st.markdown(swot_analysis)

        st.header("12. Risk & Opportunity Matrix")
        risk_opportunity = core_analysis.generate_risk_opportunity_matrix(startup_data)
        st.markdown(risk_opportunity)

    with tab6:
        st.header("13. Interactive AI Chat")
        chat_mode = st.radio("Select Chat Mode:", ["VC Analyst (Refine Analysis)", "Founder (Simulate Pitch Meeting)"], key="chat_mode")

        user_query = st.text_input("Ask a question about the analysis:", key="chat_input")
        if st.button("Get Response"):
            if user_query:
                if chat_mode == "VC Analyst (Refine Analysis)":
                    with st.spinner("Refining analysis..."):
                        refined_response = core_analysis.refine_analysis(startup_data, user_query)
                        st.markdown(refined_response)
                else: # Founder mode
                    with st.spinner("Simulating founder response..."):
                        founder_response = core_analysis.simulate_pitch_meeting(startup_data, user_query)
                        st.markdown(founder_response)
            else:
                st.warning("Please enter a question to get a response.")
    
else:
    st.info("Upload a .txt or .pdf file to begin the analysis.")
    if st.button("Clear Analysis"):
        clear_all_state()
        st.rerun()