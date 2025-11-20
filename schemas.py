"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
    image: Optional[str] = Field(None, description="Primary image URL")

class CartItem(BaseModel):
    product_id: str
    qty: int = Field(1, ge=1, description="Quantity")

class Cart(BaseModel):
    """Cart per client_id"""
    client_id: str
    items: List[CartItem] = []

class Wishlist(BaseModel):
    client_id: str
    product_ids: List[str] = []

class Order(BaseModel):
    client_id: str
    items: List[CartItem]
    total: float
    payment_method: str = "COD"
    status: str = "placed"
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
