import logging
from typing import List

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


def get_all_slugs() -> list[str]:
    """Fetch all product slugs from the catalog"""
    BASE_URL = "https://pellwall.com/collections/ingredients-for-perfumery"
    slugs, page = [], 1

    with requests.Session() as session:
        while True:
            page_url = f"{BASE_URL}?page={page}"
            response = session.get(page_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            products = soup.find_all(
                "div", class_="wishlist-hero-custom-button wishlisthero-floating"
            )
            if not products:
                break

            slugs.extend(
                product["data-wlh-link"].replace("/products/", "").split("?")[0]
                for product in products
            )
            page += 1

    return slugs


class ProductScraper:
    """Handles web scraping of product data"""

    BASE_URL = "https://pellwall.com/products"

    def __init__(self, slug: str):
        self.slug = slug
        self.url = f"{self.BASE_URL}/{slug}"
        self._soup = self._fetch_soup()

    @retry(stop=stop_after_attempt(10), wait=wait_fixed(1))
    def _fetch_soup(self) -> BeautifulSoup:
        response = requests.get(self.url)
        response.raise_for_status()
        return BeautifulSoup(response.content.decode("utf-8", "ignore"), "html.parser")

    def scrape(self) -> dict:
        """Scrape all product data at once"""
        try:
            return {
                "slug": self.slug,
                "url": self.url,
                "name": self._get_name(),
                "type": self._get_type(),
                "tags": self._get_tags(),
                "cas_no": self._get_cas_no(),
                "odour": self._get_odour(),
                "solvent": self._get_solvent(),
                "synonyms": self._get_synonyms(),
                "manufacturer": self._get_manufacturer(),
            }
        except Exception as e:
            logger.error(f"Failed to scrape product {self.slug}: {e}")
            raise

    def _get_name(self) -> str:
        return (
            self._soup.find("div", class_="product__title")
            .find("h1")
            .get_text(strip=True)
        )

    def _get_type(self) -> str | None:
        product_info_container = self._soup.find(
            "div",
            id="ProductInfo-template--15936675938552__main",
            class_="product__info-container product__info-container--sticky",
        )
        type_badge = product_info_container.find("div", class_="product-type-badge")
        if not type_badge:
            return None
        return type_badge.find("a").get_text(strip=True).lower()

    def _get_tags(self) -> List[str] | None:
        product_description = self._soup.find(
            "div", class_="product__description rte quick-add-hidden"
        )
        if not product_description:
            return None
        tags = [
            a["href"].split("/collections/all/")[1]
            for a in product_description.find(
                "i", class_="fa fa-tags"
            ).find_next_siblings("a")
        ]
        return tags if tags else None

    def _get_cas_no(self) -> List[str]:
        cas_no = self._extract_detail("CAS No.", split=True)
        return cas_no if cas_no and "n/a" not in "".join(cas_no).lower() else None

    def _get_odour(self) -> List[str]:
        odour = self._extract_detail("Odour (decreasing)", split=True, lower=True)
        for i, item in enumerate(odour):
            if "." in item:
                odour[i] = item.split(".")[0]
                return odour[: i + 1]
        return odour

    def _get_solvent(self) -> str | None:
        solvent_detail = self._extract_detail("Solvent")
        return (
            solvent_detail
            if solvent_detail
            and "none" not in solvent_detail.lower()
            and "n/a" not in solvent_detail.lower()
            else None
        )

    def _get_synonyms(self) -> List[str]:
        return self._extract_detail("Main Synonyms", split=True)

    def _get_manufacturer(self) -> str:
        return self._extract_detail("Manufacturer")

    def _extract_detail(
        self, key: str, split: bool = False, lower: bool = False
    ) -> List[str] | str:
        product_info_container = self._soup.find(
            "div",
            id="ProductInfo-template--15936675938552__main",
            class_="product__info-container product__info-container--sticky",
        )
        product_raw_details = product_info_container.find("hr").find_next_siblings("p")
        raw_details = {
            detail.find("strong")
            .get_text()
            .rstrip(":"): detail.get_text()
            .split(":")[-1]
            .strip()
            for detail in product_raw_details
            if detail.find("strong")
        }
        if lower:
            raw_details = {key: value.lower() for key, value in raw_details.items()}
        if split:
            return [
                item.strip()
                for item in raw_details.get(key, "")
                .replace(key, "")
                .replace("; ", ", ")
                .split(", ")
                if item.strip()
            ]
        return raw_details.get(key, "") or ""
