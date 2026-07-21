import json
import os
import sqlite3
import ijson
import re
from decimal import Decimal
from datetime import datetime

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to convert ijson Decimal objects to floats."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class UniversalFoodIntelPipeline:
    def __init__(self, target_category=None, input_filename="input_food_data.json"):
        """
        Initialize a fully dynamic, non-hardcoded data processing pipeline.
        
        Args:
            target_category (str): The exact text match for brandedFoodCategory.
                                   Pass None to process the entire dataset.
            input_filename (str): The name of your source data download file.
        """
        # 1. Base Directory Setup
        self.src_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = os.path.abspath(os.path.join(self.src_dir, "..", "output"))
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.input_file = os.path.abspath(os.path.join(self.src_dir, "..", input_filename))
        self.target_category = target_category

        # 2. Dynamic Filenaming (Slugification Strategy)
        if self.target_category:
            clean_slug = re.sub(r'[^a-zA-Z0-9_]', '', self.target_category.lower().replace(' ', '_')).strip('_')
            clean_slug = clean_slug[:30]
        else:
            clean_slug = "all_foods"

        # 3. Dynamic Assignment of Object Path Attributes
        self.level1_json = os.path.join(self.output_dir, f"{clean_slug}_extracted.json")
        self.level1_report = os.path.join(self.output_dir, f"{clean_slug}_extraction_report.txt")
        self.level2_json = os.path.join(self.output_dir, f"{clean_slug}_allergen_tagged.json")
        self.level3_db = os.path.join(self.output_dir, f"{clean_slug}_intelligence.db")

        # 4. Master Allergen Taxonomy Dictionary
        self.allergen_dict = {
            "Milk": ["milk", "dairy", "butter", "cream", "whey", "lactose", "casein", "caseinate", "yogurt", "cheese", "ghee", "buttermilk", "curd", "kefir", "lactalbumin", "lactoglobulin",],
            "Wheat": ["wheat", "flour", "semolina", "spelt", "kamut", "triticale"],
            "Eggs": ["egg", "albumen", "ovalbumin", "yolk"],
            "Sesame": ["sesame", "tahini", "benne", "gingelly", "til"],
            "Tree nuts": ["cashew", "pistachio", "pecan", "almond", "walnut", "hazelnut", "macadamia", "chestnut", "brazil nut", "hickory"],
            "Peanuts": ["peanut", "arachis"],
            "Soy": ["soy", "soya", "soybean", "lecithin", "tofu", "edamame"]
        }
    def level1_cleanup(self):
        """LEVEL 1: Dynamic dataset scanner. Filters by category OR extracts everything."""
        print(f"\n--- RUNNING LEVEL 1 CLEANUP [{os.path.basename(self.level1_json)}] ---")
        if os.path.exists(self.level1_json):
            print("Skipping: Level 1 file already exists.")
            return True

        if not os.path.exists(self.input_file):
            print(f"Error: Base file not found at '{self.input_file}'.")
            return False

        matched_records = []
        total_scanned = 0
        unique_categories = set()

        try:
            with open(self.input_file, 'rb') as f:
                parser = ijson.items(f, 'BrandedFoods.item')
                for record in parser:
                    total_scanned += 1
                    cat = record.get("brandedFoodCategory")
                    if cat:
                        unique_categories.add(cat)
                    
                    # Core change: if no category string is passed, fetch EVERYTHING
                    if self.target_category is None or cat == self.target_category:
                        matched_records.append(record)

                    if total_scanned % 50000 == 0:
                        print(f"Scanned {total_scanned} records...")
        except Exception as e:
            print(f"Error during streaming operations: {e}")
            return False

        with open(self.level1_json, 'w', encoding='utf-8') as out_f:
            json.dump(matched_records, out_f, cls=DecimalEncoder, indent=4)

        with open(self.level1_report, 'w', encoding='utf-8') as rep_f:
            rep_f.write(f"Universal Extraction Report\nTotal Scanned: {total_scanned}\nTotal Extracted: {len(matched_records)}\n")

        print(f"Success! Stored {len(matched_records)} records.")
        return True

    def _scan_ingredients(self, ingredients_text):
        """Internal Helper: Runs strict regex scans across the ingredient block string."""
        if not ingredients_text:
            return {allergen: "N" for allergen in self.allergen_dict}

        text_lower = ingredients_text.lower()
        flags = {}

        for allergen, keywords in self.allergen_dict.items():
            matched = False
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r's?\b'
                if re.search(pattern, text_lower):
                    matched = True
                    break
            flags[allergen] = "Y" if matched else "N"

        # Apply Non-Dairy Exclusions
        if flags["Milk"] == "Y":
            all_milk_mentions = re.findall(r'\b(milk|butter)s?\b', text_lower)
            cocoa_butter_count = text_lower.count("cocoa butter")
            coconut_milk_count = text_lower.count("coconut milk")
            total_exclusions = cocoa_butter_count + coconut_milk_count

            if len(all_milk_mentions) <= total_exclusions:
                remaining = [k for k in self.allergen_dict["Milk"] if k not in ["milk", "butter"]]
                still_has_dairy = any(re.search(r'\b' + re.escape(k) + r's?\b', text_lower) for k in remaining)
                if not still_has_dairy:
                    flags["Milk"] = "N"

        return flags
    def level2_cleanup(self):
        """LEVEL 2: Core rule evaluator loop."""
        print(f"\n--- RUNNING LEVEL 2 CLEANUP [{os.path.basename(self.level2_json)}] ---")
        if os.path.exists(self.level2_json):
            print("Skipping: Level 2 file already exists.")
            return True

        if not os.path.exists(self.level1_json):
            print("Error: Input level 1 missing.")
            return False

        with open(self.level1_json, 'r', encoding='utf-8') as f:
            records = json.load(f)

        tagged_records = []
        for record in records:
            ingredients = record.get("ingredients", "")
            allergen_flags = self._scan_ingredients(ingredients)

            tagged_records.append({
                "fdcId": record.get("fdcId"),
                "description": record.get("description"),
                "brandedFoodCategory": record.get("brandedFoodCategory"),
                "ingredients": ingredients,
                "allergenTags": allergen_flags
            })

        with open(self.level2_json, 'w', encoding='utf-8') as out_f:
            json.dump(tagged_records, out_f, indent=4)

        print(f"Success! Tagged {len(tagged_records)} elements.")
        return True

    def level3_cleanup(self):
        """LEVEL 3: Populates target table rows using naming variables dynamically."""
        print(f"\n--- RUNNING LEVEL 3 CLEANUP [{os.path.basename(self.level3_db)}] ---")
        if os.path.exists(self.level3_db):
            print("Skipping: Level 3 database already exists.")
            return True

        if not os.path.exists(self.level2_json):
            print("Error: Input level 2 missing.")
            return False

        with open(self.level2_json, 'r', encoding='utf-8') as f:
            records = json.load(f)

        conn = sqlite3.connect(self.level3_db)
        cursor = conn.cursor()

        # The table is always named 'food_intelligence' to keep it completely generic
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_intelligence (
                fdcId INTEGER PRIMARY KEY,
                description TEXT,
                brandedFoodCategory TEXT,
                ingredients TEXT,
                allergenTags TEXT
            )
        """)

        insert_query = "INSERT OR REPLACE INTO food_intelligence VALUES (?, ?, ?, ?, ?)"
        for record in records:
            tags_str = json.dumps(record.get("allergenTags", {}))
            cursor.execute(insert_query, (
                record.get("fdcId"),
                record.get("description"),
                record.get("brandedFoodCategory"),
                record.get("ingredients"),
                tags_str
            ))

        conn.commit()
        conn.close()
        print("Success! Populated database table columns smoothly.")
        return True

    def execute_full_pipeline(self):
        """Pipeline orchestration loop execution manager."""
        print("\n" + "="*60)
        print("     UNIVERSAL OBJECT-ORIENTED DATA PIPELINE RUN     ")
        print("="*60)
        start_time = datetime.now()
        
        if self.level1_cleanup() and self.level2_cleanup() and self.level3_cleanup():
            print("\n" + "="*60)
            print(f"🎉 SUCCESS! Database created at:\n{self.level3_db}")
            print(f"Processing duration: {datetime.now() - start_time}")
            print("="*60 + "\n")


if __name__ == "__main__":
    # Test Case: To process ONLY "Cookies & Biscuits" datasets:
    pipeline = UniversalFoodIntelPipeline(target_category="Cookies & Biscuits")
    pipeline.execute_full_pipeline()
