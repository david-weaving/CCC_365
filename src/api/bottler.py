from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy 
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):

    with db.engine.begin() as connection:

        for potion in potions_delivered: # change db updates for logic within  query calls

            if potion.potion_type[0] == 100:

                print(f"How much RED ml brewed: {potion.quantity*100}")
                print(f"Number of RED potions made: {potion.quantity}")

                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml= num_red_ml - {potion.quantity*100}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions= num_red_potions + {potion.quantity}"))
            
            if potion.potion_type[1] == 100:
                
                print(f"How much GREEN ml brewed: {potion.quantity*100}")
                print(f"Number of GREEN potions made: {potion.quantity}")

                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml= num_green_ml - {potion.quantity*100}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions= num_green_potions + {potion.quantity}"))

            if potion.potion_type[2] == 100:

                print(f"How much BLUE ml is left after breweing: {potion.quantity*100}")
                print(f"Number of BLUE potions made: {potion.quantity}")

                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml= num_blue_ml - {potion.quantity*100}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions= num_blue_potions + {potion.quantity}"))


        

        



    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    # GOAL: check how much green ml I have and bottle potions

    # return quantity of potions.

    # potion type needs to be [0,100,0,0]

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
        red_ml = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        green_ml = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory"))
        blue_ml = result.scalar()


        quantity_green = 0
        quantity_blue = 0
        quantity_red = 0
        bottles_to_mix = []
    

        # the while loops below are for mixing
        while red_ml >= 100:
            red_ml -= 100
            quantity_red += 1

        while green_ml >= 100:
            green_ml -= 100
            quantity_green += 1

        while blue_ml >= 100:
            blue_ml -= 100
            quantity_blue += 1
            
        if quantity_red > 0:

            print(f"Quantity of RED potions to make: {quantity_red}")

            bottles_to_mix.append(            {
                "potion_type": [100, 0, 0, 0],
                "quantity": quantity_red,
            })

        if quantity_green > 0:

            print(f"Quantity of GREEN potions to make: {quantity_green}")

            bottles_to_mix.append(            {
                "potion_type": [0, 100, 0, 0],
                "quantity": quantity_green,
            })

        if quantity_blue > 0:

            print(f"Quantity of GREEN potions to make: {quantity_blue}")

            bottles_to_mix.append(            {
                "potion_type": [0, 0, 100, 0],
                "quantity": quantity_blue,
            })
        

    
    return bottles_to_mix

if __name__ == "__main__":
    print(get_bottle_plan())
