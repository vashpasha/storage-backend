from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class LoaderParams(BaseModel):
    number: Optional[str] = None
    model: Optional[str] = None
    prod: Optional[int] = None
    status: Optional[int] = None
    
class PositionsParams(BaseModel):
    name: Optional[str] = None
    salary: Optional[Decimal] = None

class StatusesParams(BaseModel):
    name: Optional[str] = None

class ProdsParams(BaseModel):
    name: str
    phone: str
    country: str

class WorkItem(BaseModel):
    id: int
    loader: int
    worker: int
    storage: int
    start_time: datetime
    end_time: datetime

class NewWorkParams(BaseModel):
    loader: int
    worker: int
    storage: int

class PostWorkParams(NewWorkParams):
    start_time: datetime
    end_time: datetime


class RepairItem(BaseModel):
    id: int
    loader: int
    repair_company: int
    start_time: datetime
    end_time: datetime
    cost: Decimal

class NewRepairParams(BaseModel):
    loader: int
    repair_company: int
    cost: Decimal

class PostRepairParams(NewRepairParams):
    start_time: datetime
    end_time: datetime


class StorageParams(BaseModel):
    address: str

class RepairCoParams(BaseModel):
    name: str
    address: str
    phone: str

class WorkSearch(BaseModel):
    start_time: datetime
    end_time: datetime
    
class WorkerParams(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[int] = None
    phone: Optional[str] = None
