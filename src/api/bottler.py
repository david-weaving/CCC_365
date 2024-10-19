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
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions ORDER BY id DESC"))
        potion_table = result.fetchall()

        for rows in potion_table:
            for potion in potions_delivered:
                
                if tuple(potion.potion_type) == rows[2:6]:
                    connection.execute(sqlalchemy.text(f"INSERT INTO potion_ledgers (amount, potion_id) VALUES ({potion.quantity}, {rows[0]})"))

                    connection.execute(sqlalchemy.text(f"UPDATE ml_inventory SET red_ml = red_ml - :total_red"),
                                       {"total_red": potion.potion_type[0]*potion.quantity})
                    
                    connection.execute(sqlalchemy.text(f"UPDATE ml_inventory SET green_ml = green_ml - :total_green"),
                                       {"total_green": potion.potion_type[1]*potion.quantity})
                    
                    connection.execute(sqlalchemy.text(f"UPDATE ml_inventory SET blue_ml = blue_ml - :total_blue"),
                                       {"total_blue": potion.potion_type[2]*potion.quantity})

                


        

        



    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions ORDER BY id DESC"))
        potion_table = result.fetchall()
    
        result = connection.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, black_ml FROM ml_inventory"))
        row = result.fetchone()

        r1,g1,b1,d1 = row[:4]

        
        bottles_to_mix = []
        for rows in potion_table: # grabs each row in the table, each represents a different potion type
            pot_name, r2,g2,b2,d2 = rows[1:6] # grabs those specific columns
            #print(pot_name, r2,b2,g2,d2)

            quantity = 0
            if sum((r1,b1,g1,d1)) > 0: # so we dont append only 0's
                
                while r1 >= r2 and g1 >= g2 and b1 >= b2 and d1 >=d2 and quantity < 2: # currently making 2 of every potion I can
                    r1 -= r2 # r1 represents my inventory, r2 is required potions
                    g1 -= g2
                    b1 -= b2
                    d1 -= d2
                    quantity += 1
                
                print(f"Number of {pot_name} TO make: {quantity}")
                if quantity > 0:
                    bottles_to_mix.append({
                        "potion_type": [r2,g2,b2,d2], # given that row, how many of these potions can I make, if any?
                        "quantity": quantity,
                    })

    return bottles_to_mix

if __name__ == "__main__":
    print(get_bottle_plan())
