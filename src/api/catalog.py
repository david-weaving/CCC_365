from fastapi import APIRouter
import sqlalchemy 
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():

    with db.engine.begin() as connection:
        
        result = connection.execute(sqlalchemy.text("SELECT potions.id, COALESCE(sum(potion_ledgers.amount),0) AS inventory, potions.red_ml AS red, potions.green_ml AS green, potions.blue_ml AS blue, potions.dark_ml AS dark, potions.potion_name AS name FROM potions LEFT JOIN potion_ledgers ON potion_ledgers.potion_id = potions.id GROUP BY potions.id ORDER BY potions.id"))
        catalog = result.fetchall()

    my_catalog = []

    for pot_id, amount, red, green, blue, dark, name in catalog:
        print(f"ID: {pot_id}, amount: {amount}, potion: {name}")
        if amount > 0:
            
            
            my_catalog.append(
                        {
                "sku": name,
                "name": name.replace("_", " "),
                "quantity": int(amount),
                "price": 50,
                "potion_type": [red, green, blue, dark],
            }
           
        )
            print(my_catalog)

    

    return my_catalog
       
