import re
from dataclasses import asdict, dataclass, field

import requests
from bs4 import BeautifulSoup, ResultSet, Tag


@dataclass
class Product:
    slug: str
    url: str = field(init=False)
    product_name: str = field(init=False, default=None)
    cas_no: str = field(init=False, default=None)
    odor: str = field(init=False, default=None)
    solvent: str = field(init=False, default=None)
    synonyms: str = field(init=False, default=None)
    description: str = field(init=False, default=None)
    tags: list[str] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.url = f"https://pellwall.com/products/{self.slug}/"
        product_name, product_infos, product_description = fetch_details(self.url)

        self.product_name = product_name.get_text(strip=True)
        for product_info in product_infos:
            if product_info.find(string="CAS No.") and not self.cas_no:
                self.cas_no = product_info.get_text().split("CAS No. ")[1]
            if product_info.find(string=re.compile("Odour")) and not self.odor:
                self.odor = (
                    product_info.get_text()
                    .rsplit(": ", 1)[1]
                    .split(".")[0]
                    .lower()
                    .split(", ")
                )
            if product_info.find(string=re.compile("Solvent")) and not self.solvent:
                solvent = product_info.get_text()
                self.solvent = (
                    solvent.split(": ")[1].lower()
                    if "none" not in solvent.lower()
                    else "N/A"
                )
            if product_info.find(string=re.compile("Synonyms")) and not self.synonyms:
                self.synonyms = (
                    product_info.get_text()
                    .split(": ")[1]
                    .lower()
                    .replace(";", ",")
                    .split(", ")
                )
            if product_info.find("i", class_="fa fa-tags") and not self.tags:
                self.tags = [
                    tag.get_text().lower() for tag in product_info.find_all("a")
                ]
            self.description = "\n ".join([p.get_text() for p in product_description])


def fetch_details(url: str) -> tuple[Tag, ResultSet]:
    response = requests.get(url)
    soup = BeautifulSoup(response.content.decode("utf-8", "ignore"), "html.parser")

    product_name = soup.find("div", class_="product__title").find("h1")
    product_infos = soup.find(
        "div", class_="product__info-container product__info-container--sticky"
    ).find_all("p")
    product_description = soup.find(
        "div", class_="product__description rte quick-add-hidden"
    ).find_all("p")

    return product_name, product_infos, product_description


def get_all_products() -> list[str]:
    BASE_URL = "https://pellwall.com/collections/ingredients-for-perfumery"

    session = requests.Session()
    product_slugs = []
    page = 1

    while True:
        response = session.get(f"{BASE_URL}?page={page}")
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        products = soup.find_all(
            "div", class_="wishlist-hero-custom-button wishlisthero-floating"
        )

        if not products:
            break

        for product in products:
            product_name = (
                product["data-wlh-link"].replace("/products/", "").split("?")[0]
            )
            product_slugs.append(product_name)

        page += 1

    return product_slugs


if __name__ == "__main__":
    import json

    for slug in get_all_products():
        try:
            product = Product(slug)
            print(json.dumps(asdict(product), indent=4))
        except Exception as e:
            print(f"Failed to fetch/parse {slug}: {e}")
