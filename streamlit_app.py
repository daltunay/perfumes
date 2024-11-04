import pandas as pd
import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Perfume Database", layout="wide", page_icon="🌸")
st.title("PellWall Perfume Ingredients Database", anchor=False)

# write about section: the database was build based on the PellWall website
# specify the URLs

with st.popover(label="About", icon="ℹ️"):
    st.markdown(
        """
        This is a database of perfume ingredients scraped from the [PellWall](https://pellwall.com) website.  
        The database is built using [FastAPI](https://fastapi.tiangolo.com) and [SQLModel](https://sqlmodel.tiangolo.com).  
        The data is scraped using [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) and [Requests](https://docs.python-requests.org).  
        The web app is built using [Streamlit](https://streamlit.io).
        """
    )


def show_catalog():
    st.header("Catalog", anchor=False)
    response = requests.get(f"{API_URL}/products/")
    response.raise_for_status()
    products = response.json()
    df = pd.DataFrame(products).sort_values("id").set_index("id")
    st.dataframe(df, use_container_width=True)


def show_search(df):
    st.header("Search", anchor=False)
    key_col, query_col, option_col = st.columns(3)

    by_column = key_col.selectbox(
        "Find by",
        ["cas_no", "name", "odour", "slug", "synonyms", "tags"],
        key="details_search_by",
        format_func=lambda x: x.replace("_", " ").title(),
        index=1,
    )

    search_results = pd.DataFrame()
    query = None

    # List-based columns
    if by_column in ["cas_no", "tags", "odour", "synonyms"]:
        query = query_col.multiselect(
            "Select one or several value(s)",
            sorted(df[by_column].explode().dropna().unique()),
            key="details_query",
            default=None,
        )
        option = option_col.radio(
            "Filter type",
            ["Contains any", "Contains all", "Exact match"],
            key="details_option",
            index=0,
            horizontal=True,
            help=f"- **Contains any**: the product contains any {by_column} in the chosen options  \n"
            f"- **Contains all**: the product contains all {by_column} in the chosen options  \n"
            f"- **Exact match**: the product contains only the {by_column} in the chosen options",
        )
        if query:
            if option == "Contains any":
                search_results = df[
                    df[by_column].apply(
                        lambda x: any(q in x for q in query) if x else False
                    )
                ]
            elif option == "Contains all":
                search_results = df[
                    df[by_column].apply(
                        lambda x: all(q in x for q in query) if x else False
                    )
                ]
            else:  # Exact match
                search_results = df[
                    df[by_column].apply(lambda x: set(x) == set(query) if x else False)
                ]

    # Text-based columns
    else:
        match_type = option_col.radio(
            "Match type",
            ["Exact", "Contains"],
            key="details_option",
            index=0,
            horizontal=True,
            help=f"- **Exact**: the product {by_column} matches the query exactly  \n"
            f"- **Contains**: the product {by_column} contains the query",
        )

        if match_type == "Exact":
            query = query_col.selectbox(
                "Select a value", df[by_column].unique(), key="details_query", index=None
            )
            if query:
                search_results = df[df[by_column] == query]
        else:
            query = query_col.text_input("Enter a value", key="details_query")
            if query:
                search_results = df[
                    df[by_column].str.contains(query, case=False, na=False)
                ]

    # Display results
    if not query:
        st.info(f"Please select a value for {by_column}")
    elif search_results.empty:
        st.warning("No results found")
    elif (n_results := search_results.shape[0]) > 50:
        st.warning(f"Too many results ({n_results}), please refine your search")
    else:
        st.dataframe(search_results.drop(columns="id"), use_container_width=True)
        slugs = sorted(search_results["slug"].values)
        for slug, tab in zip(slugs, st.tabs(slugs)):
            response = requests.get(f"{API_URL}/products/{slug}")
            response.raise_for_status()
            product = response.json()
            tab.json(product)


tab1, tab2 = st.tabs(["Catalog", "Search"])
with tab1:
    show_catalog()
with tab2:
    response = requests.get(f"{API_URL}/products/")
    response.raise_for_status()
    df = pd.DataFrame(response.json()).sort_values("name")
    show_search(df)
