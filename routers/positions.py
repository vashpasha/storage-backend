from fastapi import APIRouter, HTTPException, Depends
from db import connect_to_database

from models import PositionsParams


router = APIRouter()

@router.get("/")
async def positions_list(db=Depends(connect_to_database)):
    items = await db.fetch("SELECT * FROM positions")
    return [dict(item) for item in items]

@router.post("/")
async def positions_create(item: PositionsParams, db=Depends(connect_to_database)):
    try:
        query = """
            INSERT INTO positions(name, salary)
            VALUES ($1, $2)
        """
        values = (item.name, item.salary)
        await db.execute(query, *values)
    except Exception as e:
        return {"error": e}
    
@router.put("/{id}")
async def positions_update(id: int, item: PositionsParams, db=Depends(connect_to_database)):
    try:
        previous = await db.fetch("SELECT * FROM positions WHERE id=$1", id)
        query = """
            UPDATE positions
            SET name=$1, salary=$2
            WHERE id=$3
        """
        values = (item.name or previous['name'], item.salary or previous['salary'], id)
        await db.execute(query, *values)
    except Exception as e:
        return {"error": e}
    
@router.delete("/{id}")
async def positions_delete(id: int, db=Depends(connect_to_database)):
    try: 
        query = "DELETE FROM positions WHERE id=$1"
        result = await db.execute(query, id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404)
        return
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    
@router.post("/table/")
async def new_column_pos(name: str, value: str, db=Depends(connect_to_database)):
    try:
        query = """
            ALTER TABLE positions
                ADD COLUMN $1
                VARCHAR(100) DEFAULT $2
        """

        values = (name, value)
        await db.execute(query, *values)
    except Exception as e:
        return {"error": e}
    
@router.delete("/table/")
async def delete_column_pos(name: str, db=Depends(connect_to_database)):
    try:
        if name in ["name", "id", "salary"]:
            return {"error": "can't delete this column"}
        await db.execute("ALTER TABLE positions DROP COLUMN $1", name)
    except Exception as e:
        return {"error": e}