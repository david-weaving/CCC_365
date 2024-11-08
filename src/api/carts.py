from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy as sa
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

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    with db.engine.begin() as connection:
        # Build the base query
        query = """
            SELECT 
                cli.primary_key as line_item_id,
                cli.potion_id as item_sku,
                c.customer_name,
                p.price as line_item_total,
                CURRENT_TIMESTAMP as timestamp
            FROM cart_line_item cli
            JOIN cart c ON cli.cart_id = c.cart_id
            JOIN potions p ON cli.potion_id = p.potion_name
            WHERE 1=1
        """
        params = {}

        # Add filters
        if customer_name:
            query += " AND LOWER(c.customer_name) LIKE :customer_name"
            params['customer_name'] = f'%{customer_name.lower()}%'

        if potion_sku:
            query += " AND LOWER(cli.potion_id) LIKE :potion_sku"
            params['potion_sku'] = f'%{potion_sku.lower()}%'

        # Add sorting
        sort_direction = "ASC" if sort_order == search_sort_order.asc else "DESC"
        query += f" ORDER BY {sort_col.value} {sort_direction}"
        
        # Add pagination
        query += " LIMIT 6"  # Get one extra to check for next page

        # Execute query
        result = connection.execute(sqlalchemy.text(query), params)
        rows = result.fetchall()

        # Process results
        has_next = len(rows) > 5
        results = rows[:5]  # Trim to max 5 results

        # Format results
        formatted_results = [
            {
                "line_item_id": row.line_item_id,
                "item_sku": row.item_sku,
                "customer_name": row.customer_name,
                "line_item_total": row.line_item_total,
                "timestamp": str(row.timestamp)
            }
            for row in results
        ]

        return {
            "previous": "",  # For now, could implement if needed
            "next": "" if not has_next else "next",
            "results": formatted_results
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
            "INSERT INTO cart (id, class, level) VALUES (DEFAULT, :character_class, :level) RETURNING id"
                ),
            {"character_class": new_cart.character_class, "level": new_cart.level}
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

    print(f"total_potions_bought: ({total_pots}), total_gold_paid: ({total_gold})")

    return {"total_potions_bought": total_pots, "total_gold_paid": total_gold}
        
