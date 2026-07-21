import json
import os
import sqlite3
import urllib.request

# Configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:latest"

# ----------------------------------------------------
# AGENT TOOLS (Python Functions the AI can query)
# ----------------------------------------------------

def tool_get_random_cookie_ids(num_samples=3):
    """Tool: Fetches random cookie FDC IDs from our created database."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return "Error: Database file does not exist."
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT fdcId, description FROM cookies ORDER BY RANDOM() LIMIT ?;", (num_samples,))
    rows = cursor.fetchall()
    conn.close()
    return [{"fdcId": row[0], "description": row[1]} for row in rows]

def tool_read_database_record(fdc_id):
    """Tool: Reads a processed record and its allergen tags directly from our SQLite DB."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT description, ingredients, allergenTags FROM cookies WHERE fdcId = ?;", (fdc_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"description": row[0], "ingredients": row[1], "allergenTags": json.loads(row[2])}
    return f"Record {fdc_id} not found in our SQLite DB."

def tool_read_raw_json_record(fdc_id):
    """Tool: Searches for the original raw object inside cookiesjuly2026.json to compare headers."""
    json_path = get_json_path()
    if not os.path.exists(json_path):
        return "Error: cookiesjuly2026.json not found."
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for record in data:
            if record.get("fdcId") == int(fdc_id):
                return {
                    "description": record.get("description"),
                    "ingredients": record.get("ingredients"),
                    "brandedFoodCategory": record.get("brandedFoodCategory")
                }
    return f"Record {fdc_id} not found in the raw extracted JSON."

# ----------------------------------------------------
# AGENT CORE ORCHESTRATION ENGINE
# ----------------------------------------------------

def query_ollama(system_prompt, user_prompt):
    """Executes a chat session block with Ollama in strict structured mode."""
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.0}
    }
    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("message", {}).get("content", "").strip()
    except Exception as e:
        return f'{{"error": "Failed to connect to Ollama: {str(e)}"}}'

def run_autonomous_ai_audit():
    print("====================================================")
    print(f"   INITIALIZING AUTONOMOUS AI TESTING AGENT ({MODEL_NAME})  ")
    print("====================================================\n")

    # Step 1: Execute tool to get random validation targets
    print("[Agent Action] Querying database tool for random audit samples...")
    sample_targets = tool_get_random_cookie_ids(num_samples=3)
    if isinstance(sample_targets, str):
        print(sample_targets)
        return

    print(f"[Agent State] Targets locked. Auditing {len(sample_targets)} cookies.\n")

    system_instruction = (
        "You are an autonomous quality assurance AI agent. Your job is to verify data integrity "
        "by comparing the raw extracted JSON file properties against the final SQLite database table rows. "
        "Analyze the provided text files side by side and check if the information matches exactly without corruption. "
        "Also verify if the rule engine applied allergen definitions correctly.\n"
        "Exclusion validation rule: Cocoa Butter and Coconut Milk are NOT dairy (Milk: N).\n"
        "Output your final audit report in plain JSON format matching this schema:\n"
        '{"fdcId": 123, "data_match_status": "PASS/FAIL", "allergen_rule_status": "PASS/FAIL", "critical_notes": "text summary"}'
    )

    for idx, target in enumerate(sample_targets, 1):
        fdc_id = target["fdcId"]
        desc = target["description"]
        print(f"--- [Audit Row {idx}] Analyzing FDC ID: {fdc_id} | {desc[:40]} ---")

        # Step 2: Use tools to gather context parameters for the AI
        raw_json_context = tool_read_raw_json_record(fdc_id)
        processed_db_context = tool_read_database_record(fdc_id)

        # Build context payload string for Ollama
        user_prompt = f"""
        Please audit this food data record. Compare the raw data against the processed data.
        
        RAW SOURCE JSON DATA BLOCK:
        {json.dumps(raw_json_context, indent=2)}
        
        OUR PROCESSED SQLITE DATABASE BLOCK:
        {json.dumps(processed_db_context, indent=2)}
        
        Run two checks:
        1. Data Match Status: Ensure descriptions and ingredients text columns perfectly match.
        2. Allergen Rule Status: Ensure the allergen tags are accurate according to standard definitions and exclusions.
        """

        # Step 3: Run AI verification pass
        ai_analysis_output = query_ollama(system_instruction, user_prompt)

        try:
            audit_report = json.loads(ai_analysis_output)
            print(f"📈 AI Agent Evaluation Audit Report:")
            print(f"   - Data Integrity:  {audit_report.get('data_match_status')}")
            print(f"   - Allergen Rules:  {audit_report.get('allergen_rule_status')}")
            print(f"   - Critical Notes:  {audit_report.get('critical_notes')}\n")
        except Exception as e:
            print(f"⚠️ Agent output formatting error: {e}")
            print(f"   Raw Agent Output: {ai_analysis_output}\n")

    print("====================================================")
    print("             AI AGENT AUDIT RUN COMPLETED           ")
    print("====================================================")

# Path utilities to keep scripts isolated from terminal execution directory traps
def get_db_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output", "CookieIntelligence.db"))

def get_json_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output", "cookiesjuly2026.json"))

if __name__ == "__main__":
    run_autonomous_ai_audit()
import json
import os
import sqlite3
import urllib.request

# Configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:latest"

# ----------------------------------------------------
# AGENT TOOLS (Python Functions the AI can query)
# ----------------------------------------------------

def tool_get_random_cookie_ids(num_samples=3):
    """Tool: Fetches random cookie FDC IDs from our created database."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return "Error: Database file does not exist."
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT fdcId, description FROM cookies ORDER BY RANDOM() LIMIT ?;", (num_samples,))
    rows = cursor.fetchall()
    conn.close()
    return [{"fdcId": row[0], "description": row[1]} for row in rows]

def tool_read_database_record(fdc_id):
    """Tool: Reads a processed record and its allergen tags directly from our SQLite DB."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT description, ingredients, allergenTags FROM cookies WHERE fdcId = ?;", (fdc_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"description": row[0], "ingredients": row[1], "allergenTags": json.loads(row[2])}
    return f"Record {fdc_id} not found in our SQLite DB."

def tool_read_raw_json_record(fdc_id):
    """Tool: Searches for the original raw object inside cookiesjuly2026.json to compare headers."""
    json_path = get_json_path()
    if not os.path.exists(json_path):
        return "Error: cookiesjuly2026.json not found."
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for record in data:
            if record.get("fdcId") == int(fdc_id):
                return {
                    "description": record.get("description"),
                    "ingredients": record.get("ingredients"),
                    "brandedFoodCategory": record.get("brandedFoodCategory")
                }
    return f"Record {fdc_id} not found in the raw extracted JSON."

# ----------------------------------------------------
# AGENT CORE ORCHESTRATION ENGINE
# ----------------------------------------------------

def query_ollama(system_prompt, user_prompt):
    """Executes a chat session block with Ollama in strict structured mode."""
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.0}
    }
    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("message", {}).get("content", "").strip()
    except Exception as e:
        return f'{{"error": "Failed to connect to Ollama: {str(e)}"}}'

def run_autonomous_ai_audit():
    print("====================================================")
    print(f"   INITIALIZING AUTONOMOUS AI TESTING AGENT ({MODEL_NAME})  ")
    print("====================================================\n")

    # Step 1: Execute tool to get random validation targets
    print("[Agent Action] Querying database tool for random audit samples...")
    sample_targets = tool_get_random_cookie_ids(num_samples=3)
    if isinstance(sample_targets, str):
        print(sample_targets)
        return

    print(f"[Agent State] Targets locked. Auditing {len(sample_targets)} cookies.\n")

    system_instruction = (
        "You are an autonomous quality assurance AI agent. Your job is to verify data integrity "
        "by comparing the raw extracted JSON file properties against the final SQLite database table rows. "
        "Analyze the provided text files side by side and check if the information matches exactly without corruption. "
        "Also verify if the rule engine applied allergen definitions correctly.\n"
        "Exclusion validation rule: Cocoa Butter and Coconut Milk are NOT dairy (Milk: N).\n"
        "Output your final audit report in plain JSON format matching this schema:\n"
        '{"fdcId": 123, "data_match_status": "PASS/FAIL", "allergen_rule_status": "PASS/FAIL", "critical_notes": "text summary"}'
    )

    for idx, target in enumerate(sample_targets, 1):
        fdc_id = target["fdcId"]
        desc = target["description"]
        print(f"--- [Audit Row {idx}] Analyzing FDC ID: {fdc_id} | {desc[:40]} ---")

        # Step 2: Use tools to gather context parameters for the AI
        raw_json_context = tool_read_raw_json_record(fdc_id)
        processed_db_context = tool_read_database_record(fdc_id)

        # Build context payload string for Ollama
        user_prompt = f"""
        Please audit this food data record. Compare the raw data against the processed data.
        
        RAW SOURCE JSON DATA BLOCK:
        {json.dumps(raw_json_context, indent=2)}
        
        OUR PROCESSED SQLITE DATABASE BLOCK:
        {json.dumps(processed_db_context, indent=2)}
        
        Run two checks:
        1. Data Match Status: Ensure descriptions and ingredients text columns perfectly match.
        2. Allergen Rule Status: Ensure the allergen tags are accurate according to standard definitions and exclusions.
        """

        # Step 3: Run AI verification pass
        ai_analysis_output = query_ollama(system_instruction, user_prompt)

        try:
            audit_report = json.loads(ai_analysis_output)
            print(f"📈 AI Agent Evaluation Audit Report:")
            print(f"   - Data Integrity:  {audit_report.get('data_match_status')}")
            print(f"   - Allergen Rules:  {audit_report.get('allergen_rule_status')}")
            print(f"   - Critical Notes:  {audit_report.get('critical_notes')}\n")
        except Exception as e:
            print(f"⚠️ Agent output formatting error: {e}")
            print(f"   Raw Agent Output: {ai_analysis_output}\n")

    print("====================================================")
    print("             AI AGENT AUDIT RUN COMPLETED           ")
    print("====================================================")

# Path utilities to keep scripts isolated from terminal execution directory traps
def get_db_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output", "CookieIntelligence.db"))

def get_json_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output", "cookiesjuly2026.json"))

if __name__ == "__main__":
    run_autonomous_ai_audit()
