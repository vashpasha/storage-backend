from fastapi import APIRouter, HTTPException, Depends
from db import connect_to_database

from models import ProdsParams


router = APIRouter()

@router.get("/")
async def status_list(db=Depends(connect_to_database)):
    items = await db.fetch("SELECT * FROM prods")
    return {'data': [dict(item) for item in items]}

@router.post("/")
async def new_prod(item: ProdsParams, db=Depends(connect_to_database)):
    try:
        query = """
            INSERT INTO prods(name, phone, country)
            VALUES ($1, $2, $3)
        """
        values = (item.name, item.phone, item.country)

        await db.execute(query, *values)
    except Exception as e:
        raise HTTPException(status_code=500)
    
@router.put("/{id}")
async def update_loader(id:int, item: ProdsParams, db=Depends(connect_to_database)):
    try:
        previous = await db.fetchrow("SELECT name, phone, country FROM prods WHERE id=$1", id)
        query = """
            UPDATE prods
            SET name=$1, phone=$2, country=$3
            WHERE id=$4
        """
        values = (
            item.name or previous['name'],
            item.phone or previous['phone'],
            item.country or previous['country'],
            id
        )
        await db.execute(query, *values)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    
@router.delete("/{id}")
async def delete_prod(id: int, db=Depends(connect_to_database)):
    try:
        query = "DELETE FROM prods WHERE id = $1"
        result = await db.execute(query, id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404)
        return
    except Exception as e:
        raise HTTPException(status_code=500)
    
@router.post("/table/")
async def new_column_prods(name: str, value: str, db=Depends(connect_to_database)):
    try:
        query = """
            ALTER TABLE prods
                ADD COLUMN $1
                VARCHAR(100) DEFAULT $2
        """

        values = (name, value)
        await db.execute(query, *values)
    except Exception as e:
        return {"error": e}
    
@router.delete("/table/")
async def delete_column_prods(name: str, db=Depends(connect_to_database)):
    try:
        if name in ["name", "id", "phone", "country"]:
            return {"error": "can't delete this column"}
        await db.execute("ALTER TABLE prods DROP COLUMN $1", name)
    except Exception as e:
        return {"error": e}