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
            # First get total count for pagination
            count_query = """
                SELECT COUNT(*) 
                FROM cart_line_item cli
                JOIN cart c ON cli.cart_id = c.id
                WHERE 1=1
            """
            params = {}

            if customer_name:
                count_query += " AND LOWER(c.name) LIKE :customer_name"
                params['customer_name'] = f'%{customer_name.lower()}%'

            if potion_sku:
                count_query += " AND LOWER(cli.potion_id) LIKE :potion_sku"
                params['potion_sku'] = f'%{potion_sku.lower()}%'

            total_count = connection.execute(sqlalchemy.text(count_query), params).scalar()

            # Now get the actual results
            query = """
                WITH numbered_rows AS (
                    SELECT 
                        cli.primary_key as line_item_id,
                        cli.potion_id as item_sku,
                        c.name as customer_name,
                        12 as timestamp,
                        ROW_NUMBER() OVER (ORDER BY c.name) as row_num
                    FROM cart_line_item cli
                    JOIN cart c ON cli.cart_id = c.id
                    WHERE 1=1
            """

            if customer_name:
                query += " AND LOWER(c.name) LIKE :customer_name"

            if potion_sku:
                query += " AND LOWER(cli.potion_id) LIKE :potion_sku"

            query += ") SELECT * FROM numbered_rows WHERE row_num <= 5"

            result = connection.execute(sqlalchemy.text(query), params)
            rows = result.fetchall()

            formatted_results = [
                {
                    "line_item_id": row.line_item_id,
                    "item_sku": row.item_sku,
                    "customer_name": row.customer_name,
                    "line_item_total": 50,
                    "timestamp": row.timestamp
                }
                for row in rows
            ]

            has_more = total_count > 5

            return {
                "previous": "",
                "next": "next" if has_more else "",
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
        
