import json
import os
import sqlite3

def create_cookie_database(json_input_file, db_output_file):
    # 1. SAFETY GUARD: Stop if the database file already exists
    if os.path.exists(db_output_file):
        print(f"Error: Database file '{db_output_file}' already exists at:\n{db_output_file}\nAborting to prevent overwrite.")
        return

    # 2. INPUT CHECK: Ensure the source tagged file exists
    if not os.path.exists(json_input_file):
        print(f"Error: Input JSON file not found at:\n{json_input_file}\nPlease ensure level 2 cleanup ran successfully.")
        return

    print(f"Reading tagged records from:\n{json_input_file}...")
    with open(json_input_file, 'r', encoding='utf-8') as f:
        records = json.load(f)

    print(f"Connecting to SQLite database:\n{db_output_file}")
    conn = sqlite3.connect(db_output_file)
    cursor = conn.cursor()

    # Schema using a single text column for allergenTags
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cookies (
            fdcId INTEGER PRIMARY KEY,
            description TEXT,
            brandedFoodCategory TEXT,
            ingredients TEXT,
            allergenTags TEXT
        )
    """)

    print("Inserting data records into database...")
    insert_query = """
        INSERT OR REPLACE INTO cookies (
            fdcId, description, brandedFoodCategory, ingredients, allergenTags
        ) VALUES (?, ?, ?, ?, ?)
    """

    inserted_count = 0
    for record in records:
        fdc_id = record.get("fdcId")
        desc = record.get("description")
        category = record.get("brandedFoodCategory")
        ingredients = record.get("ingredients")
        tags_json_str = json.dumps(record.get("allergenTags", {}))
        
        data_tuple = (fdc_id, desc, category, ingredients, tags_json_str)
        cursor.execute(insert_query, data_tuple)
        inserted_count += 1

    conn.commit()
    conn.close()
    print(f"Success! Created database table 'cookies' with {inserted_count} rows.")

if __name__ == "__main__":
    # Get the absolute path of the directory containing THIS script (src folder)
    SRC_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Navigate up one level from 'src' to 'RuleBased', then into 'output'
    OUTPUT_DIR = os.path.abspath(os.path.join(SRC_DIR, "..", "output"))
    
    # Dynamically create the output directory if it doesn't exist yet
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Set strict absolute paths for input and output files
    INPUT_FILE = os.path.join(OUTPUT_DIR, "CookieAllergenTagged.json")
    OUTPUT_DB = os.path.join(OUTPUT_DIR, "CookieIntelligence.db")

    create_cookie_database(INPUT_FILE, OUTPUT_DB)

