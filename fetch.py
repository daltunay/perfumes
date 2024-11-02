import csv
import logging
import os
from typing import List

from product import Product, get_all_slugs

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def read_slugs_from_file(slugs_file_path: str) -> List[str]:
    logging.info(f"Reading slugs from {slugs_file_path}")
    with open(slugs_file_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file.readlines()]


def write_slugs_to_file(slugs: List[str], slugs_file_path: str):
    logging.info(f"Writing {len(slugs)} slugs to {slugs_file_path}")
    with open(slugs_file_path, "w", encoding="utf-8") as file:
        for slug in slugs:
            file.write(f"{slug}\n")


def fetch_products(slugs: List[str]) -> List[Product]:
    products = []
    failed_slugs = []
    total = len(slugs)

    logging.info(f"Starting to fetch {total} products")
    for i, slug in enumerate(slugs, 1):
        try:
            product = Product(slug)
            products.append(product)
            if i % 10 == 0:
                logging.info(f"Progress: {i}/{total} products fetched")
        except Exception as e:
            logging.error(f"Failed to fetch product {slug}: {str(e)}")
            failed_slugs.append(slug)
            continue

    if failed_slugs:
        logging.warning(f"Failed to fetch {len(failed_slugs)} products: {failed_slugs}")

    logging.info(f"Successfully fetched {len(products)} products")
    return products


def write_products_to_csv(products: List[Product], csv_file_path: str):
    logging.info(f"Writing {len(products)} products to {csv_file_path}")
    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        fieldnames = [
            "slug",
            "url",
            "name",
            "type",
            "tags",
            "cas_no",
            "odour",
            "solvent",
            "synonyms",
            "manufacturer",
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for product in products:
            writer.writerow(product.to_dict())


if __name__ == "__main__":
    csv_file_path = "assets/products.csv"
    slugs_file_path = "assets/slugs.txt"

    # Ensure assets directory exists
    os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

    if os.path.exists(slugs_file_path):
        slugs = read_slugs_from_file(slugs_file_path)
    else:
        logging.info("Fetching all slugs from website")
        slugs = get_all_slugs()
        write_slugs_to_file(slugs, slugs_file_path)

    products = fetch_products(slugs)
    write_products_to_csv(products, csv_file_path)
    logging.info("Process completed")
