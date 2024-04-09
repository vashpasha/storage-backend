from fastapi import APIRouter, HTTPException, Depends
from db import connect_to_database

from models import StatusesParams


router = APIRouter()

@router.get("/")
async def status_list(db=Depends(connect_to_database)):
    items = await db.fetch("SELECT * FROM statuses")
    return [dict(item) for item in items]

@router.post("/")
async def positions_create(item: StatusesParams, db=Depends(connect_to_database)):
    try:
        query = """
            INSERT INTO statuses(name)
            VALUES ($1)
        """
        await db.execute(query, item.name)
    except Exception as e:
        return {"error": e}

@router.put("/{id}")
async def positions_update(id: int, item: StatusesParams, db=Depends(connect_to_database)):
    try:
        previous = await db.fetch("SELECT * FROM statuses WHERE id=$1", id)
        query = """
            UPDATE statuses
            SET name=$1
            WHERE id=$2
        """
        values = (item.name or previous['name'], id)
        await db.execute(query, *values)
    except Exception as e:
        return {"error": e}
    
@router.delete("/{id}")
async def positions_delete(id: int, db=Depends(connect_to_database)):
    try: 
        if id==7:
            return {"error": "untocheble"}
        update = """
            UPDATE loaders
            SET status=7
            WHERE status=$1
        """
        await db.execute(update, id)
        query = "DELETE FROM statuses WHERE id=$1"
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
            ALTER TABLE statuses
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
        if name in ["name", "id"]:
            return {"error": "can't delete this column"}
        await db.execute("ALTER TABLE statuses DROP COLUMN $1", name)
    except Exception as e:
        return {"error": e}