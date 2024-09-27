from fastapi import APIRouter
import sqlalchemy 
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():

    with db.engine.begin() as connection:
        
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        green_pots = result.scalar()
    
    print(f"Catalog has following items: Green Potions: {green_pots} and price is 25 gold ")


    return [
            {
                "sku": "GREEN_POTION_1",
                "name": "green potion",
                "quantity": green_pots,
                "price": 25,
                "potion_type": [0, 100, 0, 0],
            }
        ]
