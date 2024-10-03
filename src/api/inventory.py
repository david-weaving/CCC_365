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
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        red_pots = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        green_pots = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory"))
        blue_pots = result.scalar()

        all_pots = red_pots + green_pots + blue_pots
        
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
        red_ml = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        green_ml = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory"))
        blue_ml = result.scalar()

        all_ml = red_ml + green_ml + blue_ml

        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        gold = result.scalar()
    
    return {"number_of_potions": all_pots, "ml_in_barrels": all_ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 50,
        "ml_capacity": 10000
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
