from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/items", tags=["Items"])

class Item(BaseModel):
    id: int
    name: str
    price: float

# simple in-memory store
_items = {
    1: {"id": 1, "name": "Laptop", "price": 89999.99},
    2: {"id": 2, "name": "Mouse", "price": 999.99},
}

@router.get("/")
def list_items():
    return list(_items.values())

@router.get("/{item_id}")
def get_item(item_id: int):
    item = _items.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post("/")
def create_item(item: Item):
    if item.id in _items:
        raise HTTPException(status_code=400, detail="Item id already exists")
    _items[item.id] = item.dict()
    return {"message": "Item created successfully", "item": item}
