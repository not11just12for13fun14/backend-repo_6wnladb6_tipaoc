import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from schemas import Product as ProductSchema
from database import create_document, get_documents, db

app = FastAPI(title="E-Commerce API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
    image: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "E-Commerce Backend Running"}

@app.get("/api/products")
def list_products(limit: int = 20):
    try:
        items = get_documents("product", {}, limit)
        # Normalize _id to string
        for it in items:
            it["id"] = str(it.pop("_id"))
        return {"items": items}
    except Exception as e:
        # Provide graceful fallback if DB not available
        sample = [
            {
                "id": "sample-1",
                "title": "Glass Card Pro",
                "description": "Minimalist translucent credit card with NFC.",
                "price": 129.0,
                "category": "Fintech",
                "in_stock": True,
                "image": "https://images.unsplash.com/photo-1556745753-b2904692b3cd?q=80&w=1200&auto=format&fit=crop"
            },
            {
                "id": "sample-2",
                "title": "Neo Wallet",
                "description": "Slim carbon fiber wallet for modern life.",
                "price": 79.0,
                "category": "Accessories",
                "in_stock": True,
                "image": "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=1200&auto=format&fit=crop"
            },
            {
                "id": "sample-3",
                "title": "Arc Charger",
                "description": "MagSafe fast charger with matte finish.",
                "price": 39.0,
                "category": "Gadgets",
                "in_stock": True,
                "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?q=80&w=1200&auto=format&fit=crop"
            },
        ]
        return {"items": sample, "note": "database_unavailable_fallback"}

@app.post("/api/products", status_code=201)
def create_product(product: ProductCreate):
    # Validate against schema fields using ProductSchema (not strictly required for insert)
    try:
        data = product.model_dump()
        new_id = create_document("product", data)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, "name", None) or "Unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
