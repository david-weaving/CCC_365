from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
from base64 import b64encode, b64decode
import json
from typing import Optional, List


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy 
from src import database as db

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    with db.engine.begin() as connection:

        # so i dont have to keep writing it up
        query = """
            SELECT 
                line_items.primary_key as line_item_id,
                line_items.potion_id as raw_potion_id,
                line_items.quantity as quantity,
                carts.name as customer_name,
                line_items.cost as line_item_total,
                line_items.time as timestamp
            FROM cart_line_item line_items
            JOIN cart carts ON line_items.cart_id = carts.id
            WHERE 1=1
        """
        
        params = {}
        if customer_name:
            query += " AND LOWER(carts.name) LIKE :customer_name"
            params['customer_name'] = f"%{customer_name.lower()}%"
        if potion_sku:
            query += " AND LOWER(line_items.potion_id) LIKE :potion_sku"
            params['potion_sku'] = f"%{potion_sku.lower()}%"

        sort_direction = "ASC" if sort_order == search_sort_order.asc else "DESC"
        
        sort_map = {
            search_sort_options.customer_name: "carts.name",
            search_sort_options.item_sku: "line_items.potion_id",
            search_sort_options.line_item_total: "line_items.cost",
            search_sort_options.timestamp: "line_items.time"
        }
        
        query += f" ORDER BY {sort_map[sort_col]} {sort_direction}"
        
        result = connection.execute(sqlalchemy.text(query), params)
        all_rows = result.fetchall()

        current_page = int(search_page.split("_")[1]) if search_page.startswith("page_") else 0
        start = current_page * 5
        end = start + 5
        
        results = all_rows[start:end]

        for row in results:
            finished_results = [
                {
                    "line_item_id": row.line_item_id,
                    "item_sku": f"{row.raw_potion_id.replace('_', ' ')} ({row.quantity})",
                    "customer_name": row.customer_name,
                    "line_item_total": row.line_item_total,
                    "timestamp": str(row.timestamp)
                }
                
            ]

        has_next = len(all_rows) > end
        
        return {
            "previous": f"page_{current_page-1}" if current_page > 0 else "",
            "next": f"page_{current_page+1}" if has_next else "",
            "results": finished_results
        }

class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(
        sqlalchemy.text(
            "INSERT INTO cart (id, class, level, name) VALUES (DEFAULT, :character_class, :level, :name) RETURNING id"
                ),
            {"character_class": new_cart.character_class, "level": new_cart.level, "name": new_cart.customer_name}
)

    cart_id = result.scalar()

    print(f"Cart ID: {cart_id} succesfully created")

    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("INSERT INTO cart_line_item (primary_key, cart_id, potion_id, quantity, time) VALUES (DEFAULT, :cart_id, :item_sku, :quantity, CURRENT_TIMESTAMP)"),
            {
                "cart_id": cart_id, 
                "item_sku": item_sku, 
                "quantity": cart_item.quantity
            }
        )        

    print(f"Customer {cart_id} wants {cart_item.quantity} {item_sku}")
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT cart_line_item.quantity, potions.price, potions.id FROM cart_line_item JOIN potions ON potions.potion_name = cart_line_item.potion_id WHERE cart_line_item.cart_id = :cart_id"),
        {"cart_id": cart_id}
    )
        

        rows = result.fetchall()
        total_pots = 0
        ledger_entries = []
        total_gold = 0

        for quantity, cost, potion_id in rows:
            ledger_entries.append({"potion_id": potion_id, "quantity": -quantity})
            total_gold += quantity * cost
            total_pots += quantity

        connection.execute(sqlalchemy.text("INSERT INTO potion_ledgers (id, potion_id, amount) VALUES (DEFAULT, :potion_id, :quantity)"),
            ledger_entries
        )

        connection.execute(sqlalchemy.text("INSERT INTO gold_ledgers (gold) VALUES (:total_gold)"),
            {"total_gold": total_gold}
        )

        connection.execute(
            sqlalchemy.text("UPDATE cart_line_item SET cost = :total_gold WHERE cart_id = :cart_id"),
            {"total_gold": total_gold, "cart_id": cart_id}
        )
    print(f"total_potions_bought: ({total_pots}), total_gold_paid: ({total_gold})")

    return {"total_potions_bought": total_pots, "total_gold_paid": total_gold}
        
