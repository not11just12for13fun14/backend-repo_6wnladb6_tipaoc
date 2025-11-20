import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from schemas import Product as ProductSchema, CartItem, Order
from database import create_document, get_documents, db

app = FastAPI(title="E-Commerce API", version="1.2.0")

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
    gallery: Optional[list[str]] = None
    specs: Optional[dict] = None

class AddToCart(BaseModel):
    client_id: str
    product_id: str
    qty: int = 1

class WishlistUpdate(BaseModel):
    client_id: str
    product_id: str

class CheckoutPayload(BaseModel):
    client_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: str
    payment_method: str = "COD"  # Only COD supported

# --- Sample catalog for fallback mode ---
SAMPLE_PRODUCTS = [
    {
        "id": "sample-1",
        "title": "Glass Card Pro",
        "description": "Minimalist translucent credit card with NFC.",
        "price": 129.0,
        "category": "Fintech",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1556745753-b2904692b3cd?q=80&w=1200&auto=format&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1556745753-b2904692b3cd?q=80&w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=1200&auto=format&fit=crop"
        ],
        "specs": {"Material": "Polycarbonate", "NFC": "Yes", "Finish": "Matte glass"}
    },
    {
        "id": "sample-2",
        "title": "Neo Wallet",
        "description": "Slim carbon fiber wallet for modern life.",
        "price": 79.0,
        "category": "Accessories",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=1200&auto=format&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1610395219791-93e2c8d0e87b?q=80&w=1200&auto=format&fit=crop"
        ],
        "specs": {"Material": "Carbon fiber", "Capacity": "6 cards", "RFID": "Shielded"}
    },
    {
        "id": "sample-3",
        "title": "Arc Charger",
        "description": "MagSafe fast charger with matte finish.",
        "price": 39.0,
        "category": "Gadgets",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?q=80&w=1200&auto=format&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?q=80&w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1587829741301-dc798b83add3?q=80&w=1200&auto=format&fit=crop"
        ],
        "specs": {"Output": "15W", "Cable": "USB‑C", "Finish": "Soft‑touch"}
    },
    {
        "id": "sample-4",
        "title": "Luma Dock",
        "description": "USB‑C hub with anodized aluminum shell.",
        "price": 59.0,
        "category": "Gadgets",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1518779578993-ec3579fee39f?q=80&w=1200&auto=format&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1518779578993-ec3579fee39f?q=80&w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1484704849700-f032a568e944?q=80&w=1200&auto=format&fit=crop"
        ],
        "specs": {"Ports": "HDMI/USB‑A/USB‑C", "Material": "Aluminum", "Color": "Deep purple"}
    },
]

@app.get("/")
def read_root():
    return {"message": "E-Commerce Backend Running"}

@app.get("/api/products")
def list_products(limit: int = 20, q: Optional[str] = None):
    try:
        filt = {}
        if q:
            filt = {"$or": [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
            ]}
        items = get_documents("product", filt, limit)
        for it in items:
            it["id"] = str(it.pop("_id"))
        return {"items": items}
    except Exception:
        items = SAMPLE_PRODUCTS
        if q:
            ql = q.lower()
            items = [s for s in items if ql in s["title"].lower() or ql in (s.get("description") or "").lower()]
        return {"items": items, "note": "database_unavailable_fallback"}

@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    # Try DB first
    try:
        if db is not None:
            doc = db["product"].find_one({"_id": ObjectId(product_id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
                return doc
    except Exception:
        pass
    # Fallback to sample
    for p in SAMPLE_PRODUCTS:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")

@app.post("/api/products", status_code=201)
def create_product(product: ProductCreate):
    try:
        data = product.model_dump()
        new_id = create_document("product", data)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Cart endpoints (ack only; frontend stores state) ---
@app.post("/api/cart/add")
def add_to_cart(payload: AddToCart):
    return {"ok": True, "message": "Added to cart"}

@app.post("/api/wishlist/toggle")
def toggle_wishlist(payload: WishlistUpdate):
    return {"ok": True, "message": "Wishlist updated"}

@app.post("/api/checkout", status_code=201)
def checkout(payload: CheckoutPayload):
    if payload.payment_method != "COD":
        raise HTTPException(status_code=400, detail="Only Cash on Delivery is supported")
    try:
        order = Order(
            client_id=payload.client_id,
            items=[],
            total=0.0,
            payment_method="COD",
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
        )
        order_id = create_document("order", order)
        return {"ok": True, "order_id": order_id, "status": "placed", "payment": "COD"}
    except Exception:
        return {"ok": True, "order_id": "sample-order", "status": "placed", "payment": "COD", "note": "database_unavailable_fallback"}

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
