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
        result = connection.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, black_ml FROM ml_inventory"))
        row = result.fetchone()

        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        gold = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT SUM(inventory) AS total_inventory FROM ( SELECT COALESCE(SUM(potion_ledgers.amount), 0) AS inventory FROM potions LEFT JOIN potion_ledgers ON potion_ledgers.potion_id = potions.id GROUP BY potions.id ) AS inventory_table;"))
        all_pots = result.scalar()

    print(f"Number of potions: {all_pots}, ml in barrels: {sum(row)}, gold: {gold}")

    return {"number_of_potions": all_pots, "ml_in_barrels": sum(row), "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 1,
        "ml_capacity": 1
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


    return "OK"
