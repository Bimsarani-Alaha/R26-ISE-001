import sys
sys.path.insert(0, r"C:\Users\sashi\OneDrive\Desktop\Research V3\backend")

from app.services.product_service import product_service

df = product_service.load_dataset()
print(f"Loaded {len(df)} products")
print(f"Columns: {list(df.columns)}")
print(f"Sample occasions: {df['occasion'].head(3).tolist()}")
print(f"Gender values: {df['gender'].unique().tolist()}")
print("Product service OK!")
