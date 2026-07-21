import sqlite3
import os

def interactive_allergen_query(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at:\n{db_path}")
        return

    # List of valid allergens for safety validation
    valid_allergens = ["Milk", "Wheat", "Eggs", "Sesame", "Tree nuts", "Peanuts", "Soy"]

    print("====================================================")
    print("         INTERACTIVE COOKIE ALLERGEN QUERY          ")
    print("====================================================")
    print("Available options: Milk, Wheat, Eggs, Sesame, Tree nuts, Peanuts, Soy")
    
    # 1. Dynamic User Input for Allergen Name
    target_allergen = input("Enter the allergen name to filter by: ").strip()
    
    # Simple formatting fix to match Title Case casing rules (e.g. "milk" -> "Milk")
    if target_allergen.lower() == "tree nuts":
        target_allergen = "Tree nuts"
    else:
        target_allergen = target_allergen.capitalize()

    if target_allergen not in valid_allergens:
        print(f"Error: '{target_allergen}' is not a tracked allergen in this database.")
        return

    # 2. Dynamic User Input for Status
    target_status = input(f"Should '{target_allergen}' be present? (Enter Y or N): ").strip().upper()
    if target_status not in ["Y", "N"]:
        print("Error: Invalid entry. Please choose either 'Y' or 'N'.")
        return

    # Connect and query the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Base string parameter path for json_extract, e.g., '$.Milk'
    json_path_param = f"$.{target_allergen}"

    # Query 1: Dynamic Count Summary
    count_query = """
        SELECT COUNT(*) 
        FROM cookies 
        WHERE json_extract(allergenTags, ?) = ?;
    """
    cursor.execute(count_query, (json_path_param, target_status))
    match_count = cursor.fetchone()[0]

    # Query 2: Dynamic Data Rows Preview
    preview_query = """
        SELECT fdcId, description, brandedFoodCategory, allergenTags
        FROM cookies 
        WHERE json_extract(allergenTags, ?) = ?
        LIMIT 15;
    """
    cursor.execute(preview_query, (json_path_param, target_status))
    preview_rows = cursor.fetchall()
    conn.close()

    # --- PRINT OUT TARGET GENERATED METRICS ---
    status_label = "FREE" if target_status == "N" else "CONTAINING"
    print("\n----------------------------------------------------")
    print(f"RESULTS FOR: Cookies {status_label} '{target_allergen}'")
    print(f"Total Matches Found: {match_count}")
    print("----------------------------------------------------")
    
    if match_count == 0:
        print("No cookie records matched your exact request constraints.")
        return

    print("PREVIEW (First 15 records matching your input):")
    print(f"{'fdcId':<10} | {'Description':<45} | {'Allergen Tags Object string'}")
    print("-" * 95)
    
    for row in preview_rows:
        fdc_id, desc, category, tags_str = row
        short_desc = desc[:42] + "..." if len(desc) > 42 else desc
        print(f"{fdc_id:<10} | {short_desc:<42} | {tags_str}")
    print("====================================================")

if __name__ == "__main__":
    # Calculate strict absolute paths relative to this script's directory location
    SRC_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_FILE = os.path.abspath(os.path.join(SRC_DIR, "..", "output", "CookieIntelligence.db"))

    interactive_allergen_query(DB_FILE)
