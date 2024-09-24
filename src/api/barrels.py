from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

# MY CHANGES------------------------------------------------------------------ (remove if broken)
import sqlalchemy
from src import database as db

with db.engine.begin() as connection:
        # buy a new small green potion barell only if the number of potions in inventory is less than 10. Always mix
        # available green ml if any exists. Offer up for sale in the catalog only the amount of green potions that actually exist currently in inventory.
        # I am going to do the logic right here and then figure out how this works.
        # I am going to assume every barrell costs 10 gold, and I know it takes 100ml to make one potion. Let's also assume that each barrel contains 25ml of green.

        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        print(result)
        
# ----------------------------------------------------------------------------
router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        }
    ]

