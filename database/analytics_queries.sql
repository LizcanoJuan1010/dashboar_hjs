-- ==========================================
-- 1. CORPORATE HEATMAP: Company Type vs Education Level
-- ==========================================
SELECT 
    c.tipo_empresa AS "Tipo Empresa",
    e.nivel_educativo AS "Nivel Educativo",
    COUNT(*) AS "Total Empleados"
FROM empleados_empresas e
JOIN core_empresas c ON e.empresa_id = c.empresa_id
GROUP BY c.tipo_empresa, e.nivel_educativo
ORDER BY c.tipo_empresa, "Total Empleados" DESC;

-- ==========================================
-- 2. AGE DISTRIBUTION (Employees)
-- ==========================================
SELECT 
    CASE 
        WHEN EXTRACT(YEAR FROM AGE(fecha_nacimiento)) < 18 THEN 'Menores de 18'
        WHEN EXTRACT(YEAR FROM AGE(fecha_nacimiento)) BETWEEN 18 AND 30 THEN '18-30'
        WHEN EXTRACT(YEAR FROM AGE(fecha_nacimiento)) BETWEEN 31 AND 60 THEN '31-60'
        WHEN EXTRACT(YEAR FROM AGE(fecha_nacimiento)) > 60 THEN 'Mayor de 60'
        ELSE 'Desconocido'
    END AS "Rango Edad",
    sexo,
    COUNT(*) AS "Total"
FROM empleados_empresas
GROUP BY 1, 2
ORDER BY 1;

-- ==========================================
-- 3. HJS CAMPAIGN COVERAGE (By Puesto)
-- ==========================================
WITH CensoPorPuesto AS (
    SELECT 
        cod_departamento, cod_municipio, cod_zona, cod_puesto,
        COUNT(*) as total_censo
    FROM censo_electoral
    GROUP BY 1,2,3,4
),
ContactosPorPuesto AS (
    SELECT 
        cod_departamento, cod_municipio, cod_zona, cod_puesto,
        COUNT(*) as total_contactos
    FROM contactos_hjs GROUP BY 1,2,3,4
)
SELECT 
    d.nom_municipio,
    d.nombre_puesto,
    COALESCE(cp.total_censo, 0) as censo,
    COALESCE(hjs.total_contactos, 0) as contactos,
    ROUND((COALESCE(hjs.total_contactos, 0)::decimal / NULLIF(cp.total_censo, 0)) * 100, 2) as "Cobertura %"
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
WHERE cp.total_censo > 0
ORDER BY "Cobertura %" DESC;

-- ==========================================
-- 4. VERIFIED LEADERS (Efficiency)
-- ==========================================
SELECT 
    l.comuna,
    COUNT(*) as total_lideres,
    SUM(CASE WHEN l.verificado = 'SI' THEN 1 ELSE 0 END) as lideres_verificados,
    SUM(l.meta_votos) as meta_total_votos
FROM lideres_campana l
GROUP BY l.comuna
ORDER BY meta_total_votos DESC;
