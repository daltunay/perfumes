from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from database import get_session, init_db
from fetch import fetch_products
from models import Product


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/products/", response_model=list[Product])
def get_products(session: Session = Depends(get_session)):
    return session.exec(select(Product)).all()


@app.get("/products/{slug}", response_model=Product)
def get_product(slug: str, session: Session = Depends(get_session)):
    if product := session.exec(select(Product).where(Product.slug == slug)).first():
        return product
    raise HTTPException(status_code=404, detail="Product not found")


@app.post("/fetch-products/")
def update_products():
    products = fetch_products()
    return {"message": f"Successfully fetched {len(products)} products"}
