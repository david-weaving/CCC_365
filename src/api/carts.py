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
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        available_pots = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT customer_green_potions FROM cart"))


        # this code checks to see who is adding what to their carts and ensures that customers do not take what someone else
        # already has
        grab_column = [row[0] for row in result] # grabs entire column

        grab_column = sum(grab_column) # checking to see if there are pots left

        print(f"User {cart_id} wants to put {cart_item.quantity} in their cart")

        if available_pots > 0: # no negative available pots
            available_pots -= grab_column    
        
        if cart_item.quantity <= available_pots and available_pots > 0:
            
            user_pots = cart_item.quantity
            print(f"User {cart_id} has put {user_pots} in their cart")
            connection.execute(sqlalchemy.text(f"UPDATE cart SET customer_green_potions={user_pots} WHERE id = {cart_id}"))
        else:
            
            print(f"User {cart_id} has put {available_pots} in their cart")
            # if user buys more pots than what's available recieve the rest of the batch (or zero)
            connection.execute(sqlalchemy.text(f"UPDATE cart SET customer_green_potions={available_pots} WHERE id = {cart_id}"))

        

        # updates db based on how many pots they want and their unique id created in create_cart
        



    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT customer_green_potions FROM cart WHERE id = {cart_id}"))
        
        green_potions = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        my_green_potions = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        my_current_gold = result.scalar()

        print(f"Customer with ID: {cart_id} is going to purchase {green_potions} Green Potions")

        if green_potions > 0:
            final_price = green_potions * 50
            my_green_potions -= green_potions

            # update my db and gold
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions={my_green_potions}"))
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold={final_price + my_current_gold}"))

            # update customer's db and cart
            connection.execute(sqlalchemy.text(f"UPDATE cart SET customer_green_potions={0} WHERE id={cart_id}"))

            return {"total_potions_bought": green_potions, "total_gold_paid": final_price}
        
        else:

            # update customer's db and cart
            connection.execute(sqlalchemy.text(f"UPDATE cart SET customer_green_potions={0} WHERE id={cart_id}"))
            return {"total_potions_bought": 0, "total_gold_paid": 0}
