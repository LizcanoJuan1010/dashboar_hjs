import pandas as pd
import psycopg2
import os
import time
import unicodedata
import re

# Configuration
INPUT_FILE = '/app/data/data/BD_completa_HJS.xlsx'
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
            print(f"DB not ready, retrying... {e}")
            time.sleep(5)
            retries -= 1
    raise Exception("DB Connection failed")

def normalize_text(text):
    if pd.isna(text):
        return None
    text = str(text).strip().upper()
    # Remove accents
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text

def load_hjs():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("🚀 Preparing HJS Contact load...")
    
    # 1. Fetch Municipality Mapping from Divipole
    # We want a map: NORMALIZED_NAME -> (COD_DEPTO, COD_MUNI)
    # Warning: Duplicates exist (e.g. San Francisco in many Depts).
    # Heuristic: We'll store all matches. If ambiguous, we might rely on a default context (e.g. Santander) 
    # or just take the first one if the user didn't specify. Given the data sample (Bucaramanga), it's likely Santander focused.
    # Let's prioritise Santander (68) if duplicates exist? Or just load what we find.
    
    print("🌍 Building Municipality Lookup...")
    cur.execute("SELECT DISTINCT cod_departamento, cod_municipio, nom_municipio FROM dim_divipole")
    
    muni_lookup = {}
    
    for row in cur.fetchall():
        c_dept, c_muni, name = row
        if not name: 
            continue
        norm_name = normalize_text(name)
        
        # Simple Logic: If collision, keep existing? Or List?
        # Let's just overwrite. Most capital cities are unique or dominant.
        # Ideally we'd warn on collisions.
        if norm_name not in muni_lookup:
            muni_lookup[norm_name] = (c_dept, c_muni)
        else:
            # Collision handling (Optional optimization)
            pass 
            
    print(f"   Loaded {len(muni_lookup)} municipalities for lookup.")

    print(f"📂 Reading {INPUT_FILE}...")
    try:
        # Columns in Excel: cc, nombrecompleto, contacto, direccion, barrio, municipio, grupo
        df = pd.read_excel(INPUT_FILE, dtype=str)
        print(f"   Rows found: {len(df)}")
        
        # Prepare Data
        insert_query = """
            INSERT INTO contactos_hjs (
                documento, nombre_completo, contacto, direccion, 
                barrio, municipio_texto, cod_departamento, cod_municipio
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (documento) DO UPDATE SET
                nombre_completo = EXCLUDED.nombre_completo,
                contacto = EXCLUDED.contacto,
                direccion = EXCLUDED.direccion,
                barrio = EXCLUDED.barrio,
                municipio_texto = EXCLUDED.municipio_texto,
                cod_departamento = EXCLUDED.cod_departamento,
                cod_municipio = EXCLUDED.cod_municipio;
        """
        
        data_to_insert = []
        batch_size = 5000
        
        processed = 0
        resolved_geo = 0
        
        for index, row in df.iterrows():
            cc = str(row['cc']).strip()
            if not cc or cc.lower() == 'nan':
                continue
                
            nombre = row.get('nombrecompleto', None)
            contacto = row.get('contacto', None)
            direccion = row.get('direccion', None)
            barrio = row.get('barrio', None)
            muni_text = row.get('municipio', None)
            
            # Resolve Geo
            c_dept = None
            c_muni = None
            norm_muni = normalize_text(muni_text)
            
            if norm_muni and norm_muni in muni_lookup:
                c_dept, c_muni = muni_lookup[norm_muni]
                resolved_geo += 1
            
            data_to_insert.append((
                cc,
                nombre,
                str(contacto)[:50] if pd.notnull(contacto) else None,
                direccion,
                barrio,
                muni_text,
                c_dept,
                c_muni
            ))
            
            if len(data_to_insert) >= batch_size:
                psycopg2.extras.execute_batch(cur, insert_query, data_to_insert)
                conn.commit()
                processed += len(data_to_insert)
                data_to_insert = []
                print(f"   Saved {processed} rows...")

        if data_to_insert:
            psycopg2.extras.execute_batch(cur, insert_query, data_to_insert)
            conn.commit()
            processed += len(data_to_insert)
            
        print(f"🏁 DONE! Loaded {processed} contacts. Resolved Municipality for {resolved_geo} records.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    import psycopg2.extras
    if os.path.exists(INPUT_FILE):
        load_hjs()
    else:
        print(f"❌ File not found: {INPUT_FILE}")
