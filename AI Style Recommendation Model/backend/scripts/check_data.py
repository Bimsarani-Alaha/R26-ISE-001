import argparse
from pathlib import Path
from style_recommendation.core.config import load_settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=load_settings().dataset_path)
    dataset_path = parser.parse_args().dataset
    import csv
    
    with open(str(dataset_path), 'r', encoding='utf-8') as f:
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


if __name__ == "__main__":
    main()
