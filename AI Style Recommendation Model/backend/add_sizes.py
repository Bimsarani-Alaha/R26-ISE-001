import csv
import random

path = 'C:/Users/sashi/OneDrive/Desktop/Research V3/data/product_full_updated.csv'

with open(path, 'r', encoding='utf-8') as f:
    data = list(csv.DictReader(f))
    fieldnames = data[0].keys()

extra_sizes = ['XXL', 'XXXL', 'XXXXL']

for row in data:
    if row.get('gender', '').lower() == 'women':
        current = row.get('available_sizes', '')
        if 'XXL' not in current and random.random() < 0.4:
            add = random.choice(extra_sizes)
            row['available_sizes'] = current + '/' + add if current else add

with open(path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

women = [r for r in data if r.get('gender','').lower() == 'women']
xxl = [r for r in women if 'XXL' in r.get('available_sizes','')]
xxxl = [r for r in women if 'XXXL' in r.get('available_sizes','')]
xxxxl = [r for r in women if 'XXXXL' in r.get('available_sizes','')]
print(f'Women: {len(women)}, XXL: {len(xxl)}, XXXL: {len(xxxl)}, XXXXL: {len(xxxxl)}')
