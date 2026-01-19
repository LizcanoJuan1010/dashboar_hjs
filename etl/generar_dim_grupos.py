import pandas as pd
import re
import unicodedata
import os
import psycopg2
from psycopg2 import sql
import time

# --- CONFIGURACIÓN ---
INPUT_FOLDER = '/app/data/data'  # Inside Docker, mapped to e:/Data_Horacio/Dashboard/data
OUTPUT_FOLDER = '/app/data/data' # Save CSV output here too

# Database Connection Parameters
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

def get_db_connection():
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            return conn
        except psycopg2.OperationalError as e:
            print(f"DB not ready yet, retrying... ({e})")
            time.sleep(5)
            retries -= 1
    raise Exception("Could not connect to database")

# --- FUNCIÓN DE LIMPIEZA ---
def limpiar_nombre_grupo(texto):
    if pd.isna(texto): return None
    t = str(texto).upper().strip()
    # 1. Quitar tildes (Á -> A)
    t = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    # 2. Dejar solo letras, números y guiones (eliminar puntos, comas extra, etc.)
    t = re.sub(r'[^A-Z0-9\s\-]', ' ', t) 
    # 3. Colapsar espacios múltiples
    t = re.sub(r'\s+', ' ', t).strip()
    # Filtro: Si queda algo muy corto (ej: "-"), lo ignoramos
    return t if len(t) > 1 else None

def limpiar_doc(doc):
    if pd.isna(doc): return None
    # Dejar solo números
    return re.sub(r'[^0-9]', '', str(doc).split('.')[0])

# --- FUENTES (Archivos + Columnas Clave) ---
fuentes = [
    {
        'archivo': 'SERPA 100.000.xlsx', 
        'col_doc': 'DOCUMENTO', 
        'col_grupo': 'GRUPO' 
    },
    {
        'archivo': 'BD_completa_HJS.xlsx', 
        'col_doc': 'CC', 
        'col_grupo': 'GRUPO' 
    }
]

def procesar_grupos():
    conn = get_db_connection()
    cur = conn.cursor()
    
    df_final = pd.DataFrame()
    grupos_unicos_global = set()

    print("🔄 Iniciando procesamiento de grupos...")

    for f in fuentes:
        path = os.path.join(INPUT_FOLDER, f['archivo'])
        if not os.path.exists(path):
            print(f"⚠️ Archivo no encontrado: {path}")
            continue
            
        try:
            print(f"📄 Leyendo {f['archivo']}...")
            # Leer todo como texto para evitar errores de tipo
            df = pd.read_excel(path, dtype=str)
            # Normalizar encabezados a mayúsculas y sin espacios
            df.columns = [c.strip().upper() for c in df.columns]
            
            col_doc = f['col_doc']
            col_grupo = f['col_grupo']
            
            if col_doc in df.columns and col_grupo in df.columns:
                # 1. Seleccionar solo columnas útiles y eliminar filas vacías
                temp = df[[col_doc, col_grupo]].dropna()
                
                # 2. Limpiar Documento (Cédula)
                temp['documento'] = temp[col_doc].apply(limpiar_doc)
                temp = temp[temp['documento'] != '']
                
                # 3. Preparar Grupos para Explosión
                # Normalizar separadores: ; | / -> ,
                temp['raw_groups'] = temp[col_grupo].str.replace(';', ',').str.replace('/', ',').str.replace('|', ',')
                
                # 4. Convertir string a lista
                temp['lista'] = temp['raw_groups'].str.split(',')
                
                # 5. Explode: 1 fila por grupo-persona
                exploded = temp.explode('lista')
                
                # 6. Limpiar nombre del grupo
                exploded['nombre_grupo'] = exploded['lista'].apply(limpiar_nombre_grupo)
                
                # 7. Filtrar inválidos
                validos = exploded[['documento', 'nombre_grupo']].dropna()
                validos = validos[validos['nombre_grupo'] != '']
                
                # 8. Acumular para CSV de relaciones
                df_final = pd.concat([df_final, validos])
                
                # 9. Acumular para DB (Solo nombres únicos)
                grupos_unicos_local = set(validos['nombre_grupo'].unique())
                grupos_unicos_global.update(grupos_unicos_local)
                
                print(f"   ✅ {f['archivo']}: Procesadas {len(validos)} relaciones válidas.")
            else:
                print(f"   ⚠️ Columnas no encontradas en {f['archivo']} (Esperaba: {col_doc}, {col_grupo})")
                
        except Exception as e:
            print(f"   ❌ Error en {f['archivo']}: {e}")

    # --- CARGA A BASE DE DATOS (dim_grupos) ---
    if grupos_unicos_global:
        print(f"\n📥 Insertando {len(grupos_unicos_global)} grupos únicos en la base de datos...")
        nuevos_insertados = 0
        errores_db = 0
        
        for grupo in grupos_unicos_global:
            try:
                # Insertar si no existe
                insert_query = sql.SQL("""
                    INSERT INTO dim_grupos (nombre, descripcion)
                    VALUES (%s, 'Carga Masiva Excel')
                    ON CONFLICT (nombre) DO NOTHING;
                """)
                cur.execute(insert_query, (grupo,))
                # cur.rowcount = 1 si insertó, 0 si existía
                if cur.rowcount > 0:
                    nuevos_insertados += 1
            except Exception as e:
                errores_db += 1
                conn.rollback()
                print(f"Error insertando grupo '{grupo}': {e}")
                continue # Seguir con el siguiente
            
            conn.commit() # Commit parcial o por lotes sería mejor, pero esto es seguro fila a fila
            
        print(f"   🏁 DB Actualizada: {nuevos_insertados} nuevos grupos insertados.")
    else:
        print("\n⚠️ No se encontraron grupos para insertar en DB.")

    # --- GENERAR CSV RELACIONES ---
    if not df_final.empty:
        # Deduplicar globalmente: (Doc, Grupo) único
        # Esto soluciona el "Bingo, Bingo" -> "Bingo"
        df_final = df_final.drop_duplicates()
        
        archivo_salida = os.path.join(OUTPUT_FOLDER, 'relaciones_persona_grupo.csv')
        df_final.to_csv(archivo_salida, index=False)
        print(f"\n💾 Archivo de relaciones generado: {archivo_salida}")
        print(f"   -> Total Relaciones Únicas: {len(df_final)}")
    else:
        print("\n⚠️ No se generaron relaciones para el CSV.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    procesar_grupos()