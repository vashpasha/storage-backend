from fastapi import APIRouter, HTTPException, Depends
from db import connect_to_database
from typing import Optional

from models import LoaderParams


router = APIRouter()


@router.get("/")
async def loaders_list(status: Optional[int] = None, model: Optional[str] = None, db=Depends(connect_to_database)):
    try:
        query = "SELECT * FROM loaders"

        if status and model:
            query += " WHERE status = $1 AND model = $2"
            values = (status, model)
            items = await db.fetch(query, *values)
        elif status:
            query += " WHERE status = $1"
            items = await db.fetch(query, status)
        elif model:
            query += " WHERE model = $1"
            items = await db.fetch(query, model)
        else:        
            items = await db.fetch(query)
        return {'data': [dict(item) for item in items]}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400)
    
@router.get("/{id}")#, response_class=LoaderItem)
async def loaders_detail(id: int, db=Depends(connect_to_database)):
    item = await db.fetchrow("SELECT * FROM loaders WHERE id=$1", id)
    info = await db.fetch("SELECT workers.first_name, workers.last_name, start_time, end_time, storages.address FROM working JOIN workers ON working.worker=workers.id JOIN storages ON working.storage=storages.id WHERE loader=$1", id)
    info2 = await db.fetch("SELECT start_time, end_time, repair_companies.name, cost FROM repairing JOIN repair_companies ON repairing.repair_company=repair_companies.id  WHERE loader=$1", id)
    if item:
        return {"loader":dict(item), "works": info, "repairs": info2}
    else:
        raise HTTPException(status_code=404)


@router.post("/")
async def new_loader(item: LoaderParams, db=Depends(connect_to_database)):
    try:
        query = """
            INSERT INTO loaders(number, model, start_date, prod, status)
            VALUES ($1, $2, NOW(), $3, 7)
        """
        values = (item.number, item.model, item.prod)
        await db.execute(query, *values)
    except Exception as e:
        print("error", e)
        raise HTTPException(status_code=500)
    
@router.put("/{id}")
async def update_loader(id:int, item: LoaderParams, db=Depends(connect_to_database)):
    try:
        previous = await db.fetchrow("SELECT number, model, prod FROM loaders WHERE id=$1", id)
        query = """
            UPDATE loaders
            SET number=$1, model=$2, prod=$3, status=$4
            WHERE id=$5
            RETURNING *
        """
        values = (
            item.number or previous['number'],
            item.model or previous['model'],
            item.prod or previous['prod'],
            item.status or previous['status'],
            id
        )
        await db.execute(query, *values)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    

@router.delete("/{id}")
async def delete_loader(id: int, db=Depends(connect_to_database)):
    try: 
        archive_work = """
            INSERT INTO archive_working(loader, worker, start_time, end_time, storage)
            SELECT (loader, worker, start_time, end_time, storage) FROM working
            WHERE loader=$1
        """
        await db.execute(archive_work, id)
        archive_repair = """
            INSERT INTO archive_repairing(loader, start_time, end_time, storage, repair_company)
            SELECT (oader, start_time, end_time, storage, repair_company) FROM rapairing
            WHERE loader=$1
        """
        await db.execute(archive_repair, id)
        
        query = "DELETE FROM loaders WHERE id=$1"
        result = await db.execute(query, id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404)
        return
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)


@router.post("/table/")
async def new_column_loaders(name: str, value: str, db=Depends(connect_to_database)):
    try:
        query = """
            ALTER TABLE loaders
                ADD COLUMN $1
                VARCHAR(100) DEFAULT $2
        """

        values = (name, value)
        await db.execute(query, *values)
    except Exception as e:
        return {"error": e}
    
@router.delete("/table/")
async def delete_column_loaders(name: str, db=Depends(connect_to_database)):
    try:
        if name in ["number", "id", "model", "status", "prod", "start_date"]:
            return {"error": "can't delete this column"}
        await db.execute("ALTER TABLE loaders DROP COLUMN $1", name)
    except Exception as e:
        return {"error": e}