import re

import requests
from bs4 import BeautifulSoup, PageElement, ResultSet


def get_all_slugs() -> list[str]:
    BASE_URL = "https://pellwall.com/collections/ingredients-for-perfumery"

    session = requests.Session()
    slugs, page = [], 1

    while True:
        page_url = f"{BASE_URL}?page={page}"
        with session.get(page_url) as response:
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

        products = soup.find_all(
            "div", class_="wishlist-hero-custom-button wishlisthero-floating"
        )

        if not products:
            break

        for product in products:
            slug = product["data-wlh-link"].replace("/products/", "").split("?")[0]
            slugs.append(slug)

        page += 1

    return slugs


def extract_infos_from_details(details: ResultSet[PageElement]) -> dict[str, list[str]]:
    raw_details = {}
    for detail in details:
        if not (strong_tag := detail.find("strong")):
            continue
        key = strong_tag.get_text().rstrip(":")
        value = (
            " ".join([text.strip() for text in detail.find_all(text=True)])
            .split(":")[-1]
            .replace(key, "")
            .strip()
        )
        raw_details[key] = value

    def split_and_lower(value: str) -> list[str]:
        return [item.lower().strip() for item in value.replace("; ", ", ").split(", ")]

    return {
        "cas_no": split_and_lower(raw_details.get("CAS No.", "")),
        "odour": split_and_lower(
            raw_details.get("Odour (decreasing)", "").split(".")[0]
        ),
        "solvent": (
            solvent if "none" not in (solvent := raw_details.get("Solvent", "")) else ""
        ),
        "synonyms": split_and_lower(raw_details.get("Main Synonyms", "")),
        "manufacturer": raw_details.get("Manufacturer", ""),
    }


def extract_infos_from_slug(slug: str) -> dict[str, str]:
    BASE_URL = "https://pellwall.com/products"
    product_url = f"{BASE_URL}/{slug}"

    with requests.get(product_url) as response:
        response.raise_for_status()
        soup = BeautifulSoup(response.content.decode("utf-8", "ignore"), "html.parser")

    product_infos = soup.find(
        "div",
        id="ProductInfo-template--15936675938552__main",
        class_="product__info-container product__info-container--sticky",
    )

    product_name = (
        soup.find("div", class_="product__title").find("h1").get_text(strip=True)
    )

    product_slug = product_url.rstrip("/").split("/")[-1]

    product_type = (
        product_infos.find(
            "div", class_=re.compile(r"product-type-badge product-type-badge-")
        )
        .find("a")
        .get_text(strip=True)
        .lower()
    )

    product_raw_details = product_infos.find("hr").find_next_siblings("p")
    product_details = extract_infos_from_details(product_raw_details)

    product_description = soup.find(
        "div", class_="product__description rte quick-add-hidden"
    )

    product_tags = [
        a["href"].split("/collections/all/")[1]
        for a in product_description.find("i", class_="fa fa-tags").find_next_siblings(
            "a"
        )
    ]

    return {
        "product_name": product_name,
        "product_url": product_url,
        "product_slug": product_slug,
        "product_type": product_type,
        "product_tags": product_tags,
        **product_details,
    }
