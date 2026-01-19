-- ======================================================================================
-- MODELO HJS FINAL (VERSIÓN GOLD - CORREGIDA)
-- Arquitectura: Tabla Maestra Geográfica Única (dim_divipola)
-- Corrección: Eliminadas referencias a tablas inexistentes (municipio/depto)
-- ======================================================================================

-- --------------------------------------------------------------------------------------
-- 1. MAESTRO GEOGRÁFICO (DIVIPOLA)
-- --------------------------------------------------------------------------------------

CREATE TABLE "dim_divipole" (
    "divipole_id" SERIAL PRIMARY KEY,
    
    -- Jerarquía Completa
    "cod_departamento" VARCHAR(5) NOT NULL,
    "cod_municipio" VARCHAR(5) NOT NULL,
    "cod_zona" VARCHAR(5) NOT NULL,
    "cod_puesto" VARCHAR(20) NOT NULL,
    
    -- Nombres Descriptivos
    "nom_departamento" VARCHAR(100),
    "nom_municipio" VARCHAR(100),
    "nombre_puesto" VARCHAR(255),
    "direccion_puesto" VARCHAR(255),
    "tipo_zona" VARCHAR(50), -- Rural/Urbana
    "mesa" INTEGER,      
    
    -- Coordenadas Geográficas
    "latitud" DECIMAL(10, 8),
    "longitud" DECIMAL(11, 8),

    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Restricción para garantizar unicidad lógica
    CONSTRAINT "uq_divipole_geo" UNIQUE ("cod_departamento", "cod_municipio", "cod_zona", "cod_puesto")
);

-- Índices Compuestos para optimizar los JOINs (Vital para este modelo)
CREATE INDEX idx_divipole_full ON "dim_divipole" ("cod_departamento", "cod_municipio", "cod_zona", "cod_puesto");
CREATE INDEX idx_divipole_muni ON "dim_divipole" ("cod_municipio");


-- --------------------------------------------------------------------------------------
-- 2. CATÁLOGOS AUXILIARES
-- --------------------------------------------------------------------------------------

CREATE TABLE "dim_grupos" (
    "grupo_id" SERIAL PRIMARY KEY,
    "nombre" VARCHAR(100) NOT NULL UNIQUE,
    "descripcion" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "core_empresas" (
    "empresa_id" VARCHAR(20) PRIMARY KEY, -- ID corto o NIT
    "nit" VARCHAR(20) NOT NULL,
    "razon_social" VARCHAR(255) NOT NULL,
    "representante_legal" VARCHAR(255),
    "tipo_empresa" VARCHAR(100),
    "estado_actual" VARCHAR(50),
    "fecha_constitucion" DATE,
    "telefono_contacto" VARCHAR(50),
    "extension" VARCHAR(10),
    "direccion_fisica" TEXT,
    
    -- Ubicación (Solo código, cruza con dim_divipola si es necesario)
    "municipio_cod" VARCHAR(10), 
    
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
    -- CORRECCIÓN: Eliminada FK a "municipio" (No existe tabla separada)
);

-- --------------------------------------------------------------------------------------
-- 3. TABLAS CENTRALES (HECHOS)
-- --------------------------------------------------------------------------------------

CREATE TABLE "censo_electoral" (
    "censo_id" SERIAL PRIMARY KEY,
    "documento" VARCHAR(20) NOT NULL UNIQUE,
    "tipo_documento" VARCHAR(10),
    
    -- Códigos de cruce con dim_divipola
    "cod_departamento" VARCHAR(5),
    "cod_municipio" VARCHAR(5),
    "cod_zona" VARCHAR(5),
    "cod_puesto" VARCHAR(20),
    
    "fecha_registro_censo" DATE,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
    -- CORRECCIÓN: Eliminadas FK a "departamento"/"municipio". 
    -- Se usa el índice idx_censo_geo para cruzar con dim_divipola.
);
-- Índice alineado a la Divipola
CREATE INDEX idx_censo_geo ON "censo_electoral" ("cod_departamento", "cod_municipio", "cod_zona", "cod_puesto");


CREATE TABLE "contactos_hjs" (
    "documento" VARCHAR(20) PRIMARY KEY,
    "nombre_completo" VARCHAR(255),
    "contacto" VARCHAR(100),
    "direccion" VARCHAR(255),
    "barrio" VARCHAR(100),
    "municipio_texto" VARCHAR(100),
    "cod_departamento" VARCHAR(5),
    "cod_municipio" VARCHAR(5),
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Index for performance
CREATE INDEX idx_contactos_hjs_geo ON "contactos_hjs" ("cod_departamento", "cod_municipio");


-- --------------------------------------------------------------------------------------
-- 4. BASES DE GESTIÓN (Empleados, Líderes, Candidatos)
-- --------------------------------------------------------------------------------------

CREATE TABLE "empleados_empresas" (
    "empleado_id" VARCHAR(50) PRIMARY KEY,
    "documento" VARCHAR(20) NOT NULL, -- Constraint removed to match data reality if needed, keeping NOT NULL
    "tipo_documento" VARCHAR(10) DEFAULT 'CC',
    
    -- Conexión Directa a Empresa
    "empresa_id" VARCHAR(20), 
    
    "primer_nombre" VARCHAR(100),
    "segundo_nombre" VARCHAR(100),
    "primer_apellido" VARCHAR(100),
    "segundo_apellido" VARCHAR(100),
    "nombre_completo" VARCHAR(255),
    "sexo" CHAR(1),
    "fecha_nacimiento" DATE,
    "nivel_educativo" VARCHAR(100),
    "email" VARCHAR(150),
    "celular" VARCHAR(50),
    "direccion" TEXT,
    
    -- Ubicación Electoral
    "cod_departamento" VARCHAR(5),
    "cod_municipio" VARCHAR(5),
    "zona_codigo" VARCHAR(10),
    "puesto_codigo" VARCHAR(10),
    
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY ("empresa_id") REFERENCES "core_empresas"("empresa_id") ON UPDATE CASCADE
    -- CORRECCIÓN: Eliminada FK a "municipio"
);

CREATE TABLE "lideres_campana" (
    "lider_id" SERIAL PRIMARY KEY,
    "documento" VARCHAR(20),
    "nombre_completo" VARCHAR(255),
    "cargo_liderazgo" VARCHAR(100),
    "comuna" VARCHAR(50),
    "celular" VARCHAR(50),
    "direccion" TEXT,
    "cod_municipio" VARCHAR(5),
    "meta_votos" INTEGER DEFAULT 0,
    "verificado" VARCHAR(50),      -- Changed to VARCHAR to store 'SI'/'NO' or text
    "hojas_vida_entregadas" INTEGER,
    "boletas_bingo" INTEGER,
    "damas_gratis" INTEGER,
    "pendones" INTEGER,
    "reunion_info" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    -- CORRECCIÓN: Eliminada FK a "municipio"
);

CREATE TABLE "candidatos_gestion" (
    "candidato_id" SERIAL PRIMARY KEY,
    "documento" VARCHAR(20),
    "nombre_candidato" VARCHAR(255),
    "partido" VARCHAR(100),
    "celular" VARCHAR(50),
    "voto_estimado" INTEGER,
    "publicidad_compartida" VARCHAR(50), -- SI/NO/REQUERE MAS
    "hojas_vida_entregadas" INTEGER,
    "verificado" VARCHAR(50),
    "damas_gratis" INTEGER,
    "boletas_bingo" INTEGER,
    "pendones_entregados" INTEGER,
    "reunion_info" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------------------------
-- 5. TABLAS DE RELACIÓN Y ESPECÍFICAS
-- --------------------------------------------------------------------------------------

CREATE TABLE "representantes_legales_contacto" (
    "id_contacto_empresa" VARCHAR(50) PRIMARY KEY, -- company_contact_id
    "nombre_contacto" VARCHAR(255),                -- name
    "rol_empresa" VARCHAR(100),                    -- company_role
    "telefono_fijo" VARCHAR(50),                   -- phone_number
    "extension" VARCHAR(20),                       -- phone_extension
    "celular" VARCHAR(50),                         -- mobile_number
    "email" VARCHAR(150),                          -- email
    "empresa_id" VARCHAR(20),                      -- company_id
    "documento" VARCHAR(20),                       -- document
    "fecha_creacion" TIMESTAMP,                    -- created_time
    "fecha_retiro" TIMESTAMP,                      -- discarted_time
    
    -- CORRECCIÓN: Apuntaba a ("id"), corregido a ("empresa_id")
    FOREIGN KEY ("empresa_id") REFERENCES "core_empresas"("empresa_id") ON UPDATE CASCADE
);

CREATE TABLE "rel_contacto_grupo" (
    "rel_id" SERIAL PRIMARY KEY,
    "contacto_id" INTEGER,
    "grupo_id" INTEGER,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY ("contacto_id") REFERENCES "contactos_hjs"("documento") ON DELETE CASCADE,
    FOREIGN KEY ("grupo_id") REFERENCES "dim_grupos"("grupo_id") ON DELETE CASCADE
);