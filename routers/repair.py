from fastapi import APIRouter, HTTPException, Depends
from db import connect_to_database
from typing import Optional
from datetime import datetime

from models import WorkSearch, NewRepairParams, PostRepairParams


router = APIRouter()

@router.get("/")
async def repair_list(item: WorkSearch = None, db=Depends(connect_to_database)):
    query = """
        SELECT repairing.id, loaders.number, repair_companies.name, repairing.start_time, repairing.end_time, repairing.cost
        FROM repairing
        JOIN loaders ON repairing.loader=loaders.id
        JOIN repair_companies ON repairing.repair_company=repair_companies.id 
    """
    values = ()

    if item:
        query += " WHERE start_time BETWEEN $1 AND $2 and end_time BETWEEN $1 AND $2"
        values = (item.start_time, item.end_time)
    
    items = await db.fetch(query, *values)
    return [dict(item) for item in items]

@router.get("/active/")
async def repair_inprogress(db=Depends(connect_to_database)):
    query = """
        SELECT repairing.id, loaders.number, repair_companies.name, repairing.start_time, repairing.end_time, repairing.cost
        FROM repairing
        JOIN loaders ON repairing.loader=loaders.id
        JOIN repair_companies ON repairing.repair_company=repair_companies.id 
        WHERE end_time IS NULL
    """
    
    items = await db.fetch(query)
    return [dict(item) for item in items]

@router.get("/ended/")
async def repair_ended(db=Depends(connect_to_database)):
    query = """
        SELECT repairing.id, loaders.number, repair_companies.name, repairing.start_time, repairing.end_time, repairing.cost
        FROM repairing
        JOIN loaders ON repairing.loader=loaders.id
        JOIN repair_companies ON repairing.repair_company=repair_companies.id 
        WHERE end_time IS NOT NULL
    """
    
    items = await db.fetch(query)
    return [dict(item) for item in items]

@router.get("/archive/")
async def repair_archive(db=Depends(connect_to_database)):
    items = await db.fetch("SELECT * FROM archive_repairing")
    return [dict(item) for item in items]

@router.post("/new/")
async def create_new_repair(item: NewRepairParams, db=Depends(connect_to_database)):
    try:
        query = """
            INSERT INTO repairing (loader, repair_company, start_time, cost)
            VALUES ($1, $2, NOW(), $3)
        """
        values = (item.loader, item.repair_company, item.cost)
        await db.execute(query, *values)
        await db.execute("UPDATE loaders SET status=11 WHERE id=$1", item.loader)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail="giperunluck in new repair")

@router.post("/new/full/")
async def create_new_repair(item: PostRepairParams, db=Depends(connect_to_database)):
    try:
        query = """
            INSERT INTO repairing (loader, repair_company , start_time, end_time, cost)
            VALUES ($1, $2, $3, $4, $5)
        """
        values = (item.loader, item.repaire_company, item.start_time, item.end_time, item.cost)
        await db.execute(query, *values)
    except Exception as e:
        raise HTTPException(status_code=400, detail="giperunluck in new repair")

@router.put("/{repair_id}")
async def end_repair(repair_id: int, db=Depends(connect_to_database)):
    query = """
        UPDATE repairing
        SET end_time=NOW()
        WHERE id=$1
        RETURNING *
    """
    result = await db.fetchrow(query, repair_id)
    if result:
        await db.execute("UPDATE loaders SET status=7 WHERE id=$1", result['loader'])
        return
    else:
        raise HTTPException(status_code=404, detail="repair(to end) not found")
