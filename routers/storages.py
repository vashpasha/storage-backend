from fastapi import APIRouter, HTTPException, Depends
from db import connect_to_database

from models import StorageParams


router = APIRouter()

@router.get("/")
async def storage_list(db=Depends(connect_to_database)):
    items = await db.fetch("SELECT * FROM storages")
    return [dict(item) for item in items]

@router.post("/")
async def new_storage(item: StorageParams, db=Depends(connect_to_database)):
    try:
        query = """
            INSERT INTO storages(address)
            VALUES ($1)
        """
        values = (item.address, )
        await db.execute(query, *values)
        return
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    
@router.put("/{id}")
async def update_loader(id:int, item: StorageParams, db=Depends(connect_to_database)):
    try:
        previous = await db.fetchrow("SELECT address FROM storages WHERE id=$1", id)
        query = """
            UPDATE storages
            SET address=$1
            WHERE id=$2
        """
        values = (
            item.name or previous['address'],
            id
        )
        await db.execute(query, *values)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    
@router.delete("/{id}")
async def delete_storage(id: int, db=Depends(connect_to_database)):
    try:
        archive_work = """
            INSERT INTO archive_working(loader, worker, start_time, end_time, storage)
            SELECT (loader, worker, start_time, end_time, storage) FROM working
            WHERE storage=$1
        """
        await db.execute(archive_work, id)
        query = "DELETE FROM storages WHERE id = $1"
        result = await db.execute(query, id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404)
        return
    except Exception as e:
        raise HTTPException(status_code=500)
    
@router.post("/table/")
async def new_column_storages(name: str, value: str, db=Depends(connect_to_database)):
    try:
        query = """
            ALTER TABLE storages
                ADD COLUMN $1
                VARCHAR(100) DEFAULT $2
        """

        values = (name, value)
        await db.execute(query, *values)
    except Exception as e:
        return {"error": e}
    
@router.delete("/table/")
async def delete_column_storages(name: str, db=Depends(connect_to_database)):
    try:

        if name in ["address", "id"]:
            return {"error": "can't delete this column"}
        await db.execute("ALTER TABLE storages DROP COLUMN $1", name)
    except Exception as e:
        return {"error": e}