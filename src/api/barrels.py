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
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        green_ml = result.scalar()
        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        gold = result.scalar()
        for barrel in barrels_delivered:
            if barrel.sku == "SMALL_GREEN_BARREL":
                print(f"Barrel Quantity: {barrel.quantity}")
                green_ml += (barrel.ml_per_barrel * barrel.quantity)
                print(f"Number of Green ml: {green_ml}")
                gold -= (barrel.price * barrel.quantity)
                
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml= {green_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold= {gold}"))
        
        
        print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"
        
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
        
    print(wholesale_catalog)

    with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
            gold = result.scalar()
                
            result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
            green_pots = result.scalar()
    quantity = 0
    for barrel in wholesale_catalog:
            # I want to purchase a barrel iff the barrel is green
        if barrel.sku == "SMALL_GREEN_BARREL" and green_pots < 10: # making sure there is green ml in my barrel
            i = 1 # keeps track of barrel quantity (seeing how much I can afford)
            
            while barrel.price <= gold and i <= barrel.quantity:
                quantity = i
                i += 1
                gold -= barrel.price
                 
    
    barrels_to_buy = []

    if quantity > 0:
         barrels_to_buy.append(
              {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": quantity,
        } 
        )

    print(f"Quantity: {quantity}")
    return barrels_to_buy
