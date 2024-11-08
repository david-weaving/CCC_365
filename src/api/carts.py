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
    """
    Search for cart line items by customer name and/or potion sku.
    """
    try:
        with db.engine.begin() as connection:
            print(f"Search page: {search_page}")
            print(f"Customer name: {customer_name}")
            print(f"Potion SKU: {potion_sku}")

            # Updated query to use cost from cart_line_item
            query = """
                SELECT 
                    cli.primary_key as line_item_id,
                    cli.potion_id as item_sku,
                    c.name as customer_name,
                    cli.cost as line_item_total,
                    12 as timestamp
                FROM cart_line_item cli
                JOIN cart c ON cli.cart_id = c.id
            """
            
            result = connection.execute(sqlalchemy.text(query))
            all_rows = result.fetchall()
            
            print(f"Total rows found: {len(all_rows)}")

            # Figure out which page we're on
            if search_page.startswith("page_"):
                current_page = int(search_page.split("_")[1])
            else:
                current_page = 0

            # Calculate slice indices
            start_idx = current_page * 5
            end_idx = start_idx + 5
            
            results = all_rows[start_idx:end_idx]
            
            print(f"Getting page {current_page}")
            
            formatted_results = [
                {
                    "line_item_id": row.line_item_id,
                    "item_sku": row.item_sku,
                    "customer_name": row.customer_name,
                    "line_item_total": row.line_item_total,
                    "timestamp": row.timestamp
                }
                for row in results
            ]

            # Calculate if there's a next page
            has_next = len(all_rows) > end_idx
            
            print(f"Returning {len(formatted_results)} results")
            print(f"Has next page: {has_next}")

            return {
                "previous": f"page_{current_page-1}" if current_page > 0 else "",
                "next": f"page_{current_page+1}" if has_next else "",
                "results": formatted_results
            }

    except Exception as e:
        print(f"Search error: {str(e)}")
        return {
            "previous": "",
            "next": "",
            "results": []
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
        

        connection.execute(sqlalchemy.text("INSERT INTO cart_line_item (primary_key, cart_id, potion_id, quantity) VALUES (DEFAULT, :cart_id, :item_sku, :quantity)"),
                                           {"cart_id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity})        

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
        
