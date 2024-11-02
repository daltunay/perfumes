import logging
from sqlmodel import select

from database import get_session, init_db
from models import Product
from scraper import ProductScraper, get_all_slugs

logger = logging.getLogger(__name__)


def fetch_products() -> list[Product]:
    """Fetch products and save to database"""
    # Ensure database is initialized
    init_db()
    
    session_generator = get_session()
    session = next(session_generator)

    try:
        # Fix: Get slugs directly as a set of strings
        existing_slugs = set(session.exec(select(Product.slug)).all())

        new_slugs = set(get_all_slugs()) - existing_slugs
        logger.info(f"Found {len(new_slugs)} new products to fetch")

        products_added = 0
        for slug in new_slugs:
            try:
                scraper = ProductScraper(slug)
                product = Product.from_scrape(scraper.scrape())
                session.add(product)
                logger.info(f"Fetched product {slug}")
                products_added += 1

                if products_added % 10 == 0:
                    session.commit()
                    logger.info(f"Saved {products_added} products")

            except Exception as e:
                logger.error(f"Failed to fetch product {slug}: {e}")

        session.commit()
        return session.exec(select(Product)).all()
    finally:
        try:
            next(session_generator, None)
        except StopIteration:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_products()
