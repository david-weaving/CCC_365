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

        connection.execute(sqlalchemy.text("DELETE FROM gold_ledgers"))
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledgers (gold) VALUES (:gold)"),
            {"gold": 100}
            )
        connection.execute(sqlalchemy.text("DELETE FROM ml_ledgers"))
        connection.execute(sqlalchemy.text("INSERT INTO ml_ledgers (red_ml, green_ml, blue_ml, dark_ml) VALUES (:red_ml, :green_ml, :blue_ml, :dark_ml)"),
                           {"red_ml": 0, "green_ml": 0, "blue_ml": 0, "dark_ml": 0})
        connection.execute(sqlalchemy.text("DELETE FROM cart_line_item"))
        connection.execute(sqlalchemy.text("DELETE FROM cart"))
        connection.execute(sqlalchemy.text("DELETE FROM potion_ledgers"))
        connection.execute(sqlalchemy.text("UPDATE storage SET pots = :pots, ml = :ml WHERE id = :id"),
    {"pots": 50, "ml": 10000, "id": 1}
)


    return "OK"

