import pandas as pd
import psycopg2
import os
import time

# Configuration
INPUT_FILE = '/app/data/data/REP_LEGAL_EMPRESA.csv'
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

def load_representantes():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("🚀 Preparing Legal Representatives load...")
    print(f"📂 Reading {INPUT_FILE}...")
    
    try:
        # Check if file exists
        if not os.path.exists(INPUT_FILE):
             print(f"❌ File not found: {INPUT_FILE}")
             return

        df = pd.read_csv(INPUT_FILE, sep=';', quotechar='"', dtype=str)
        print(f"   Rows found: {len(df)}")
        
        # Columns in CSV: 
        # "company_contact_id";"name";"company_role";"phone_number";"phone_extension";
        # "mobile_number";"email";"created_time";"discarted_time";"company_id";"document"
        
        insert_query = """
            INSERT INTO representantes_legales_contacto (
                id_contacto_empresa, nombre_contacto, rol_empresa, telefono_fijo,
                extension, celular, email, empresa_id, documento, 
                fecha_creacion, fecha_retiro
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_contacto_empresa) DO NOTHING;
        """
        
        data_to_insert = []
        batch_size = 5000
        count = 0
        
        # Prefetch valid empresa_ids to avoid FK errors
        print("🔍 caching valid empresa_ids...")
        cur.execute("SELECT empresa_id FROM core_empresas")
        valid_companies = set(row[0] for row in cur.fetchall())
        print(f"   Key Cache: {len(valid_companies)} companies found.")
        
        skipped_fk = 0
        
        for index, row in df.iterrows():
            emp_id = row['company_id']
            
            # FK Validation
            if emp_id not in valid_companies:
                skipped_fk += 1
                continue
                
            data_to_insert.append((
                row['company_contact_id'],
                row['name'],
                row['company_role'],
                str(row['phone_number'])[:50] if pd.notnull(row['phone_number']) else None,
                str(row['phone_extension'])[:20] if pd.notnull(row['phone_extension']) else None,
                str(row['mobile_number'])[:50] if pd.notnull(row['mobile_number']) else None,
                row['email'],
                emp_id,
                row.get('document', None), # CSV might handle document differently or missing
                row['created_time'],
                row['discarted_time'] if pd.notnull(row['discarted_time']) else None
            ))
            
            if len(data_to_insert) >= batch_size:
                psycopg2.extras.execute_batch(cur, insert_query, data_to_insert)
                conn.commit()
                count += len(data_to_insert)
                data_to_insert = []
                print(f"   Saved {count} representatives...")

        if data_to_insert:
            psycopg2.extras.execute_batch(cur, insert_query, data_to_insert)
            conn.commit()
            count += len(data_to_insert)
            
        print(f"🏁 DONE! Loaded {count} representatives. Skipped {skipped_fk} due to missing company FK.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    import psycopg2.extras
    load_representantes()
