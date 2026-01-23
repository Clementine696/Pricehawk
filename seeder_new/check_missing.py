import pandas as pd
import json

# Check HomePro
print("Checking HomePro...")
df = pd.read_excel('part1/twd_homepro_match_result_v1.1.0.xlsx')
with open('data/homepro.json', encoding='utf-8') as f:
    hp_data = json.load(f)
    hp_skus = {p['sku'] for p in hp_data}

skipped = []
for _, row in df.iterrows():
    comp_sku = str(int(row['COMPETITOR_SKU'])) if pd.notna(row['COMPETITOR_SKU']) else None
    if comp_sku and comp_sku not in hp_skus:
        skipped.append(comp_sku)

print(f"Total matches in Excel: {len(df)}")
print(f"Total SKUs in JSON: {len(hp_skus)}")
print(f"Skipped (not in JSON): {len(skipped)}")
print(f"\nFirst 10 missing SKUs:")
for sku in skipped[:10]:
    print(f"  - {sku}")
