from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy 
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():


    with db.engine.begin() as connection:

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold=100,num_green_potions={0},num_blue_potions={0},num_red_potions={0},num_green_ml={0},num_blue_ml={0},num_red_ml={0} WHERE id = {1}"))
        connection.execute(sqlalchemy.text("DELETE FROM cart"))
        connection.execute(sqlalchemy.text("ALTER SEQUENCE cart_id_seq RESTART WITH 1")) # start from 1 again

    print("SHOP HAS BEEN RESET")


    return "OK"

