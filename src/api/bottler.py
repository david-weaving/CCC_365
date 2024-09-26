from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

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
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        green_ml = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        green_pots = result.scalar()

        # no looping because im only recieving one index of potions
        green_ml = green_ml - (100*potions_delivered[0].quantity)

        print(f"How much Green ml is left after breweing: {green_ml}")
        print(f"Number of potions made: {potions_delivered[0].quantity}")

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml={green_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions={potions_delivered[0].quantity+green_pots}"))

        



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
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        green_ml = result.scalar()
        quantity = 0
        while green_ml >= 100:
            green_ml -= 100 # take out 100 green_ml
            quantity += 1 # give myself a green potion

    print(f"Quantity of potions to make: {quantity}")
    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": quantity,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())
