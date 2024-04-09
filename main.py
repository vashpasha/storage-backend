from fastapi import FastAPI
from db import connect_to_database, close_database_connection
from fastapi.middleware.cors import CORSMiddleware

from routers.loaders import router as loader_router
from routers.prods import router as prods_router
from routers.statuses import router as status_router
from routers.work import router as work_router
from routers.repair import router as repair_router
from routers.repaircompanies import router as repaircompanies_router
from routers.storages import router as storages_router
from routers.positions import router as position_router
from routers.workers import router as workers_router
from routers.unioin import router as docs_router

app = FastAPI()


app.include_router(loader_router, prefix="/loaders")
app.include_router(prods_router, prefix="/prods")
app.include_router(status_router, prefix="/statuses")
app.include_router(work_router, prefix="/work")
app.include_router(repair_router, prefix="/repair")
app.include_router(repaircompanies_router, prefix="/repaircompanies")
app.include_router(storages_router, prefix="/storages")
app.include_router(docs_router, prefix="/docs")
app.include_router(position_router, prefix="/positions")
app.include_router(workers_router, prefix="/worker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Access-Control-Allow-Headers", "Access-Control-Allow-Origin", "Access-Control-Allow-Credentials"],
)
@app.on_event("startup")
async def startup_event():
    app.state.db = await connect_to_database()

@app.on_event("shutdown")
async def shutdown_event():
    await close_database_connection(app.state.db)
