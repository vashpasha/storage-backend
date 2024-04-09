from fastapi import APIRouter, HTTPException, Depends
from db import connect_to_database

from models import WorkSearch


router = APIRouter()

@router.get("/worktime/")
async def get_loaders(item: WorkSearch = None, db=Depends(connect_to_database)):
    try:
        values = ()
        query = """
            WITH loader_work_time AS (
                SELECT
                    loader,
                    SUM(EXTRACT(EPOCH FROM (end_time - start_time))) AS total_seconds
                FROM
                    working
        """

        if item:
            values = (item.start_time, item.end_time)
            query += "WHERE start_time BETWEEN $1 AND $2 AND end_time BETWEEN $1 AND $2"

        query += """
                GROUP BY loader
            )
            SELECT 
                loaders.id, 
                loaders.number, 
                loaders.model,
                TO_CHAR(
                    INTERVAL '1 second' * work_time.total_seconds,
                    'HH24:MI:SS'
                ) AS total_work_time
            FROM loaders
            JOIN loader_work_time  AS work_time ON loaders.id=work_time.loader;
        """
        items = await db.fetch(query, *values)
        return [dict(item) for item in items]
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    
@router.get("/repairtime/")
async def get_loaders(item: WorkSearch = None, db=Depends(connect_to_database)):
    try:
        values = ()
        query = """
            WITH loader_repair_time AS (
                SELECT
                    loader,
                    SUM(EXTRACT(EPOCH FROM (end_time - start_time))) AS total_seconds
                FROM
                    repairing
        """

        if item:
            values = (item.start_time, item.end_time)
            query += "WHERE start_time BETWEEN $1 AND $2 AND end_time BETWEEN $1 AND $2"

        query += """
                GROUP BY loader
            )
            SELECT 
                loaders.id, 
                loaders.number, 
                loaders.model,
                TO_CHAR(
                    INTERVAL '1 second' * repair_time.total_seconds,
                    'HH24:MI:SS'
                ) AS total_repair_time
            FROM loaders
            JOIN loader_repair_time  AS repair_time ON loaders.id=repair_time.loader;
        """
        items = await db.fetch(query, *values)
        return [dict(item) for item in items]
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    

@router.get("/")
async def all_info(item: WorkSearch = None, db=Depends(connect_to_database)):
    values = ()
    query = """
        SELECT * FROM (
        SELECT working.loader, working.start_time, working.end_time, storages.address 
	        FROM working
	        JOIN storages
	        ON working.storage=storages.id
        union
        SELECT repairing.loader, repairing.start_time, repairing.end_time, repair_companies.address
	        FROM repairing
	        JOIN repair_companies
	        ON repairing.repair_company=repair_companies.id
        ) AS merged_data
    """
    if item:
        query += " WHERE start_time BETWEEN $1 AND $2 and end_time BETWEEN $1 AND $2"
        values = (item.start_time, item.end_time)
    
    query += " ORDER BY start_time"
    items = await db.fetch(query, *values)
    return [dict(item) for item in items]


@router.get("/{id}")
async def all_info(id: int, item: WorkSearch = None , db=Depends(connect_to_database)):
    query = """
        SELECT * FROM (
        SELECT working.loader, working.start_time, working.end_time, storages.address 
	        FROM working
	        JOIN storages
	        ON working.storage=storages.id
        union
        SELECT repairing.loader, repairing.start_time, repairing.end_time, repair_companies.address
	        FROM repairing
	        JOIN repair_companies
	        ON repairing.repair_company=repair_companies.id
        ) AS merged_data
        WHERE loader=$1 
    """
    values = (id, )
    if item:
        query += " AND start_time BETWEEN $2 AND $3 and end_time BETWEEN $2 AND $3"
        values += (item.start_time, item.end_time)

    query += " ORDER BY start_time"
    items = await db.fetch(query, *values)
    return [dict(item) for item in items]