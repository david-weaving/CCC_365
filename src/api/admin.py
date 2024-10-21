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

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold=100"))
        connection.execute(sqlalchemy.text("UPDATE ml_inventory SET red_ml=0, green_ml=0, blue_ml=0, black_ml=0"))
        connection.execute(sqlalchemy.text("DELETE FROM cart_line_item"))
        connection.execute(sqlalchemy.text("DELETE FROM cart"))
        connection.execute(sqlalchemy.text("DELETE FROM potion_ledgers"))


    return "OK"

