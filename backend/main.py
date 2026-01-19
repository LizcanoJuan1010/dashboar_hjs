from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import databases
from pydantic import BaseModel
from typing import List, Optional, Any

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

database = databases.Database(DATABASE_URL)

app = FastAPI(title="HJS Analytics Dashboard")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    try:
        await database.connect()
    except Exception as e:
        print(f"DB Connection Error: {e}")

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/")
def read_root():
    return {"status": "online", "version": "1.0.0"}

# --- ANALYTICS ENDPOINTS ---

@app.get("/api/analytics/company-heatmap")
async def get_company_heatmap():
    query = "SELECT * FROM mv_corporate_analytics ORDER BY total DESC"
    rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

@app.get("/api/analytics/age-distribution")
async def get_age_distribution():
    query = "SELECT * FROM mv_age_distribution ORDER BY rango_edad"
    rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

@app.get("/api/analytics/coverage-by-puesto")
async def get_coverage_by_puesto(limit: int = 100):
    query = "SELECT * FROM mv_cobertura_puesto ORDER BY cobertura_pct DESC LIMIT :limit"
    rows = await database.fetch_all(query=query, values={"limit": limit})
    return [dict(row) for row in rows]

@app.get("/api/analytics/verified-leaders")
async def get_verified_leaders():
    query = """
    SELECT 
        l.comuna,
        COUNT(*) as total_lideres,
        SUM(CASE WHEN l.verificado = 'SI' THEN 1 ELSE 0 END) as lideres_verificados,
        SUM(l.meta_votos) as meta_total_votos
    FROM lideres_campana l
    GROUP BY l.comuna
    ORDER BY meta_total_votos DESC;
    """
    rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

@app.get("/api/geo/summary")
async def get_geo_summary():
    query = "SELECT * FROM mv_dashboard_summary"
    row = await database.fetch_one(query)
    return dict(row)
