import json
import os
import ijson
from decimal import Decimal
from datetime import datetime

# Custom encoder to handle ijson's high-precision Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Converts high-precision Decimal to standard JSON float
        return super(DecimalEncoder, self).default(obj)

def cleanup_food_data(input_filename, output_filename, report_filename, target_category):
    if os.path.exists(output_filename):
        print(f"Error: Output file '{output_filename}' already exists. Aborting.")
        return

    if not os.path.exists(input_filename):
        print(f"Error: Input file '{input_filename}' not found.")
        return

    matched_records = []
    total_scanned = 0
    unique_categories = set()

    print(f"Streaming USDA dataset using ijson from '{input_filename}'...")
    print(f"Targeting category: '{target_category}'")

    try:
        with open(input_filename, 'rb') as f:
            parser = ijson.items(f, 'BrandedFoods.item')
            
            for record in parser:
                total_scanned += 1
                cat = record.get("brandedFoodCategory")
                
                if cat:
                    unique_categories.add(cat)
                if cat == target_category:
                    matched_records.append(record)
                
                if total_scanned % 50000 == 0:
                    print(f"Scanned {total_scanned} records...")

    except ijson.common.IncompleteJSONError:
        print("Warning: JSON file seems truncated. Processing what was read.")
    except Exception as e:
        print(f"Retrying with alternative array paths due to: {e}")
        try:
            with open(input_filename, 'rb') as f:
                parser = ijson.items(f, 'SurveyFoods.item')
                matched_records, total_scanned, unique_categories = process_ijson_stream(parser, target_category)
        except Exception as inner_e:
            print(f"Fatal Error parsing USDA JSON schema: {inner_e}")
            return

    # Write the matching elements to file using our custom DecimalEncoder
    print("Encoding and saving matched records to output file...")
    with open(output_filename, 'w', encoding='utf-8') as out_f:
        json.dump(matched_records, out_f, cls=DecimalEncoder, indent=4)
        
    # Write summary statistics report
    with open(report_filename, 'w', encoding='utf-8') as rep_f:
        rep_f.write("=========================================\n")
        rep_f.write("        FIRST LEVEL CLEANUP REPORT       \n")
        rep_f.write("=========================================\n")
        rep_f.write(f"Execution Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        rep_f.write(f"Source Input File:   {input_filename}\n")
        rep_f.write(f"Cleaned Output File: {output_filename}\n")
        rep_f.write(f"Target Category:     {target_category}\n")
        rep_f.write("-----------------------------------------\n")
        rep_f.write(f"Total USDA Records Scanned:  {total_scanned}\n")
        rep_f.write(f"Total Target Extracted:      {len(matched_records)}\n")
        rep_f.write(f"Total Unique Categories:     {len(unique_categories)}\n")
        rep_f.write("=========================================\n")

    print(f"\nSuccess! Scanned {total_scanned} items.")
    print(f"Saved {len(matched_records)} matching items to '{output_filename}'.")
    print(f"Report written to '{report_filename}'.")

def process_ijson_stream(parser, target_category):
    matched = []
    scanned = 0
    categories = set()
    for record in parser:
        scanned += 1
        cat = record.get("brandedFoodCategory")
        if cat: categories.add(cat)
        if cat == target_category:
            matched.append(record)
    return matched, scanned, categories

if __name__ == "__main__":
    INPUT_FILE = "C:\\Users\\auj01\\Downloads\\AkshyaPatra\\3.AkshyaPatra\\Phase1_Food_Intelligence\\RuleBased\\rawdata\\FoodData_Central_branded_food_json_2026-04-30.json"  # Replace with your actual input file name
    OUTPUT_FILE = "Phase1_Food_Intelligence\\RuleBased\\output\\cookiesjuly2026.json"
    REPORT_FILE = "Phase1_Food_Intelligence\\RuleBased\\output\\cookiesjuly2026_report.txt"
    TARGET = "Cookies & Biscuits"
    cleanup_food_data(INPUT_FILE, OUTPUT_FILE, REPORT_FILE, TARGET)
