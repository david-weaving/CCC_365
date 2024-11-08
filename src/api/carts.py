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
    request: Request,
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    try:
        # Decode the search page cursor if provided
        cursor = None
        if search_page:
            cursor_data = json.loads(b64decode(search_page))
            cursor = cursor_data.get("last_value")

        # Build the base query
        query = sa.text("""
            SELECT 
                cli.primary_key as line_item_id,
                cli.potion_id as item_sku,
                c.customer_name,
                :gold as line_item_total,
                :timestamp as timestamp
            FROM cart_line_item cli
            JOIN cart c ON cli.cart_id = c.cart_id
            WHERE 1=1
        """)

        # Initialize parameters
        params = {
            'gold': 50,  # Constant as requested
            'timestamp': '2024-01-01T00:00:00Z'  # Constant as requested
        }

        # Build the WHERE clause based on filters
        where_clauses = []
        if customer_name:
            where_clauses.append("LOWER(c.customer_name) LIKE :customer_name")
            params['customer_name'] = f'%{customer_name.lower()}%'

        if potion_sku:
            where_clauses.append("LOWER(cli.potion_id) LIKE :potion_sku")
            params['potion_sku'] = f'%{potion_sku.lower()}%'

        # Add cursor pagination
        if cursor:
            compare_op = ">=" if sort_order == search_sort_order.asc else "<="
            if sort_col == search_sort_options.timestamp:
                where_clauses.append(f"timestamp {compare_op} :cursor")
            else:
                where_clauses.append(f"customer_name {compare_op} :cursor")
            params['cursor'] = cursor

        # Combine WHERE clauses
        if where_clauses:
            query = sa.text(str(query) + " AND " + " AND ".join(where_clauses))

        # Add ORDER BY
        sort_direction = "ASC" if sort_order == search_sort_order.asc else "DESC"
        query = sa.text(str(query) + f" ORDER BY {sort_col.value} {sort_direction}")

        # Add LIMIT
        query = sa.text(str(query) + " LIMIT 6")  # Get one extra to check for next page

        # Execute query
        with db.engine.connect() as connection:
            result = connection.execute(query, params)
            results = result.fetchall()

        # Process results
        has_next = len(results) > 5
        results = results[:5]  # Trim to max 5 results

        # Format results
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

        # Generate pagination tokens
        previous_token = ""
        next_token = ""

        if results:
            if cursor:  # If we have a cursor, we can go previous
                previous_data = {"last_value": cursor}
                previous_token = b64encode(json.dumps(previous_data).encode()).decode()

            if has_next:  # If we have more results, we can go next
                last_row = results[-1]
                if sort_col == search_sort_options.timestamp:
                    last_value = str(last_row.timestamp)
                else:
                    last_value = last_row.customer_name
                next_data = {"last_value": last_value}
                next_token = b64encode(json.dumps(next_data).encode()).decode()

        return {
            "previous": previous_token,
            "next": next_token,
            "results": formatted_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


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
        
