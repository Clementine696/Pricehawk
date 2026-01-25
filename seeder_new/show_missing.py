import pandas as pd
import json

# Check all retailers
retailers = {
    'HomePro': ('twd_homepro_match_result_v1.1.0.xlsx', 'homepro.json'),
    'DoHome': ('twd_dohome_match_result_v1.1.0.xlsx', 'dohome.json'),
    'Boonthavorn': ('twd_boonthavorn_match_result_v1.1.0.xlsx', 'boonthavorn.json'),
    'GlobalHouse': ('twd_globalhouse_match_result_v1.1.0.xlsx', 'globalhouse.json'),
    'MegaHome': ('twd_megahome_match_result_v1.1.0.xlsx', 'megahome.json'),
}

for name, (excel_file, json_file) in retailers.items():
    print(f"\n{'='*70}")
    print(f"{name}")
    print('='*70)
    
    # Load Excel
    df = pd.read_excel(f'part1/{excel_file}')
    df_top5 = df.sort_values(['TWD_SKU', 'RANK']).groupby('TWD_SKU').head(5)
    
    # Load JSON
    with open(f'data/{json_file}', encoding='utf-8') as f:
        products = json.load(f)
        json_skus = {p['sku'] for p in products}
    
    # Find missing
    missing = []
    for _, row in df_top5.iterrows():
        comp_sku = str(int(row['COMPETITOR_SKU'])) if pd.notna(row['COMPETITOR_SKU']) else None
        if comp_sku and comp_sku not in json_skus:
            missing.append({
                'sku': comp_sku,
                'name': row.get('COMPETITOR_NAME', 'N/A'),
                'link': row.get('COMPETITOR_LINK', 'N/A'),
                'twd_sku': str(int(row['TWD_SKU'])),
            })
    
    print(f"Total matches (top 5): {len(df_top5)}")
    print(f"Total SKUs in JSON: {len(json_skus)}")
    print(f"Missing from JSON: {len(missing)}")
    
    if missing:
        print(f"\nFirst 5 missing SKUs:")
        for item in missing[:5]:
            print(f"\n  TWD SKU: {item['twd_sku']}")
            print(f"  Competitor SKU: {item['sku']}")
            print(f"  Name: {item['name']}")
            print(f"  Link: {item['link']}")
