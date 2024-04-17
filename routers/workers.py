from fastapi import APIRouter, HTTPException, Depends
from db import connect_to_database
from typing import Optional

from models import WorkerParams


router = APIRouter()

@router.get("/")
async def workers_list(position: Optional[int] = None, free: Optional[int]= -1, db=Depends(connect_to_database)):
    query = "SELECT * FROM workers"
    
    if free is not -1 and position:
        query += " WHERE is_free = $1 AND position = $2"
        values = (bool(free), position)
        items = await db.fetch(query, *values)
    elif free is not -1:
        query += " WHERE is_free = $1"
        items = await db.fetch(query, bool(free))
    elif position:
        query += " WHERE position = $1"
        items = await db.fetch(query, position)
    else:        
        items = await db.fetch(query)

    return {'data': [dict(item) for item in items]}

@router.get("/{id}")
async def worker_detail(id: int, db=Depends(connect_to_database)):
    try: 
        info = await db.fetch("SELECT loaders.number, start_time, end_time, storages.address FROM working JOIN loaders ON working.loader=loaders.id JOIN storages ON working.storage=storages.id WHERE worker=$1", id)
        query = "SELECT * FROM workers WHERE id=$1"
        result = await db.fetchrow(query, id)
        if result:
            return {"worker": dict(result), "works": [infow for infow in info]}
        else:
            raise HTTPException(status_code=404)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    
 
@router.post("/")
async def new_worker(item: WorkerParams, db=Depends(connect_to_database)):
    try:
        query = """
            INSERT INTO workers(first_name, last_name, position, phone, is_free)
            VALUES ($1, $2, $3, $4, True)
        """
        values = (item.first_name, item.last_name, item.position, item.phone)
        await db.execute(query, *values)
    except Exception as e:
        raise HTTPException(status_code=500)
    
@router.put("/{id}")
async def update_worker(id:int, item: WorkerParams, db=Depends(connect_to_database)):
    try:
        previous = await db.fetchrow("SELECT first_name, last_name, position, phone, is_free FROM workers WHERE id=$1", id)
        query = """
            UPDATE workers
            SET first_name=$1, last_name=$2, position=$3, phone=$4, is_free=$5
            WHERE id=$6
        """
        print(previous)
        is_free = bool(item.is_free) if item.is_free!=None else previous['is_free']
        print(is_free)
        values = (
            item.first_name or previous['first_name'],
            item.last_name or previous['last_name'],
            item.position or previous['position'],
            item.phone or previous['phone'],
            is_free,
            id
        )
        await db.execute(query, *values)
    except Exception as e:
        print(item)
        print(e)
        raise HTTPException(status_code=500)
    
@router.delete("/{id}")
async def delete_worker(id: int, db=Depends(connect_to_database)):
    try: 
        archive_work = """
            INSERT INTO archive_working(loader, worker, start_time, end_time, storage)
            SELECT loader, worker, start_time, end_time, storage FROM working
            WHERE worker=$1
        """
        await db.execute(archive_work, id)
        query = "DELETE FROM workers WHERE id=$1"
        result = await db.execute(query, id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404)
        return
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)

@router.post("/table/")
async def new_column_workers(name: str, value: str, db=Depends(connect_to_database)):
    try:
        query = """
            ALTER TABLE workers
                ADD COLUMN $1
                VARCHAR(100) DEFAULT $2
        """

        values = (name, value)
        await db.execute(query, *values)
    except Exception as e:
        return {"error": e}
    
@router.delete("/table/")
async def delete_column_workers(name: str, db=Depends(connect_to_database)):
    try:
        if name in ["last_name", "first_name", "id", "phone", "position", "is_free"]:
            return {"error": "can't delete this column"}
        await db.execute("ALTER TABLE workers DROP COLUMN $1", name)
    except Exception as e:
        return {"error": e}