import streamlit as st
import ollama
import os
import random
from datetime import datetime

# --- 1. LOCAL DATABASE & TEMPLATES ---
HISTORY_DB = "resolved_incidents.txt"
QUEUE_DB = "active_incidents.txt"

INITIAL_TEMPLATE = """----Initial Notes Template----
Initial Symptoms/Issue Reported: {issue}
Sysops Analysis: 
Root Cause Hypothesis/Cause: 
Supporting Data: """

CASE_TEMPLATE = """----Case Notes Template----
Discussion Summary: 
Summary of Findings: 
Actions Performed: 
Impact Assessment: 
Next Steps: 
Estimated Resolution Time: 
User Actions: """

RESOLUTION_TEMPLATE = """----Resolution Notes Template----
Root Cause/Issue Cause: 
Resolution Description: 
Short Term Fix: 
Long Term Fix: 
Closure Approval: 

MOM:
Attendees: 
Issue discussion: 
Webex link and Password: 
Action Plan: """

# Initialize DB files
if not os.path.exists(HISTORY_DB):
    with open(HISTORY_DB, "w") as f:
        f.write("- INC1080000 (Resolved): Node.js memory leak. Fix: Enforced connection pooling.\n")

if not os.path.exists(QUEUE_DB):
    with open(QUEUE_DB, "w") as f:
        # Format is now: ID | User | Location | Issue (Short) | Description (Detailed)
        f.write("INC10818890|Priya Gaddam|TCS Hyderabad|Function Not Working|The Nginx web server is dropping connections and returning 502 Bad Gateway errors.\n")

def read_history():
    with open(HISTORY_DB, "r") as f:
        return f.read()

def get_active_tickets():
    with open(QUEUE_DB, "r") as f:
        return [line.strip().split("|") for line in f.readlines() if line.strip()]

def add_new_ticket(user, location, issue, description):
    ticket_id = f"INC108{random.randint(10000, 99999)}"
    # Clean newlines and pipes so it doesn't break our text file formatting
    clean_issue = issue.replace('\n', ' ').replace('|', '-')
    clean_desc = description.replace('\n', ' ').replace('|', '-')
    with open(QUEUE_DB, "a") as f:
        f.write(f"{ticket_id}|{user}|{location}|{clean_issue}|{clean_desc}\n")
    return ticket_id

def resolve_ticket(ticket_id, issue, fix):
    with open(HISTORY_DB, "a") as f:
        f.write(f"- {ticket_id} (Resolved): {issue}. Fix: {fix}\n")
    tickets = get_active_tickets()
    with open(QUEUE_DB, "w") as f:
        for t in tickets:
            if t[0] != ticket_id:
                f.write("|".join(t) + "\n")

# --- 2. WEB UI STYLING & SIDEBAR ---
st.set_page_config(page_title="Enterprise Service Platform - INC", layout="wide")

with st.sidebar:
    st.header("➕ Create New Ticket")
    with st.form("new_ticket_form", clear_on_submit=True):
        new_user = st.text_input("Impacted User:")
        new_loc = st.text_input("Location (e.g., TCS Hyderabad):")
        new_issue = st.text_input("Short Description / Issue:")
        new_desc = st.text_area("Detailed Description / Logs:")
        
        if st.form_submit_button("Submit Ticket") and new_user and new_issue and new_desc:
            new_id = add_new_ticket(new_user, new_loc, new_issue, new_desc)
            st.success(f"{new_id} Created!")
            st.rerun()
            
    st.divider()
    st.header("📋 Awaiting Assignment / WIP")
    active_tickets = get_active_tickets()
    
    if not active_tickets:
        st.write("No active incidents in queue.")
    else:
        for t in active_tickets:
            # Display the Short Description on the button
            short_title = t[3] if len(t) > 3 else "No Title"
            if st.button(f"🔴 {t[0]}: {short_title}", use_container_width=True):
                st.session_state.current_ticket = t
                st.session_state.messages = [] 

# --- 3. MAIN DASHBOARD (SERVICENOW CLONE) ---
if "current_ticket" not in st.session_state and active_tickets:
    st.session_state.current_ticket = active_tickets[0]

if "current_ticket" in st.session_state and st.session_state.current_ticket:
    # Unpack the 5 fields safely
    t = st.session_state.current_ticket
    t_id = t[0]
    t_user = t[1] if len(t) > 1 else "Unknown"
    t_loc = t[2] if len(t) > 2 else "Unknown"
    t_issue = t[3] if len(t) > 3 else "No Issue Provided"
    t_desc = t[4] if len(t) > 4 else "No detailed description provided."
    
    st.title(f"Enterprise Service Platform - {t_id}")
    st.info(f"Impacted User time & timezone: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST")

    # ServiceNow Grid Layout
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Number", value=t_id, disabled=True)
        st.text_input("* Impacted User", value=t_user)
        st.text_input("Location", value=t_loc)
        st.selectbox("Environment", ["Production", "Staging", "Development"])
        st.selectbox("Category", ["Performance", "Database", "Network", "Application"])
        st.selectbox("* Impact", ["3 - Low", "2 - Medium", "1 - High"], index=0)
        st.selectbox("* Urgency", ["3 - Low", "2 - Medium", "1 - High"], index=0)
        
    with col2:
        st.text_input("Opened", value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), disabled=True)
        st.selectbox("State", ["New", "Work In Progress", "Pending", "Resolved", "Closed"], index=1)
        st.selectbox("* Substate", ["Third Party", "Awaiting User Info", "Awaiting Change"])
        st.selectbox("* Source", ["Phone", "Web", "Email", "Monitoring"], index=3)
        st.selectbox("* Support Level", ["Tier 1", "Tier 2", "Tier 3"], index=1)
        st.text_input("Assignment group", value="GTST FAST")
        st.text_input("* Assigned to", value="AI Copilot (Sysops)")

    # New section for the Short Description and Detailed Description
    st.text_input("Short Description", value=t_issue)
    st.text_area("Detailed Description", value=t_desc, height=100)

    st.divider()

    # --- 4. TABS FOR NOTES & AI ANALYSIS ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 AI Sysops Analysis (Work Notes)", 
        "📝 Manual Work Notes", 
        "🗣️ Additional/Customer Visible Notes", 
        "✅ Resolution & Closure"
    ])

    with tab1:
        st.subheader("AI Automated Diagnostics")
        st.caption("AI updates internal work notes strictly using Sysops Templates.")
        
        if "messages" not in st.session_state or not st.session_state.messages:
            # We now pass BOTH the Short Issue and the Detailed Description to the AI
            system_prompt = f"""You are an AIOps Copilot handling ticket {t_id}.
            Reported Issue: "{t_issue}"
            Detailed Description: "{t_desc}"
            Historical DB: {read_history()}
            
            INSTRUCTIONS:
            First, determine if the User Input is a technical IT incident or a general knowledge/chat question.
            
            IF IT IS A GENERAL KNOWLEDGE OR CHAT QUESTION (e.g., movies, actors, weather, greetings):
            Answer the question normally and naturally. DO NOT output the Initial Notes Template.
            
            IF IT IS A TECHNICAL IT INCIDENT:
            Format your response STRICTLY using this exact template:
            
            ----Initial Notes Template----
            Initial Symptoms/Issue Reported: {t_issue} - {t_desc}
            Sysops Analysis: <Your analysis>
            Root Cause Hypothesis/Cause: <Your hypothesis based on the DB or general IT knowledge>
            Supporting Data: <Reference specific DB tickets, or if none match, write exactly: "No related historical incidents found.">
            """
            
            st.session_state.messages = [{"role": "system", "content": system_prompt}]
            
            with st.spinner("Running initial diagnostics & generating Initial Notes Template..."):
                response = ollama.chat(model='llama3.2', messages=st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": response['message']['content']})

        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if user_input := st.chat_input("Prompt AI to generate Case Notes or analyze logs..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
                
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    if "update" in user_input.lower() or "case notes" in user_input.lower():
                        st.session_state.messages.append({"role": "system", "content": f"Format your next response strictly using this template:\n{CASE_TEMPLATE}"})
                    
                    response = ollama.chat(model='llama3.2', messages=st.session_state.messages)
                    reply = response['message']['content']
                    st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

    with tab2:
        st.subheader("Manual Work Notes (Internal)")
        st.text_area("Update Case Notes", value=CASE_TEMPLATE, height=300)
        st.button("Post Work Note")

    with tab3:
        st.subheader("Additional Notes (Customer Visible)")
        st.info("Notes entered here will be visible to the Impacted User on the portal.")
        st.text_area("Message to Customer:", placeholder="Hello Priya, we are currently investigating the issue...", height=150)
        st.button("Post Customer Note")

    with tab4:
        st.subheader("Resolve Incident")
        with st.form("resolve_form", clear_on_submit=True):
            res_notes = st.text_area("Resolution Notes", value=RESOLUTION_TEMPLATE, height=400)
            if st.form_submit_button("Resolve Ticket & Train Copilot") and res_notes:
                # Save the short issue to history so it's clean and concise
                resolve_ticket(t_id, t_issue, "Resolution notes updated via SNOW dashboard.")
                st.session_state.current_ticket = None
                st.session_state.messages = []
                st.rerun()
else:
    st.success("Queue is empty. Use the sidebar to create a new ticket.")