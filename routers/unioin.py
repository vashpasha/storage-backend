from fastapi import APIRouter, HTTPException, Depends
from db import connect_to_database
from datetime import datetime
from typing import Optional

from models import WorkSearch


router = APIRouter()

@router.get("/worktime/")
async def get_loaders(start: Optional[datetime] = None, end: Optional[datetime] = None, db=Depends(connect_to_database)):
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

        if start and end:
            values = (start, end)
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
        return {'data': [dict(item) for item in items]}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    
@router.get("/repairtime/")
async def get_loaders(start: Optional[datetime] = None, end: Optional[datetime] = None, db=Depends(connect_to_database)):
    try:
        values = ()
        query = """
            WITH loader_repair_time AS (
                SELECT
                    loader,
                    SUM(EXTRACT(EPOCH FROM (end_time - start_time))) AS total_seconds,
                    SUM(cost) AS total_cost
                FROM
                    repairing
        """
        
        if start and end:
            values = (start, end)
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
                ) AS total_repair_time,
                repair_time.total_cost AS total_repair_cost
            FROM loaders
            JOIN loader_repair_time  AS repair_time ON loaders.id=repair_time.loader;
        """
        items = await db.fetch(query, *values)
        return {'data': [dict(item) for item in items]}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    

@router.get("/")
async def all_info(start: Optional[datetime] = None, end: Optional[datetime] = None, db=Depends(connect_to_database)):
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
    
    if start and end:
        values = (start, end)
        query += " WHERE start_time BETWEEN $1 AND $2 and end_time BETWEEN $1 AND $2"
    
    query += " ORDER BY start_time"
    items = await db.fetch(query, *values)
    return {'data': [dict(item) for item in items]}


@router.get("/{id}")
async def all_info(id: int, start: Optional[datetime] = None, end: Optional[datetime] = None, db=Depends(connect_to_database)):
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
    
    if start and end:
        values += (start, end)
        query += " AND start_time BETWEEN $2 AND $3 and end_time BETWEEN $2 AND $3"

    query += " ORDER BY start_time"
    items = await db.fetch(query, *values)
    return {'data': [dict(item) for item in items]}


@router.get("/hours/")
async def pricol(db=Depends(connect_to_database)):
    try:
        loaders = await db.fetch("select number from loaders")
        loaders = [item[0] for item in loaders]

        loader_cols = ', '.join([
            f"COALESCE(SUM(CASE WHEN l.number = '{number}' THEN lh.hours_worked else 0 end), 0) as {number}"
            for number in loaders
        ])

        query = f"""
            WITH month_series AS (
                SELECT 
                    generate_series(
                        date_trunc('month', current_date - interval '11 month'), 
                        date_trunc('month', current_date), 
                        interval '1 month'
                    ) AS month
            ),
            loader_hours AS (
                SELECT 
                    DATE_TRUNC('month', start_time) AS month,
                    loader,
                    ROUND(SUM(EXTRACT(epoch FROM (COALESCE(end_time, current_timestamp) - start_time)) / 3600), 2) AS hours_worked
                FROM 
                    working
                WHERE 
                    start_time >= current_date - interval '11 month'
                GROUP BY 
                    month, loader
            )
            SELECT 
                to_char(ms.month, 'YYYY-MM') AS month,
                {loader_cols}
            FROM 
                month_series ms
            CROSS JOIN 
                loaders l
            LEFT JOIN 
                loader_hours lh ON DATE_TRUNC('month', lh.month) = ms.month AND l.id = lh.loader
            GROUP BY 
                ms.month
            ORDER BY 
                ms.month
        """

        result = await db.fetch(query)
        return {'headers': loaders,'data': [item for item in result]}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)