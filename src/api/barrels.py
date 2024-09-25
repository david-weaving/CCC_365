from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

# MY CHANGES------------------------------------------------------------------ It works, now I need to figure out how to get it to work across the rest of my files
import sqlalchemy 
from src import database as db

# with db.engine.begin() as connection:
#         # buy a new small green potion barell only if the number of potions in inventory is less than 10. Always mix
#         # available green ml if any exists. Offer up for sale in the catalog only the amount of green potions that actually exist currently in inventory.
#         # I am going to do the logic right here and then figure out how this works.
#         # I am going to assume every barrell costs 10 gold, and I know it takes 100ml to make one potion. Let's also assume that each barrel contains 25ml of green.

#         result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
#         gold = result.scalar() # scalar() returns the first value from the row
        
#         result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
#         current_potions = result.scalar()
        
#         cost_of_potion_barrels = 10
#         g_barrel = 0
        
#         while current_potions < 10 and gold >= 10: # while we have less than 10 or we can afford the potions
#                 gold -= cost_of_potion_barrels
#                 g_barrel += 25
#                 if g_barrel == 100: # we have enough to make a potion!
#                         current_potions += 1
#                         g_barrel = 0
                
        
#         connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold={gold}"))
#         connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions={current_potions}"))
        
# ----------------------------------------------------------------------------





router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int] # [r,g,b,d]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        green_ml = result.scalar()
        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        gold = result.scalar()
        for barrel in barrels_delivered:
            green_ml += barrel.ml_per_barrel
            gold -= barrel.price
                
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml {green_ml}"))
        
        print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"
        
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
        
    print(wholesale_catalog)
    quantity = 0
    with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
            gold = result.scalar()
                
            result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
            green_pots = result.scalar()

            result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
            green_ml = result.scalar()
                                        
    for barrel in wholesale_catalog:
            # I want to purchase a barrel iff the barrel is green
        if barrel.potion_type[1] > 0: # making sure there is green ml in my barrel
            if barrel.price <= gold and green_pots < 10: # if i can afford it
                gold -= barrel.price # deduct price
                quantity += 1


    return [
        {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": quantity,
        }
    ]

