from fastapi import APIRouter, HTTPException, Depends
from db import connect_to_database
from typing import Optional
from datetime import datetime

from random import choices

from models import WorkSearch, NewWorkParams, PostWorkParams


router = APIRouter()

@router.get("/")
async def work_list(item: WorkSearch = None, db=Depends(connect_to_database)):
    query = """
        SELECT working.id, loaders.number, workers.first_name, workers.last_name, working.start_time, working.end_time, storages.address
        FROM working 
        JOIN workers ON working.worker=workers.id 
        JOIN loaders ON working.loader=loaders.id
        JOIN storages ON working.storage=storages.id
    """
    values = ()  # Define an empty tuple here

    if item:
        query += " WHERE start_time BETWEEN $1 AND $2 and end_time BETWEEN $1 AND $2"
        values = (item.start_time, item.end_time)
    
    items = await db.fetch(query, *values)
    print(query)
    return [dict(item) for item in items]

@router.get("/active/")
async def work_inprogress(db=Depends(connect_to_database)):
    query = """
        SELECT working.id, loaders.number, workers.first_name, workers.last_name, working.start_time, working.end_time, storages.address
        FROM working 
        JOIN workers ON working.worker=workers.id 
        JOIN loaders ON working.loader=loaders.id
        JOIN storages ON working.storage=storages.id
        WHERE end_time IS NULL
    """
    
    items = await db.fetch(query)
    return [dict(item) for item in items]

@router.get("/ended/")
async def work_ended(db=Depends(connect_to_database)):
    query = """
        SELECT working.id, loaders.number, workers.first_name, workers.last_name, working.start_time, working.end_time, storages.address
        FROM working 
        JOIN workers ON working.worker=workers.id 
        JOIN loaders ON working.loader=loaders.id
        JOIN storages ON working.storage=storages.id
        WHERE end_time IS NOT NULL
    """
    
    items = await db.fetch(query)
    return [dict(item) for item in items]

@router.get("/archive/")
async def repair_archive(db=Depends(connect_to_database)):
    items = await db.fetch("SELECT * FROM archive_working")
    return [dict(item) for item in items]


@router.post("/new/")
async def create_new_work(item: NewWorkParams, db=Depends(connect_to_database)):
    try:
        query = """
            INSERT INTO working (loader, worker, start_time, storage)
            VALUES ($1, $2, NOW(), $3)
        """
        values = (item.loader, item.worker, item.storage)
        await db.execute(query, *values)
        await db.execute("UPDATE workers SET is_free=False WHERE id=$1", item.worker)
        await db.execute("UPDATE loaders SET status=10 WHERE id=$1", item.loader)
    except Exception as e:
        raise HTTPException(status_code=400, detail="giperunluck in new work")


@router.post("/new/full/")
async def create_new_work(item: PostWorkParams, db=Depends(connect_to_database)):
    try:
        query = """
            INSERT INTO working (loader, worker, start_time, end_time, storage)
            VALUES ($1, $2, $3, $4, $5)
        """
        values = (item.loader, item.worker, item.start_time, item.end_time,item.storage)
        await db.execute(query, *values)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail="giperunluck in new work")

@router.put("/{work_id}")
async def end_work(work_id: int, db=Depends(connect_to_database)):
    try:
        query = """
            UPDATE working
            SET end_time=NOW()
            WHERE id=$1
            RETURNING *
        """
        result = await db.fetchrow(query, work_id)
        if result:
            new_status = choices([7, 8], weights=[7, 1])[0]
            await db.execute("UPDATE loaders SET status=$1 WHERE id=$2", new_status, result['loader'])
            await db.execute("UPDATE workers SET is_free=True WHERE id=$1", result['worker'])
            
            time = await db.fetchrow("select start_time, end_time from working where id=$1", id)
            start_time, end_time = datetime(time['start_time']), datetime(time['end_time'])
            duration = start_time-end_time
            duration = duration.total_seconds()

            if duration > 8*60*60+15*60:
                return {"message": "WORK MORE THAT 8 HOURS IT IS VERY BAD :("}
            return
        else:
            raise HTTPException(status_code=404, detail="work(to end) not found")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
