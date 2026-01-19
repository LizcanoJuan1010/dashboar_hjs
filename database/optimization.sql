-- =============================================
-- OPTIMIZATION: Materialized Views for Dashboard
-- =============================================

-- 1. Pre-calculated Summary Stats (Instant Load)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_summary AS
SELECT
    (SELECT count(1) FROM censo_electoral) AS censo_total,
    (SELECT count(1) FROM contactos_hjs) AS contactos_hjs,
    (SELECT count(1) FROM core_empresas) AS empresas_registradas,
    NOW() as last_updated;

-- 2. Pre-calculated Coverage by Puesto (Aggregated via JOIN)
-- Matches Contacts to their Censo Puesto to calculate real coverage
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cobertura_puesto AS
WITH CensoPorPuesto AS (
    SELECT 
        cod_departamento, cod_municipio, cod_zona, cod_puesto,
        COUNT(1) as total_censo
    FROM censo_electoral
    GROUP BY 1,2,3,4
),
ContactosPorPuesto AS (
    SELECT 
        ce.cod_departamento, ce.cod_municipio, ce.cod_zona, ce.cod_puesto,
        COUNT(1) as total_contactos
    FROM contactos_hjs c
    JOIN censo_electoral ce ON c.documento = ce.documento
    GROUP BY 1,2,3,4
)
SELECT 
    d.nom_municipio,
    d.nombre_puesto,
    COALESCE(cp.total_censo, 0) as censo,
    COALESCE(hjs.total_contactos, 0) as contactos,
    CASE 
        WHEN COALESCE(cp.total_censo, 0) > 0 THEN 
            ROUND((COALESCE(hjs.total_contactos, 0)::decimal / cp.total_censo) * 100, 2)
        ELSE 0 
    END as cobertura_pct
FROM dim_divipole d
LEFT JOIN CensoPorPuesto cp ON 
    d.cod_departamento = cp.cod_departamento AND 
    d.cod_municipio = cp.cod_municipio AND 
    d.cod_zona = cp.cod_zona AND 
    d.cod_puesto = cp.cod_puesto
LEFT JOIN ContactosPorPuesto hjs ON 
    d.cod_departamento = hjs.cod_departamento AND 
    d.cod_municipio = hjs.cod_municipio AND 
    d.cod_zona = hjs.cod_zona AND 
    d.cod_puesto = hjs.cod_puesto
WHERE cp.total_censo > 0;

-- Indexes for Materialized Views to ensure fast retrieval
CREATE INDEX IF NOT EXISTS idx_mv_cobertura_puesto_pct ON mv_cobertura_puesto(cobertura_pct DESC);

-- 3. Corporate Analytics View
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_corporate_analytics AS
SELECT 
    c.tipo_empresa,
    e.nivel_educativo,
    COUNT(1) AS total
FROM empleados_empresas e
JOIN core_empresas c ON e.empresa_id = c.empresa_id
GROUP BY c.tipo_empresa, e.nivel_educativo;

-- 4. Age Distribution View
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_age_distribution AS
SELECT 
    CASE 
        WHEN EXTRACT(YEAR FROM AGE(fecha_nacimiento)) < 18 THEN 'Menores de 18'
        WHEN EXTRACT(YEAR FROM AGE(fecha_nacimiento)) BETWEEN 18 AND 30 THEN '18-30'
        WHEN EXTRACT(YEAR FROM AGE(fecha_nacimiento)) BETWEEN 31 AND 60 THEN '31-60'
        WHEN EXTRACT(YEAR FROM AGE(fecha_nacimiento)) > 60 THEN 'Mayor de 60'
        ELSE 'Desconocido'
    END AS rango_edad,
    sexo,
    COUNT(1) AS total
FROM empleados_empresas
GROUP BY 1, 2;
