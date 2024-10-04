from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy 
from src import database as db


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

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
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
        result = connection.execute(sqlalchemy.text("INSERT INTO cart DEFAULT VALUES RETURNING id"))
    
    cart_id = result.scalar()

    print(f"Cart ID: {cart_id} succesfully created")

    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):

    with db.engine.begin() as connection:
        
        if item_sku == "RED_POTION":
            print(f"Customer {cart_id} wants to buy {cart_item.quantity} Red Potions")
            connection.execute(sqlalchemy.text(f"UPDATE cart SET customer_red_potions ={cart_item.quantity} WHERE id = {cart_id}"))

        if item_sku == "GREEN_POTION":
            print(f"Customer {cart_id} wants to buy {cart_item.quantity} Green Potions")
            connection.execute(sqlalchemy.text(f"UPDATE cart SET customer_green_potions ={cart_item.quantity} WHERE id = {cart_id}"))

        if item_sku == "BLUE_POTION":
            print(f"Customer {cart_id} wants to buy {cart_item.quantity} Blue Potions")
            connection.execute(sqlalchemy.text(f"UPDATE cart SET customer_blue_potions ={cart_item.quantity} WHERE id = {cart_id}"))

        # updates db based on how many pots they want and their unique id created in create_cart
        



    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text(f"SELECT customer_red_potions FROM cart WHERE id = {cart_id}"))
        red_potions = result.scalar()

        result = connection.execute(sqlalchemy.text(f"SELECT customer_green_potions FROM cart WHERE id = {cart_id}"))
        green_potions = result.scalar()

        result = connection.execute(sqlalchemy.text(f"SELECT customer_blue_potions FROM cart WHERE id = {cart_id}"))
        blue_potions = result.scalar()


        if red_potions > 0:
            # update my db and gold
            print(f"Customer with ID: {cart_id} HAS PURCHASED {red_potions} Red Potions")
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions= num_red_potions - {red_potions}"))
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold= gold + {red_potions * 50}"))

            return {"total_potions_bought": red_potions, "total_gold_paid": (red_potions * 50)}

        if green_potions > 0:

            print(f"Customer with ID: {cart_id} HAS PURCHASED {green_potions} Green Potions")
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions= num_green_potions - {green_potions}"))
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold= gold + {green_potions * 50}"))

            return {"total_potions_bought": green_potions, "total_gold_paid": (green_potions * 50)}

        if blue_potions > 0:

            print(f"Customer with ID: {cart_id} HAS PURCHASED {blue_potions} Blue Potions")
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions= num_blue_potions - {blue_potions}"))
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold= gold + {blue_potions * 50}"))
            

            return {"total_potions_bought": blue_potions, "total_gold_paid": (blue_potions * 50)}
        

        
        else:

            return {"total_potions_bought": 0, "total_gold_paid": 0}
