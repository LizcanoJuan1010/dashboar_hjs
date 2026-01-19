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
    query = """
    WITH CensoPorPuesto AS (
        SELECT cod_departamento, cod_municipio, cod_zona, cod_puesto, COUNT(*) as total_censo
        FROM censo_electoral GROUP BY 1,2,3,4
    ),
    ContactosPorMunicipio AS (
        SELECT cod_departamento, cod_municipio, COUNT(*) as total_contactos
        FROM contactos_hjs GROUP BY 1,2
    )
    SELECT 
        d.cod_departamento,
        d.nom_departamento AS departamento,
        d.nom_municipio AS municipio,
        d.nombre_puesto AS puesto,
        COALESCE(cp.total_censo, 0) as censo,
        -- Distribute contacts proportional to censo if we wanted to estimate, 
        -- but simpler to just show 0 at puesto level or show aggregate at municipality level.
        -- Given user request: "show info of depts and municipios", we will actually modify this to return municipality level rows mainly? 
        -- BUT frontend expects 'puesto' field. 
        -- Strategy: We will join contacts at municipality level. This means every puesto in the same municipality shows the SAME total contacts for the municipality? 
        -- No, that interprets as "contacts in this puesto". 
        -- Better: Show 0 for puesto-level matches, and maybe we rely on a different visualization for municipality coverage.
        -- However, the user said "mejore que solo muestre informacion de departamentos y municipios".
        -- Let's TRY to return municipality-aggregated data, setting 'puesto' to 'TODOS'.
        COALESCE(hjs.total_contactos, 0) as contactos,
        ROUND((COALESCE(hjs.total_contactos, 0)::decimal / NULLIF(SUM(cp.total_censo) OVER (PARTITION BY d.cod_departamento, d.cod_municipio), 0)) * 100, 2) as cobertura_pct
    FROM dim_divipole d
    LEFT JOIN CensoPorPuesto cp ON 
        d.cod_departamento = cp.cod_departamento AND 
        d.cod_municipio = cp.cod_municipio AND 
        d.cod_zona = cp.cod_zona AND 
        d.cod_puesto = cp.cod_puesto
    LEFT JOIN ContactosPorMunicipio hjs ON 
        d.cod_departamento = hjs.cod_departamento AND 
        d.cod_municipio = hjs.cod_municipio
    WHERE cp.total_censo > 0
    -- To adhere to "only depts/muni", we might want to group by municipality?
    -- But the frontend likely expects distinct rows per puesto.
    -- Let's just create a query that aggregates by municipality and returns that.
    -- But we need to check if frontend breaks if 'cod_puesto' is missing.
    -- Returning dataset aggregated by Municipality for now, mocking Puesto as 'GENERAL'
    GROUP BY d.cod_departamento, d.nom_departamento, d.nom_municipio, hjs.total_contactos
    ORDER BY cobertura_pct DESC
    LIMIT :limit;
    """
    # ACTUALLY, simpler approach:
    # 1. Aggregate censo by municipality
    # 2. Join with contacts by municipality
    # 3. Return rows where each row is a municipality
    query = """
    SELECT 
        d.cod_departamento,
        MAX(d.nom_departamento) AS departamento,
        d.nom_municipio AS municipio,
        'GENERAL' AS puesto,
        COUNT(c.documento) as censo,
        (SELECT COUNT(*) FROM contactos_hjs h WHERE h.cod_departamento = d.cod_departamento AND h.cod_municipio = d.cod_municipio) as contactos,
        0 as cobertura_pct -- calculated in frontend or simpler math
    FROM dim_divipole d
    LEFT JOIN censo_electoral c ON d.cod_municipio = c.cod_municipio AND d.cod_departamento = c.cod_departamento
    GROUP BY d.cod_departamento, d.cod_municipio, d.nom_municipio
    ORDER BY contactos DESC
    LIMIT :limit;
    """
    # RE-THINKING based on user request "show info of depts and municipios"
    # and keeping the frontend happy (which expects 'puesto').
    # I will construct a query that returns Municipios as the grain.
    query = """
    WITH CensoMuni AS (
        SELECT cod_departamento, cod_municipio, COUNT(*) as total_censo
        FROM censo_electoral GROUP BY 1,2
    ),
    ContactosMuni AS (
        SELECT cod_departamento, cod_municipio, COUNT(*) as total_contactos
        FROM contactos_hjs GROUP BY 1,2
    )
    SELECT 
        d.cod_departamento,
        d.nom_departamento AS departamento,
        d.nom_municipio AS municipio,
        'AGREGADO MUNICIPAL' AS puesto,
        COALESCE(c.total_censo, 0) as censo,
        COALESCE(h.total_contactos, 0) as contactos,
        CASE WHEN c.total_censo > 0 THEN 
            ROUND((COALESCE(h.total_contactos, 0)::decimal / c.total_censo) * 100, 2)
        ELSE 0 END as cobertura_pct
    FROM (SELECT DISTINCT cod_departamento, cod_municipio, nom_departamento, nom_municipio FROM dim_divipole) d
    LEFT JOIN CensoMuni c ON d.cod_departamento = c.cod_departamento AND d.cod_municipio = c.cod_municipio
    LEFT JOIN ContactosMuni h ON d.cod_departamento = h.cod_departamento AND d.cod_municipio = h.cod_municipio
    WHERE c.total_censo > 0 OR h.total_contactos > 0
    ORDER BY cobertura_pct DESC
    LIMIT :limit;
    """
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

@app.get("/api/analytics/education-level")
async def get_education_level():
    query = """
    SELECT 
        div.cod_departamento,
        COALESCE(div.nom_departamento, 'Desconocido') AS departamento,
        COALESCE(div.nom_municipio, 'Desconocido') AS municipio,
        COALESCE(e.nivel_educativo, 'No Registrado') AS nivel_educativo,
        COUNT(*) AS total_personas
    FROM empleados_empresas e
    LEFT JOIN (
        SELECT DISTINCT cod_departamento, cod_municipio, nom_municipio, nom_departamento 
        FROM dim_divipole
    ) div ON e.cod_departamento = div.cod_departamento AND e.cod_municipio = div.cod_municipio
    GROUP BY div.cod_departamento, div.nom_departamento, div.nom_municipio, e.nivel_educativo
    ORDER BY departamento, municipio, total_personas DESC;
    """
    rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

@app.get("/api/analytics/sex-distribution")
async def get_sex_distribution():
    query = """
    SELECT 
        div.cod_departamento,
        COALESCE(div.nom_departamento, 'Desconocido') AS departamento,
        e.sexo,
        COUNT(*) AS total
    FROM empleados_empresas e
    LEFT JOIN (
        SELECT DISTINCT cod_departamento, cod_municipio, nom_departamento 
        FROM dim_divipole
    ) div ON e.cod_departamento = div.cod_departamento AND e.cod_municipio = div.cod_municipio
    WHERE e.sexo IS NOT NULL
    GROUP BY div.cod_departamento, div.nom_departamento, e.sexo
    ORDER BY departamento, e.sexo;
    """
    rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

@app.get("/api/analytics/top-companies")
async def get_top_companies():
    query = """
    SELECT 
        div.cod_departamento,
        c.razon_social AS empresa,
        c.nit,
        c.tipo_empresa AS tipo,
        COALESCE(div.nom_departamento, 'Desconocido') AS departamento,
        COUNT(e.empleado_id) AS total_empleados
    FROM core_empresas c
    JOIN empleados_empresas e ON c.empresa_id = e.empresa_id
    LEFT JOIN (
        SELECT DISTINCT cod_departamento, cod_municipio, nom_departamento 
        FROM dim_divipole
    ) div ON c.municipio_cod = div.cod_departamento || div.cod_municipio
    GROUP BY div.cod_departamento, c.empresa_id, c.razon_social, c.nit, c.tipo_empresa, div.nom_departamento
    ORDER BY total_empleados DESC
    LIMIT 50;
    """
    rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

@app.get("/api/analytics/puestos-demographics")
async def get_puestos_demographics():
    query = """
    SELECT 
        d.cod_departamento,
        d.nom_departamento AS departamento,
        d.nom_municipio AS municipio,
        d.nombre_puesto AS puesto,
        d.cod_puesto AS codigo_puesto,
        SUM(CASE WHEN e.sexo = 'M' THEN 1 ELSE 0 END) AS hombres,
        SUM(CASE WHEN e.sexo = 'F' THEN 1 ELSE 0 END) AS mujeres,
        COUNT(*) AS total_general
    FROM dim_divipole d
    JOIN empleados_empresas e ON 
        d.cod_departamento = e.cod_departamento AND
        d.cod_municipio = e.cod_municipio
    GROUP BY d.cod_departamento, d.nom_departamento, d.nom_municipio, d.nombre_puesto, d.cod_puesto
    ORDER BY total_general DESC
    LIMIT 200;
    """
    rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

@app.get("/api/analytics/leader-efficiency")
async def get_leader_efficiency():
    query = """
    SELECT 
        div.cod_departamento,
        l.nombre_completo AS lider,
        l.meta_votos,
        (COALESCE(l.pendones, 0) + COALESCE(l.boletas_bingo, 0) + COALESCE(l.damas_gratis, 0)) AS total_recursos,
        l.comuna,
        COALESCE(div.nom_departamento, 'Desconocido') AS departamento
    FROM lideres_campana l
    LEFT JOIN (
        SELECT DISTINCT cod_departamento, cod_municipio, nom_departamento 
        FROM dim_divipole
    ) div ON l.cod_municipio = div.cod_municipio
    WHERE l.meta_votos > 0
    ORDER BY total_recursos DESC
    LIMIT 100;
    """
    rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

@app.get("/api/analytics/company-timeline")
async def get_company_timeline():
    query = """
    SELECT 
        div.cod_departamento,
        TO_CHAR(c.fecha_constitucion, 'YYYY') AS anio,
        COALESCE(div.nom_departamento, 'Desconocido') AS departamento,
        COUNT(*) AS total_empresas
    FROM core_empresas c
    LEFT JOIN (
        SELECT DISTINCT cod_departamento, cod_municipio, nom_departamento 
        FROM dim_divipole
    ) div ON c.municipio_cod = div.cod_departamento || div.cod_municipio
    WHERE c.fecha_constitucion IS NOT NULL
    GROUP BY div.cod_departamento, 1, 2
    ORDER BY 1;
    """
    rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

@app.get("/api/analytics/mesas-by-dept")
async def get_mesas_by_dept(cod_dept: str = None):
    if cod_dept:
        query = """
        SELECT 
            cod_departamento,
            nom_departamento AS departamento,
            COUNT(*) AS total_mesas
        FROM dim_divipole
        WHERE cod_departamento = :cod_dept
        GROUP BY cod_departamento, nom_departamento;
        """
        rows = await database.fetch_all(query=query, values={"cod_dept": cod_dept})
    else:
        query = """
        SELECT 
            cod_departamento,
            nom_departamento AS departamento,
            COUNT(*) AS total_mesas
        FROM dim_divipole
        WHERE nom_departamento IS NOT NULL
        GROUP BY cod_departamento, nom_departamento
        ORDER BY total_mesas DESC;
        """
        rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

@app.get("/api/analytics/empresas-by-dept")
async def get_empresas_by_dept(cod_dept: str = None):
    if cod_dept:
        query = """
        SELECT 
            d.cod_departamento,
            d.nom_departamento AS departamento,
            COUNT(DISTINCT c.empresa_id) AS total_empresas
        FROM core_empresas c
        JOIN (
            SELECT DISTINCT cod_municipio, cod_departamento, nom_departamento 
            FROM dim_divipole
        ) d ON c.municipio_cod = d.cod_departamento || d.cod_municipio
        WHERE d.cod_departamento = :cod_dept
        GROUP BY d.cod_departamento, d.nom_departamento;
        """
        rows = await database.fetch_all(query=query, values={"cod_dept": cod_dept})
    else:
        query = """
        SELECT 
            d.cod_departamento,
            COALESCE(d.nom_departamento, 'Desconocido') AS departamento,
            COUNT(DISTINCT c.empresa_id) AS total_empresas
        FROM core_empresas c
        LEFT JOIN (
            SELECT DISTINCT cod_municipio, cod_departamento, nom_departamento 
            FROM dim_divipole
        ) d ON c.municipio_cod = d.cod_departamento || d.cod_municipio
        GROUP BY d.cod_departamento, d.nom_departamento
        ORDER BY total_empresas DESC;
        """
        rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

# Drill-down: Municipalities in a department
@app.get("/api/analytics/municipios-by-dept")
async def get_municipios_by_dept(cod_dept: str):
    query = """
    SELECT 
        cod_municipio,
        nom_municipio AS municipio,
        COUNT(*) AS total_mesas
    FROM dim_divipole
    WHERE cod_departamento = :cod_dept
    GROUP BY cod_municipio, nom_municipio
    ORDER BY total_mesas DESC;
    """
    rows = await database.fetch_all(query=query, values={"cod_dept": cod_dept})
    return [dict(row) for row in rows]

# Drill-down: Puestos in a municipality
@app.get("/api/analytics/puestos-by-muni")
async def get_puestos_by_muni(cod_muni: str, cod_dept: str):
    query = """
    SELECT 
        cod_puesto,
        nombre_puesto AS puesto,
        direccion_puesto AS direccion,
        COUNT(*) AS total_mesas
    FROM dim_divipole
    WHERE cod_municipio = :cod_muni AND cod_departamento = :cod_dept
    GROUP BY cod_puesto, nombre_puesto, direccion_puesto
    ORDER BY total_mesas DESC
    LIMIT 50;
    """
    rows = await database.fetch_all(query=query, values={"cod_muni": cod_muni, "cod_dept": cod_dept})
    return [dict(row) for row in rows]

# Summary with optional department filter
@app.get("/api/geo/summary")
async def get_geo_summary(cod_dept: str = None):
    if cod_dept:
        query = """
        SELECT
            (SELECT COUNT(*) FROM censo_electoral WHERE cod_departamento = :cod_dept) AS censo_total,
            (SELECT COUNT(*) FROM contactos_hjs WHERE cod_departamento = :cod_dept) AS contactos_hjs,
            (SELECT COUNT(DISTINCT c.empresa_id) 
             FROM core_empresas c 
             JOIN (SELECT DISTINCT cod_municipio, cod_departamento FROM dim_divipole WHERE cod_departamento = :cod_dept) d 
             ON c.municipio_cod = d.cod_departamento || d.cod_municipio) AS empresas_registradas,
            (SELECT COUNT(*) 
             FROM empleados_empresas 
             WHERE cod_departamento = :cod_dept) AS empleados_registrados,
            (SELECT COUNT(email) FROM empleados_empresas WHERE cod_departamento = :cod_dept AND email IS NOT NULL AND email != '') AS total_emails,
            (SELECT COUNT(celular) FROM empleados_empresas WHERE cod_departamento = :cod_dept AND celular IS NOT NULL AND celular != '') AS total_celulares
        """
        row = await database.fetch_one(query=query, values={"cod_dept": cod_dept})
    else:
        query = """
        SELECT
            (SELECT COUNT(*) FROM censo_electoral) AS censo_total,
            (SELECT COUNT(*) FROM contactos_hjs) AS contactos_hjs,
            (SELECT COUNT(*) FROM core_empresas) AS empresas_registradas,
            (SELECT COUNT(*) FROM empleados_empresas) AS empleados_registrados,
            (SELECT COUNT(email) FROM empleados_empresas WHERE email IS NOT NULL AND email != '') AS total_emails,
            (SELECT COUNT(celular) FROM empleados_empresas WHERE celular IS NOT NULL AND celular != '') AS total_celulares
        """
        row = await database.fetch_one(query=query)
    return dict(row)

# Contact Info Endpoint
@app.get("/api/analytics/contact-info")
async def get_contact_info(limit: int = 100):
    query = """
    SELECT 
        documento,
        nombre_completo,
        celular,
        email
    FROM empleados_empresas
    WHERE celular IS NOT NULL OR email IS NOT NULL
    LIMIT :limit;
    """
    rows = await database.fetch_all(query=query, values={"limit": limit})
    return [dict(row) for row in rows]

# Upcoming Birthdays Endpoint
@app.get("/api/analytics/upcoming-birthdays")
async def get_upcoming_birthdays(limit: int = 100):
    # Logic to find upcoming birthdays relative to current date, ignoring year
    query = """
    SELECT 
        documento,
        nombre_completo,
        celular,
        email,
        fecha_nacimiento,
        -- Calculate days until next birthday
        (
            EXTRACT(DOY FROM fecha_nacimiento) - EXTRACT(DOY FROM CURRENT_DATE) + 365
        )::int % 365 AS days_until_birthday
    FROM empleados_empresas
    WHERE fecha_nacimiento IS NOT NULL
    ORDER BY days_until_birthday ASC
    LIMIT :limit;
    """
    rows = await database.fetch_all(query=query, values={"limit": limit})
    return [dict(row) for row in rows]
