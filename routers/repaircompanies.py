from fastapi import APIRouter, HTTPException, Depends
from db import connect_to_database

from models import RepairCoParams


router = APIRouter()

@router.get("/")
async def status_list(db=Depends(connect_to_database)):
    items = await db.fetch("SELECT * FROM repair_companies")
    return {'data': [dict(item) for item in items]}

@router.post("/")
async def new_repair_company(item: RepairCoParams, db=Depends(connect_to_database)):
    try:
        query = """
            INSERT INTO repair_companies(name, address, phone)
            VALUES ($1, $2, $3)
        """
        values = (item.name, item.address, item.phone)
        
        await db.execute(query, *values)
        return
    except Exception as e:
        raise HTTPException(status_code=500)
        
@router.put("/{id}")
async def update_loader(id:int, item: RepairCoParams, db=Depends(connect_to_database)):
    try:
        previous = await db.fetchrow("SELECT name, phone, address FROM repair_companies WHERE id=$1", id)
        query = """
            UPDATE repair_companies
            SET name=$1, phone=$2, address=$3
            WHERE id=$4
        """
        values = (
            item.name or previous['name'],
            item.phone or previous['phone'],
            item.address or previous['address'],
            id
        )
        await db.execute(query, *values)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    
@router.delete("/{id}")
async def delete_repair_company(id: int, db=Depends(connect_to_database)):
    try:
        archive_repair = """
            INSERT INTO archive_repairing(loader, start_time, end_time, cost, repair_company)
            SELECT loader, start_time, end_time, cost, repair_company FROM repairing
            WHERE repair_company=$1
        """
        await db.execute(archive_repair, id)
        query = "DELETE FROM repair_companies WHERE id = $1"
        result = await db.execute(query, id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404)
        return
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    
@router.post("/table/")
async def new_column_repco(name: str, value: str, db=Depends(connect_to_database)):
    try:
        query = """
            ALTER TABLE repair_companies
                ADD COLUMN $1
                VARCHAR(100) DEFAULT $2
        """

        values = (name, value)
        await db.execute(query, *values)
    except Exception as e:
        return {"error": e}
    
@router.delete("/table/")
async def delete_column_repco(name: str, db=Depends(connect_to_database)):
    try:
        
        if name in ["name", "id", "phone", "address"]:
            return {"error": "can't delete this column"}
        await db.execute("ALTER TABLE repair_companies DROP COLUMN $1", name)
    except Exception as e:
        return {"error": e}