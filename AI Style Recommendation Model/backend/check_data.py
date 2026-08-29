import csv

with open('C:/Users/sashi/OneDrive/Desktop/Research V3/data/product_full_updated.csv', 'r', encoding='utf-8') as f:
    data = list(csv.DictReader(f))

# Check neck_type column name
print("Columns:", list(data[0].keys()))

# Find sweetheart neck dresses
sw = [r for r in data if 'sweetheart' in r.get('neck_type','').lower() and 'dress' in r.get('article_type','').lower()]
print(f"\nSweetheart neck dresses: {len(sw)}")
for r in sw[:10]:
    print(f"  {r['product_id']}: {r['article_type']}, {r['base_colour']}, neck={r['neck_type']}")

# Check what neck_type the AI might parse as
print(f"\nNeck types in dataset (sample):")
neck_types = set(r.get('neck_type','') for r in data if 'dress' in r.get('article_type','').lower())
for nt in sorted(neck_types)[:20]:
    print(f"  '{nt}'")
