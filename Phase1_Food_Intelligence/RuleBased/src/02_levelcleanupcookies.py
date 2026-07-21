import json
import os
import re

# Comprehensive dictionary mapping allergens strictly to their direct names/variants
ALLERGEN_DICT = {
    "Milk": [
        "milk", "butter", "cream", "whey", "lactose", "casein", "caseinate", 
        "yogurt", "cheese", "ghee", "buttermilk", "curd"
    ],
    "Wheat": [
        "wheat", "flour", "semolina", "spelt", "kamut", "triticale"
    ],
    "Eggs": [
        "egg", "albumen", "ovalbumin", "yolk"
    ],
    "Sesame": [
        "sesame", "tahini", "benne", "gingelly", "til"
    ],
    "Tree nuts": [
        "cashew", "pistachio", "pecan", "almond", "walnut", 
        "hazelnut", "macadamia", "chestnut", "brazil nut", "hickory"
    ],
    "Peanuts": [
        "peanut", "arachis"
    ],
    "Soy": [
        "soy", "soya", "soybean", "lecithin", "tofu", "edamame"
    ]
}

def scan_ingredients(ingredients_text):
    if not ingredients_text:
        return {allergen: "N" for allergen in ALLERGEN_DICT}
        
    text_lower = ingredients_text.lower()
    flags = {}
    
    # Process standard keyword checks with automatic plural matching
    for allergen, keywords in ALLERGEN_DICT.items():
        matched = False
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r's?\b'
            if re.search(pattern, text_lower):
                matched = True
                break
        flags[allergen] = "Y" if matched else "N"
        
    # --- NON-DAIRY EXCLUSION LOGIC ---
    if flags["Milk"] == "Y":
        all_milk_mentions = re.findall(r'\b(milk|butter)s?\b', text_lower)
        
        cocoa_butter_count = text_lower.count("cocoa butter")
        coconut_milk_count = text_lower.count("coconut milk")
        total_false_positives = cocoa_butter_count + coconut_milk_count
        
        if len(all_milk_mentions) <= total_false_positives:
            remaining_dairy_keywords = [k for k in ALLERGEN_DICT["Milk"] if k not in ["milk", "butter"]]
            still_has_dairy = any(re.search(r'\b' + re.escape(k) + r's?\b', text_lower) for k in remaining_dairy_keywords)
            
            if not still_has_dairy:
                flags["Milk"] = "N"
                
    return flags

def process_allergen_tagging(input_filename, output_filename):
    # 1. NEW GUARD CLAUSE: Stop execution if output file already exists
    if os.path.exists(output_filename):
        print(f"Error: Output file '{output_filename}' already exists. Aborting to prevent overwrite.")
        return

    # 2. Existing check: Ensure input data is present
    if not os.path.exists(input_filename):
        print(f"Error: Input file '{input_filename}' not found.")
        return

    print(f"Reading records from '{input_filename}'...")
    with open(input_filename, 'r', encoding='utf-8') as f:
        records = json.load(f)

    tagged_records = []
    print("Tagging allergens across dataset with strict name definitions...")

    for record in records:
        ingredients = record.get("ingredients", "")
        allergen_flags = scan_ingredients(ingredients)
        
        new_record = {
            "fdcId": record.get("fdcId"),
            "description": record.get("description"),
            "brandedFoodCategory": record.get("brandedFoodCategory"),
            "ingredients": ingredients,
            "allergenTags": allergen_flags
        }
        tagged_records.append(new_record)

    with open(output_filename, 'w', encoding='utf-8') as out_f:
        json.dump(tagged_records, out_f, indent=4)

    print(f"Success! Saved {len(tagged_records)} precisely tagged items to '{output_filename}'.")

if __name__ == "__main__":
    INPUT_FILE = os.path.join("Phase1_Food_Intelligence", "RuleBased", "output", "cookiesjuly2026.json")
    OUTPUT_FILE = os.path.join("Phase1_Food_Intelligence", "RuleBased", "output", "CookieAllergenTagged.json")

    if not os.path.exists(os.path.dirname(OUTPUT_FILE)) and os.path.dirname(OUTPUT_FILE) != "":
        OUTPUT_FILE = "CookieAllergenTagged.json"
        INPUT_FILE = "cookiesjuly2026.json"

    process_allergen_tagging(INPUT_FILE, OUTPUT_FILE)
