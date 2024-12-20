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

        potion_ml = {"red_ml": 0, "green_ml": 0, "blue_ml": 0}
        gold_cost = 0

        for barrel in barrels_delivered: # change db updates for logic within  query calls, already changed red: use as reference
            if barrel.potion_type[0] == 1:
                
                potion_ml["red_ml"] += (barrel.ml_per_barrel * barrel.quantity)
                gold_cost += barrel.price * barrel.quantity

                print(f"Cost deducted for current barrel of red: {barrel.price}")
                print(f"Red ml RECIEVED: {potion_ml['red_ml']}")


            if barrel.potion_type[1] == 1:

                potion_ml["green_ml"] += (barrel.ml_per_barrel * barrel.quantity)
                gold_cost += barrel.price * barrel.quantity

                print(f"Cost deducted for current barrel of green: {barrel.price}")
                print(f"Green ml RECIEVED: {potion_ml['green_ml']}")

            if barrel.potion_type[2] == 1:

                potion_ml["blue_ml"] += (barrel.ml_per_barrel * barrel.quantity)
                gold_cost += barrel.price * barrel.quantity

                print(f"Cost deducted for current barrel of blue: {barrel.price}")
                print(f"Blue ml RECIEVED: {potion_ml['blue_ml']}")
    
                         
        if potion_ml["red_ml"] + potion_ml["green_ml"] + potion_ml["blue_ml"] != 0:

            connection.execute(sqlalchemy.text("INSERT INTO ml_ledgers (red_ml, green_ml, blue_ml) VALUES (:red_ml,:green_ml,:blue_ml)"),
                            potion_ml)
            connection.execute(sqlalchemy.text("INSERT INTO gold_ledgers (gold) VALUES (:gold_cost)"),
                    {"gold_cost": -gold_cost})
        
        print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"
        
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):

    print(wholesale_catalog)

    barrels_to_buy = []

    with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT SUM(gold) FROM gold_ledgers"))
            gold = result.scalar()

            result = connection.execute(sqlalchemy.text("SELECT (SUM(red_ml) + SUM(green_ml) + SUM(blue_ml) + SUM(dark_ml)) FROM ml_ledgers"))
            all_ml = result.scalar()

            result = connection.execute(sqlalchemy.text("SELECT ml FROM storage"))
            limit = result.scalar()



    print(f"all my ml: {all_ml}")
    print(f"my current gold: {gold}")

    to_buy = 1
    ml_to_buy = 500

    for barrel in wholesale_catalog:
        quantity = 0 # might change to an array for quantity of each potion type
        if barrel.potion_type[0] == 1 and barrel.ml_per_barrel == ml_to_buy and barrel.price <= gold and all_ml < limit:

            while barrel.price <= gold and quantity < to_buy and barrel.quantity > 0:
                all_ml += barrel.ml_per_barrel
                if all_ml > limit:
                    break
                else:
                    quantity += 1
                    barrel.quantity -= 1
                    gold -= barrel.price


            if quantity > 0:
                barrels_to_buy.append(
                {
                "sku": barrel.sku,
                "quantity": quantity,
            }
            )
        quantity=0
        if barrel.potion_type[1] == 1 and barrel.ml_per_barrel == ml_to_buy and barrel.price <= gold and all_ml < limit:

            while barrel.price <= gold and quantity < to_buy and barrel.quantity > 0:
                all_ml += barrel.ml_per_barrel
                if all_ml > limit:
                    break
                else:
                    quantity += 1
                    barrel.quantity -= 1
                    gold -= barrel.price


            if quantity > 0:
                barrels_to_buy.append(
                        {
                    "sku": barrel.sku,
                    "quantity": quantity,

            }
            )
        quantity=0
        if barrel.potion_type[2] == 1 and barrel.ml_per_barrel == ml_to_buy and barrel.price <= gold and all_ml < limit:

            while barrel.price <= gold and quantity < to_buy and barrel.quantity > 0:
                all_ml += barrel.ml_per_barrel
                if all_ml > limit:
                    break
                else:
                    quantity += 1
                    barrel.quantity -= 1
                    gold -= barrel.price

            if quantity > 0:
                barrels_to_buy.append(
                        {
                    "sku": barrel.sku,
                    "quantity": quantity,

                }
                )

    print(barrels_to_buy)
    return barrels_to_buy
