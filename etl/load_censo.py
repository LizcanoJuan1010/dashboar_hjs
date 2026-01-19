import pandas as pd
import psycopg2
import os
import time
from io import StringIO
import datetime

# Configuration
INPUT_FILE = '/app/data/data/CENSO.csv'
CHUNK_SIZE = 100000

# DB Config
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

def load_censo():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("🚀 Preparing database for bulk load...")
    
    # 1. Create Staging Table (Unlogged for speed)
    cur.execute("DROP TABLE IF EXISTS staging_censo_import;")
    cur.execute("""
        CREATE UNLOGGED TABLE staging_censo_import (
            documento VARCHAR(20),
            cod_departamento VARCHAR(5),
            cod_municipio VARCHAR(5),
            cod_zona VARCHAR(5),
            cod_puesto VARCHAR(20),
            fecha_registro_censo DATE,
            tipo_documento VARCHAR(10)
        );
    """)
    conn.commit()
    
    print(f"📂 Reading {INPUT_FILE}...")
    
    # 2. Process CSV in Chunks
    # User said cols: "identification_number";"department_code";... with sep=';'
    try:
        chunk_iter = pd.read_csv(
            INPUT_FILE, 
            sep=';', 
            chunksize=CHUNK_SIZE,
            dtype=str, # Read all as string to avoid type errors
            quotechar='"'
        )
        
        total_rows = 0
        start_time = time.time()
        
        for i, chunk in enumerate(chunk_iter):
            # Map columns
            # CSV: identification_number, department_code, municipality_code, zone_code, place_code, register_date, identification_type
            # DB: documento, cod_departamento, cod_municipio, cod_zona, cod_puesto, fecha_registro_censo, tipo_documento
            
            df_stage = pd.DataFrame()
            df_stage['documento'] = chunk['identification_number']
            df_stage['cod_departamento'] = chunk['department_code']
            df_stage['cod_municipio'] = chunk['municipality_code']
            df_stage['cod_zona'] = chunk['zone_code']
            df_stage['cod_puesto'] = chunk['place_code']
            df_stage['fecha_registro_censo'] = chunk['register_date'] # Postgres usually handles 'YYYY-MM-DD' text automatically
            df_stage['tipo_documento'] = chunk['identification_type']
            
            # Clean data if needed (e.g. max lengths)
            df_stage['tipo_documento'] = df_stage['tipo_documento'].str.slice(0, 10)
            
            # Write to memory buffer
            buffer = StringIO()
            df_stage.to_csv(buffer, index=False, header=False, sep='\t')
            buffer.seek(0)
            
            # COPY to Staging
            try:
                cur.copy_from(buffer, 'staging_censo_import', sep='\t', null='')
                total_rows += len(df_stage)
            except Exception as e:
                print(f"❌ Error copying chunk {i}: {e}")
                conn.rollback()
                continue
                
            if (i + 1) % 10 == 0:
                conn.commit()
                elapsed = time.time() - start_time
                print(f"   ⏱ Chunk {i+1} processed. Total rows staged: {total_rows} ({total_rows/elapsed:.0f} rows/sec)")
        
        conn.commit()
        print(f"✅ Staging complete. Total rows in buffer: {total_rows}")
        
        # 3. Final Insert (Staging -> Production)
        print("📥 Moving data from Staging to Production (censo_electoral)...")
        print("   (This might take a while due to index updates and deduplication)")
        
        # Using INSERT ON CONFLICT DO NOTHING based on unique constraint
        # Assumption: 'documento' is unique in censo_electoral
        cur.execute("""
            INSERT INTO censo_electoral (
                documento, tipo_documento, cod_departamento, cod_municipio, 
                cod_zona, cod_puesto, fecha_registro_censo
            )
            SELECT DISTINCT 
                documento, tipo_documento, cod_departamento, cod_municipio,
                cod_zona, cod_puesto, 
                CAST(fecha_registro_censo AS DATE)
            FROM staging_censo_import
            ON CONFLICT (documento) DO NOTHING;
        """)
        
        inserted_count = cur.rowcount
        conn.commit()
        
        # Cleanup
        cur.execute("DROP TABLE staging_censo_import;")
        conn.commit()
        
        print(f"🏁 DONE! Successfully inserted/processed {inserted_count} census records.")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        conn.rollback()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    if os.path.exists(INPUT_FILE):
        load_censo()
    else:
        print(f"❌ File not found: {INPUT_FILE}")
