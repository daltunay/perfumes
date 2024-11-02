from sqlmodel import JSON, Field, SQLModel


class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(index=True)
    url: str
    name: str
    type: str | None = Field(default=None)
    tags: list[str] | None = Field(default=None, sa_type=JSON)
    cas_no: list[str] | None = Field(default=None, sa_type=JSON)
    odour: list[str] | None = Field(default=None, sa_type=JSON)
    solvent: str | None = Field(default=None)
    synonyms: list[str] | None = Field(default=None, sa_type=JSON)
    manufacturer: str | None = Field(default=None)

    @classmethod
    def from_scrape(cls, data: dict) -> "Product":
        # Convert empty strings and empty lists to None
        for key, value in data.items():
            if isinstance(value, str) and not value.strip():
                data[key] = None
            elif isinstance(value, list) and not value:
                data[key] = None
        return cls(**data)
