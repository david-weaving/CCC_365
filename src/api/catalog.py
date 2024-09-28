from fastapi import APIRouter
import sqlalchemy 
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():

    with db.engine.begin() as connection:
        
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        green_pots = result.scalar()
    
    print(f"Catalog has following items: Green Potions: {green_pots} and price is 50 gold ")

    my_catalog = []

    if green_pots > 0:
        my_catalog.append(
                        {
                "sku": "GREEN_POTION_1",
                "name": "green potion",
                "quantity": green_pots,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            }
        )
    return my_catalog
       
