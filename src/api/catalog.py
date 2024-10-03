from fastapi import APIRouter
import sqlalchemy 
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():

    with db.engine.begin() as connection:
        
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        red_pots = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        green_pots = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory"))
        blue_pots = result.scalar()

    
    print(f"Catalog has the following Potions: Green: {green_pots}, Red: {red_pots}, Blue: {blue_pots} and price is 50 gold")

    my_catalog = []

    if red_pots > 0:

        my_catalog.append(
                        {
                "sku": "RED_POTION",
                "name": "red potion",
                "quantity": red_pots,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        )

    if green_pots > 0:

        my_catalog.append(
                        {
                "sku": "GREEN_POTION",
                "name": "green potion",
                "quantity": green_pots,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            }
        )

    if blue_pots > 0:

        my_catalog.append(
                        {
                "sku": "BLUE_POTION",
                "name": "blue potion",
                "quantity": blue_pots,
                "price": 50,
                "potion_type": [0, 0, 100, 0],
            }
        )

    

    return my_catalog
       
