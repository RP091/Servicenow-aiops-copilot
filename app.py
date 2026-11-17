import streamlit as st
import ollama
import requests

# --- TELEGRAM SETUP ---
TELEGRAM_BOT_TOKEN = '8876623929:AAEuHDk7YScCgD63pH2DLXviAnDKWMyC440'
TELEGRAM_CHAT_ID = '7547542403'

def send_telegram_alert(message_body):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"🚨 *AIOps Degradation Alert* 🚨\n\n{message_body}",
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True
        else:
            st.error(f"Telegram API Error: {response.text}")
            return False
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False

# Page setup
st.set_page_config(page_title="AIOps Copilot (Local)", page_icon="🛠️")
st.title("🛠️ Local AIOps Support Copilot")
st.caption("Running 100% locally and securely using Llama 3.2.")

# Sidebar for file uploads
with st.sidebar:
    st.header("📂 Analyze Log Files")
    uploaded_file = st.file_uploader("Upload a server log (.txt or .log)", type=["txt", "log"])
    file_context = ""
    if uploaded_file is not None:
        file_context = uploaded_file.getvalue().decode("utf-8")[-2000:]
        st.success("Log file loaded securely in memory.")

# Create tabs for Manual Chat vs Automated Webhook simulation
tab1, tab2 = st.tabs(["💬 Manual RCA Chat", "🚨 Grafana/Splunk Webhook Listener"])

with tab1:
    st.caption("Chat with your local SRE Assistant.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Example: Nginx 502 Bad Gateway or paste a stack trace..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        system_instruction = f"""
        You are an expert Site Reliability Engineer (SRE) Assistant. 
        Rule 1: If the user provides an infrastructure error, log, or technical issue, provide a concise Root Cause Analysis (RCA) and 2-3 exact terminal commands to fix it.
        Rule 2: If the user says hello, asks how you are, or makes casual conversation, respond naturally, politely, and conversationally.
        
        Attached Log File Content: {file_context if uploaded_file else 'None'}
        User Input: {prompt}
        """

        with st.chat_message("assistant"):
            try:
                response_stream = ollama.chat(
                    model='llama3.2',
                    messages=[{'role': 'user', 'content': system_instruction}],
                    stream=True
                )
                def stream_data():
                    for chunk in response_stream:
                        yield chunk['message']['content']
                response_text = st.write_stream(stream_data)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Error: Make sure Ollama is running. Details: {e}")

with tab2:
    st.header("Simulate APM Degradation Alert")
    st.info("In a production environment, Grafana or Splunk would POST this JSON to our app automatically. Here, we simulate that trigger.")
    
    sample_grafana_payload = """
    {
      "ruleName": "High CPU Usage - Production Database",
      "state": "alerting",
      "message": "CPU on Oracle DB pod exceeded 95% for 5 minutes.",
      "evalMatches": [
        {"metric": "cpu_usage", "tags": {"cluster": "us-east-1", "service": "oracle-erp"}, "value": 98.4}
      ]
    }
    """
    
    st.code(sample_grafana_payload, language='json')
    
    if st.button("Trigger Webhook & Send Telegram Alert"):
        with st.spinner("Llama 3.2 is analyzing the APM payload..."):
            webhook_prompt = f"Analyze this Grafana alert JSON. Keep it very short. State the impacted service, the root cause, and 1 exact terminal command to mitigate it: {sample_grafana_payload}"
            
            try:
                response = ollama.chat(
                    model='llama3.2',
                    messages=[{'role': 'user', 'content': webhook_prompt}]
                )
                
                ai_rca = response['message']['content']
                st.write("**AI Analysis Generated:**")
                st.success(ai_rca)
                
                with st.spinner("Dispatching to Telegram..."):
                    if send_telegram_alert(ai_rca):
                        st.success("Telegram Alert Sent Successfully! Check your phone.")
            except Exception as e:
                st.error(f"Error: {e}")