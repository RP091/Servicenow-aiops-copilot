import ollama
import time

# 1. Our "Historical Database" of old tickets and how they were fixed
historical_db = """
- INC-050 (Resolved): Memory leak in Node.js app caused by unclosed DB connections. Fix: Enforced connection pooling limits.
- INC-082 (Resolved): Linux OOM (Out of Memory) killer terminated Java process. Fix: Increased JVM heap size limit in config.
- INC-099 (Resolved): Python analytics script crashed with MemoryError. Fix: Switched to pandas chunksize processing to avoid loading massive CSVs into RAM.
"""

# 2. The brand new, unknown incident that just came in
new_incident = {
    "ticket": "INC-111", 
    "user": "Rohit", 
    "log": "CRITICAL: Python data processing container killed by OOM killer on worker-node-03."
}

print("🚨 ALERT: No automated playbook found for this issue.")
print(f"Spawning dedicated AI Chat Space for {new_incident['ticket']}...\n")
time.sleep(1.5)

print("=" * 60)
print(f"💬 AI INVESTIGATION SPACE: {new_incident['ticket']}")
print(f"Initial Log: {new_incident['log']}")
print("Type 'exit' or 'quit' to close this workspace.")
print("=" * 60)

# 3. Setup the AI's system prompt with the historical context and the new ticket info
messages = [
    {
        'role': 'system', 
        'content': f"""You are a Senior Site Reliability Engineer helping Rohit troubleshoot ticket {new_incident['ticket']}. 
        The current error is: '{new_incident['log']}'.
        Here is the historical database of past memory issues: {historical_db}.
        Compare the current error to the past incidents, suggest what the root cause might be, and ask Rohit for specific server data to confirm."""
    }
]

# 4. Fire the initial analysis from the AI automatically
print("\n🤖 Llama 3.2 is analyzing the ticket against historical data...")
response = ollama.chat(model='llama3.2', messages=messages)
reply = response['message']['content']
messages.append({'role': 'assistant', 'content': reply})
print(f"\nLlama 3.2:\n{reply}\n")

# 5. Start the interactive chat loop
while True:
    user_input = input("Rohit (You) ❯ ")
    
    if user_input.lower() in ['exit', 'quit']:
        print(f"\n🔒 Closing chat space for {new_incident['ticket']}. Ticket status set to: PENDING USER ACTION.")
        break
        
    messages.append({'role': 'user', 'content': user_input})
    
    print("🤖 Thinking...")
    response = ollama.chat(model='llama3.2', messages=messages)
    reply = response['message']['content']
    messages.append({'role': 'assistant', 'content': reply})
    
    print(f"\nLlama 3.2:\n{reply}\n")