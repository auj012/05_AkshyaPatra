import json
import os
import sqlite3
import random
import ijson

def verify_against_raw_source(raw_usda_file, db_path, num_samples=3):
    if not os.path.exists(raw_usda_file):
        print(f"Error: Original raw source file not found at:\n{raw_usda_file}")
        return
    if not os.path.exists(db_path):
        print(f"Error: Processed SQLite DB not found at:\n{db_path}")
        return

    # 1. Connect to our created database and pick a few random records to audit
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT fdcId, description, ingredients, allergenTags FROM cookies")
    all_db_records = cursor.fetchall()
    conn.close()

    if not all_db_records:
        print("Your database table is empty. Run your cleanup pipeline first.")
        return

    sampled_records = random.sample(all_db_records, min(num_samples, len(all_db_records)))
    target_ids = {row[0]: row for row in sampled_records}

    print("======================================================================")
    print("      PIPELINE END-TO-END VERIFICATION: DB VS RAW SOURCE FILE         ")
    print("======================================================================\n")
    print(f"Streaming original source '{os.path.basename(raw_usda_file)}' to find matching records...\n")

    # 2. Stream through the massive original uncleaned file to pull the true original rows
    source_matches = {}
    try:
        with open(raw_usda_file, 'rb') as f:
            # Check BrandedFoods array just like in script 1
            parser = ijson.items(f, 'BrandedFoods.item')
            for record in parser:
                fdc_id = record.get("fdcId")
                if fdc_id in target_ids:
                    source_matches[fdc_id] = record
                    if len(source_matches) == len(target_ids):
                        break  # Stop streaming early if we found all our test samples
    except Exception as e:
        print(f"Error streaming raw file: {e}")
        return

    # 3. Print the comparison side-by-side so you can audit it perfectly
    for idx, fdc_id in enumerate(target_ids.keys(), 1):
        db_id, db_desc, db_ingredients, db_tags = target_ids[fdc_id]
        raw_record = source_matches.get(fdc_id)

        print(f"--- [AUDIT SAMPLE {idx}] FDC ID: {fdc_id} ---")
        
        if not raw_record:
            print("❌ ERROR: Record exists in your DB but was not found in the raw source file!")
            print("-" * 70 + "\n")
            continue

        # Extract values directly from the uncleaned source file
        raw_desc = raw_record.get("description")
        raw_ingredients = raw_record.get("ingredients")
        raw_category = raw_record.get("brandedFoodCategory")

        # Compare descriptions
        desc_status = "✅ MATCH" if db_desc == raw_desc else "❌ MISMATCH!"
        print(f"Description (Raw Source): {raw_desc}")
        print(f"Description (Our DB):     {db_desc} -> {desc_status}")
        
        # Compare categories
        cat_status = "✅ MATCH" if raw_category == "Cookies & Biscuits" else "❌ WARNING (Category Mismatch)"
        print(f"Category (Raw Source):    {raw_category} -> {cat_status}")

        # Compare raw text vs cleaned database column
        ing_status = "✅ MATCH" if db_ingredients == raw_ingredients else "❌ MISMATCH!"
        print(f"Ingredients (Raw Source): {raw_ingredients[:120]}...")
        print(f"Ingredients (Our DB):     {db_ingredients[:120]}... -> {ing_status}")

        # Show final generated tags for human confirmation
        print(f"Generated Allergen Tags:  {db_tags}")
        print("-" * 70 + "\n")

    print("======================================================================")
    print("                      VERIFICATION COMPLETE                           ")
    print("======================================================================")

if __name__ == "__main__":
    SRC_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = os.path.abspath(os.path.join(SRC_DIR, "..", "output"))

    # CONFIGURATION LINK MAPPINGS:
    # Change this path to point exactly to your massive uncleaned download file
    #RAW_USDA_DATASET = os.path.join(SRC_DIR, "..", "input_food_data.json") 
    RAW_USDA_DATASET = "C:\\Users\\auj01\\Downloads\\AkshyaPatra\\3.AkshyaPatra\\Phase1_Food_Intelligence\\RuleBased\\rawdata\\FoodData_Central_branded_food_json_2026-04-30.json"  # Replace with your actual input file name

    OUR_DATABASE = os.path.join(OUTPUT_DIR, "CookieIntelligence.db")

    verify_against_raw_source(RAW_USDA_DATASET, OUR_DATABASE, num_samples=3)
