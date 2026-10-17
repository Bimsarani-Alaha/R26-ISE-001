"""Print catalog diagnostics using the backend in this checkout."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from style_recommendation.repositories.catalog_repository import CatalogRepository


def main():
    df = CatalogRepository().load_dataset()
    print(f"Loaded {len(df)} products")
    print(f"Columns: {list(df.columns)}")
    print(f"Sample occasions: {df['occasion'].head(3).tolist()}")
    print(f"Gender values: {df['gender'].unique().tolist()}")
    print("Catalog repository OK!")


if __name__ == "__main__":
    main()
