from typing import List, Optional
from pydantic import BaseModel, Field


class ReceiptResult(BaseModel):
    class Item(BaseModel):
        price: Optional[int] = Field(default=None)
        name: str = Field(default="")

    items: List[Item] = Field(default=[])
    total: Optional[int] = Field(default=None)
    date: str = Field(default="")
    store: str = Field(default="")
