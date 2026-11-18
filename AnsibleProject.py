import ollama
import subprocess
import time

# 1. Simulated Incident Queue (10 Tickets)
# 4 Web Crashes, 3 Disk Space Issues, 3 DB Connection Issues
incidents = [
    {"ticket": "INC-101", "user": "Rahul", "log": "CRITICAL: Nginx web service has crashed on node 1"},
    {"ticket": "INC-102", "user": "Priya", "log": "ERROR: Nginx dropping connections, 502 Bad Gateway"},
    {"ticket": "INC-103", "user": "Amit", "log": "FATAL: Web service on localhost unresponsive"},
    {"ticket": "INC-104", "user": "Sneha", "log": "ERROR: Nginx process died unexpectedly"},
    
    {"ticket": "INC-105", "user": "Vikram", "log": "ERROR: Disk space usage exceeded 95% on /var/log"},
    {"ticket": "INC-106", "user": "Karan", "log": "CRITICAL: No space left on device in /var/log"},
    {"ticket": "INC-107", "user": "Neha", "log": "ERROR: /var/log partition is full, cannot write"},
    
    {"ticket": "INC-108", "user": "Arjun", "log": "FATAL: Database connection pool exhausted"},
    {"ticket": "INC-109", "user": "Riya", "log": "ERROR: Unable to connect to DB, max connections reached"},
    {"ticket": "INC-110", "user": "Rohan", "log": "CRITICAL: Postgres connection timeout, pool full"}
]

print(f"📥 Pulled {len(incidents)} new incidents from the queue. Starting AIOps Triage...\n")
print("-" * 50)

# 2. Process each ticket automatically
for incident in incidents:
    print(f"🎫 Ticket: {incident['ticket']} | User: {incident['user']}")
    print(f"📝 Log: {incident['log']}")
    
    # Strict prompt to force the LLM into routing mode
    prompt = f"""
    You are an AIOps incident router. Analyze this server log: '{incident['log']}'.
    Map the log to exactly ONE of these playbook filenames:
    - If web service/Nginx crash: 'restart_service.yaml'
    - If disk space/partition full: 'clear_disk.yaml'
    - If database/connection pool: 'restart_db.yaml'
    
    Reply with ONLY the exact filename. Do not add quotes, markdown, or explanations.
    """

    # Fetch AI decision
    response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
    ai_decision = response['message']['content'].strip()
    
    print(f"🤖 AI Routing Decision: {ai_decision}")
    
    # 3. Execute the mapped playbook
    if ai_decision in ['restart_service.yaml', 'clear_disk.yaml', 'restart_db.yaml']:
        try:
            # Running Ansible silently, just grabbing the output message to keep terminal clean
            result = subprocess.run(
                ['ansible-playbook', ai_decision], 
                capture_output=True, text=True, check=True
            )
            print("✅ Status: RESOLVED via Automation")
        except subprocess.CalledProcessError as e:
            print(f"❌ Status: FAILED - {e.stderr}")
    else:
        print(f"⚠️ Status: ESCALATED TO HUMAN - AI could not determine playbook. Output was: {ai_decision}")
        
    print("-" * 50)
    time.sleep(2) # Brief pause so you can watch it process in real-time

print("🏁 Triage Complete. All routine incidents auto-remediated.")