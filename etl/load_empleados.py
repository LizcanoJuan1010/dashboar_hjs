import pandas as pd
import psycopg2
import os
import time
from io import StringIO

# Configuration
INPUT_FILE = '/app/data/data/EMPLEADOS_EMPRESAS.csv'
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

def load_empleados():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("🚀 Preparing database for EMPLEADOS load...")
    
    # 0. Get Valid Companies for FK validation
    print("🔎 Fetching valid Company IDs...")
    cur.execute("SELECT empresa_id FROM core_empresas")
    valid_companies = set(row[0] for row in cur.fetchall())
    print(f"   Found {len(valid_companies)} valid companies.")

    print(f"📂 Reading {INPUT_FILE}...")
    
    try:
        # Load CSV
        df = pd.read_csv(INPUT_FILE, sep=';', quotechar='"', dtype=str)
        total_rows = len(df)
        print(f"   Rows found: {total_rows}")
        
        # 1. Generate 'nombre_completo'
        df['first_name_one'] = df['first_name_one'].fillna('')
        df['first_name_two'] = df['first_name_two'].fillna('')
        df['last_name_one'] = df['last_name_one'].fillna('')
        df['last_name_two'] = df['last_name_two'].fillna('')
        
        df['nombre_completo'] = (
            df['first_name_one'] + ' ' + 
            df['first_name_two'] + ' ' + 
            df['last_name_one'] + ' ' + 
            df['last_name_two']
        ).str.replace(r'\s+', ' ', regex=True).str.strip()
        
        # 2. Date Cleaning
        df['birthday'] = pd.to_datetime(df['birthday'], errors='coerce').dt.date
        
        # 3. Filter Invalid Companies (FK Constraint Logic)
        # Only keep rows where company_id is present in DB or is Null (if we allow nulls)
        # If company_id is provided but not in DB, it would crash insert.
        # Let's set invalid company_ids to None so we can still load the person? 
        # Or drop them? User asked to "carga toda la informacion". 
        # Making it None is safer than dropping.
        
        def validate_company(cid):
            if pd.isna(cid) or cid == '':
                return None
            if cid in valid_companies:
                return cid
            return None # Invalid/Unknown company -> Set to None to avoid FK error
            
        df['clean_company_id'] = df['company_id'].apply(validate_company)
        
        # 4. Prepare Batch
        insert_query = """
            INSERT INTO empleados_empresas (
                empleado_id, documento, tipo_documento, empresa_id,
                primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, nombre_completo,
                sexo, fecha_nacimiento, nivel_educativo, email, celular, direccion,
                cod_departamento, cod_municipio, zona_codigo, puesto_codigo
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (empleado_id) DO UPDATE SET
                documento = EXCLUDED.documento,
                nombre_completo = EXCLUDED.nombre_completo,
                empresa_id = EXCLUDED.empresa_id,
                updated_at = CURRENT_TIMESTAMP;
        """
        
        batch_size = 10000
        processed = 0
        
        print(f"📥 Starting Batch Insertion ({batch_size} rows per batch)...")
        
        # To reduce memory usage, we can iterate key columns or convert to list in chunks
        # But valid_companies set helps.
        
        data_to_insert = []
        
        for index, row in df.iterrows():
            if pd.isna(row['nominated_citizen_id']):
                continue
                
            cel = row['mobile_number'] if pd.notnull(row['mobile_number']) and str(row['mobile_number']).strip() != '' else row['phone_number']
            
            data_to_insert.append((
                row['nominated_citizen_id'], 
                row['identification_number'], 
                row['identification_type'] if pd.notnull(row['identification_type']) else 'CC',
                row['clean_company_id'], # Use validated ID
                row['first_name_one'],
                row['first_name_two'],
                row['last_name_one'],
                row['last_name_two'],
                row['nombre_completo'],
                row['sex'][:1] if pd.notnull(row['sex']) else None,
                row['birthday'] if pd.notnull(row['birthday']) else None,
                row['education_level'],
                row['email'],
                str(cel)[:50] if cel else None,
                row['address'],
                row['department_code'],
                row['municipality_code'], 
                row['zone_code'], 
                row['place_code']
            ))
            
            if len(data_to_insert) >= batch_size:
                psycopg2.extras.execute_batch(cur, insert_query, data_to_insert)
                conn.commit()
                processed += len(data_to_insert)
                data_to_insert = []
                print(f"   Saved {processed}/{total_rows}...")
        
        # Final batch
        if data_to_insert:
            psycopg2.extras.execute_batch(cur, insert_query, data_to_insert)
            conn.commit()
            processed += len(data_to_insert)
            
        print(f"🏁 DONE! Successfully processed {processed} records.")

    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        conn.rollback()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    import psycopg2.extras
    if os.path.exists(INPUT_FILE):
        start_time = time.time()
        load_empleados()
        print(f"⏱️ Duration: {time.time() - start_time:.2f} seconds")
    else:
        print(f"❌ File not found: {INPUT_FILE}")
