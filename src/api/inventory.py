from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy 
from src import database as db


router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT (SUM(red_ml) +SUM(green_ml) + SUM(blue_ml) + SUM(dark_ml)) FROM ml_ledgers"))
        row = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT SUM(gold) FROM gold_ledgers"))
        gold = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT SUM(inventory) AS total_inventory FROM ( SELECT COALESCE(SUM(potion_ledgers.amount), 0) AS inventory FROM potions LEFT JOIN potion_ledgers ON potion_ledgers.potion_id = potions.id GROUP BY potions.id ) AS inventory_table;"))
        all_pots = result.scalar()

    print(f"Number of potions: {all_pots}, ml in barrels: {row}, gold: {gold}")

    return {"number_of_potions": all_pots, "ml_in_barrels": row, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT SUM(gold) FROM gold_ledgers"))
        gold = result.scalar()

    switch = False # this is dumb, but i dont want any new capacity.
    
    if switch is True:
        print("Capacity plan looked at.")
        return {
        "potion_capacity": 1,
        "ml_capacity": 1
        }
    else:
        print("cannot afford capacity plan.")
        return {
            "potion_capacity": 0,
            "ml_capacity": 0
            }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:

        if capacity_purchase.potion_capacity == 1 and capacity_purchase.ml_capacity  == 1:
            cost = (capacity_purchase.potion_capacity * 1000) + (capacity_purchase.ml_capacity * 1000)

            print(f"New potion capacity bought: {capacity_purchase.potion_capacity}, {capacity_purchase.ml_capacity}")

            connection.execute(sqlalchemy.text("INSERT INTO gold_ledgers (gold) VALUES (:cost)"),
                    {"gold_cost": -cost})
            
            connection.execute(sqlalchemy.text("UPDATE storage SET pots = pots + :new_pot, ml = ml + :new_ml"),
                               {"new_pot": 50, "new_ml": 10000})
            
        else:
            print("no new storage!")

    return "OK"
