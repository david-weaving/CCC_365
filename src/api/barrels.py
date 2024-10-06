from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

# MY CHANGES------------------------------------------------------------------ It works, now I need to figure out how to get it to work across the rest of my files
import sqlalchemy 
from src import database as db

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

        for barrel in barrels_delivered:
            if barrel.potion_type[0] == 1:
                
                print(f"Cost deducted for current barrel of red: {barrel.price * barrel.quantity}")
                print(f"Red ml RECIEVED: {barrel.ml_per_barrel*barrel.quantity}")
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml= num_red_ml + {barrel.ml_per_barrel * barrel.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold= gold - {barrel.price * barrel.quantity}"))

            if barrel.potion_type[1] == 1:

                print(f"Cost deducted for current barrel of green: {barrel.price * barrel.quantity}")
                print(f"Green ml RECIEVED: {barrel.ml_per_barrel*barrel.quantity}")
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml= num_green_ml + {barrel.ml_per_barrel * barrel.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold= gold - {barrel.price * barrel.quantity}"))

            if barrel.potion_type[2] == 1:

                print(f"Cost deducted for current barrel of blue: {barrel.price * barrel.quantity}")
                print(f"Blue ml RECIEVED: {barrel.ml_per_barrel*barrel.quantity}")
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml= num_blue_ml + {barrel.ml_per_barrel * barrel.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold= gold - {barrel.price * barrel.quantity}"))
                         
        
        
        print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"
        
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
        
    print(wholesale_catalog)

    barrels_to_buy = []

    with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
            gold = result.scalar()
                
            result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
            green_pots = result.scalar()

            result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
            red_pots = result.scalar()

            result = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory"))
            blue_pots = result.scalar()

    

    for barrel in wholesale_catalog:
        quantity = 0 # might change to an array for quantity of each potion type
        if barrel.potion_type[0] == 1 and barrel.ml_per_barrel == 500 and red_pots < 10 and barrel.price <= gold:

            while barrel.price <= gold and quantity < 1 and barrel.quantity > 0:
                quantity += 1
                barrel.quantity -= 1
                gold -= barrel.price
                
            
            print(f"Quantity of red barrels looked at: {quantity}")
            
            barrels_to_buy.append(
              {
            "sku": barrel.sku,
            "quantity": quantity,
        }
        )
        quantity=0
        if barrel.potion_type[1] == 1 and barrel.ml_per_barrel == 500 and green_pots < 10 and barrel.price <= gold:
            
            while barrel.price <= gold and quantity < 1 and barrel.quantity > 0:
                quantity += 1
                barrel.quantity -= 1
                gold -= barrel.price

            
            print(f"Quantity of green barrels looked at: {quantity}")

            barrels_to_buy.append(
                    {
                "sku": barrel.sku,
                "quantity": quantity,

            }
            )
        quantity=0
        if barrel.potion_type[2] == 1 and barrel.ml_per_barrel == 500 and blue_pots < 10 and barrel.price <= gold:
     
            while barrel.price <= gold and quantity < 1 and barrel.quantity > 0:
                quantity += 1
                barrel.quantity -= 1
                gold -= barrel.price


            print(f"Quantity of blue barrels looked at: {quantity}")

            barrels_to_buy.append(
                    {
                "sku": barrel.sku,
                "quantity": quantity,

            }
            )
            



    return barrels_to_buy
