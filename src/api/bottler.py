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
    # Fetch the potion table once and store the result
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions ORDER BY id DESC"))
        potion_table = result.fetchall()

        insert_values = []
        update_totals = {"total_red": 0, "total_green": 0, "total_blue": 0}

        potion_dict = {tuple(row[2:6]): row[0] for row in potion_table}

        for potion in potions_delivered:
            potion_type_tuple = tuple(potion.potion_type)

            if potion_type_tuple in potion_dict:
                potion_id = potion_dict[potion_type_tuple]
                
                insert_values.append({"potion_id": potion_id, "amount": potion.quantity})
                
                
                update_totals["total_red"] += potion.potion_type[0] * potion.quantity
                update_totals["total_green"] += potion.potion_type[1] * potion.quantity
                update_totals["total_blue"] += potion.potion_type[2] * potion.quantity


        if insert_values:
            connection.execute(sqlalchemy.text("INSERT INTO potion_ledgers (potion_id, amount) VALUES (:potion_id, :amount)"),
                insert_values
            )

        connection.execute(sqlalchemy.text("UPDATE ml_inventory SET red_ml = red_ml - :total_red, green_ml = green_ml - :total_green, blue_ml = blue_ml - :total_blue"),
            update_totals
        )

    print(f"potions delivered: {potions_delivered} order_id: {order_id}")
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

        result = connection.execute(sqlalchemy.text("SELECT SUM(inventory) AS total_inventory FROM ( SELECT COALESCE(SUM(potion_ledgers.amount), 0) AS inventory FROM potions LEFT JOIN potion_ledgers ON potion_ledgers.potion_id = potions.id GROUP BY potions.id ) AS inventory_table;"))
        all_pots = result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT pots FROM storage"))
        limit = result.scalar()

        r1,g1,b1,d1 = row[:4]

        
        bottles_to_mix = []
        print(f"ALL MY POTS: {all_pots} ")
        for rows in potion_table: # grabs each row in the table, each represents a different potion type
            pot_name, r2,g2,b2,d2 = rows[1:6] # grabs those specific columns
            #print(pot_name, r2,b2,g2,d2)

            quantity = 0
            if sum((r1,b1,g1,d1)) > 0: # so we dont append only 0's
                
                while r1 >= r2 and g1 >= g2 and b1 >= b2 and d1 >=d2 and all_pots < limit and quantity < 3: # currently making 3 of every potion I can
                    r1 -= r2 # r1 represents my inventory, r2 is required potions
                    g1 -= g2
                    b1 -= b2
                    d1 -= d2
                    quantity += 1
                    all_pots += 1
                
                print(f"Number of {pot_name} made: {quantity}")
                print(f"r:{r2}, b:{b2}, g:{g2}, d{d2}")
                if quantity > 0:
                    bottles_to_mix.append({
                        "potion_type": [r2,g2,b2,d2], # given that row, how many of these potions can I make, if any?
                        "quantity": quantity,
                    })

    print(bottles_to_mix)
    return bottles_to_mix

if __name__ == "__main__":
    print(get_bottle_plan())
