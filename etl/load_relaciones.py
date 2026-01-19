import pandas as pd
import psycopg2
import os
import time
import psycopg2.extras
import sys
import traceback

# Configuration
INPUT_FILE = '/app/data/data/relaciones_persona_grupo.csv'
LOG_FILE = '/app/data/error_rel.log'
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

def log_to_file(msg):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(str(msg) + "\n")
    except:
        pass

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
            msg = f"DB not ready, retrying... {e}"
            print(msg)
            log_to_file(msg)
            time.sleep(5)
            retries -= 1
    raise Exception("DB Connection failed")

def load_relaciones():
    print("🚀 Preparing Relations load...")
    log_to_file("Starting load_relaciones...")
    
    if not os.path.exists(INPUT_FILE):
        msg = f"❌ File not found: {INPUT_FILE}"
        print(msg)
        log_to_file(msg)
        return

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1. Load Groups Map (Name -> ID)
        print("🔍 Caching Group IDs...")
        cur.execute("SELECT nombre, grupo_id FROM dim_grupos")
        group_map = {row[0]: row[1] for row in cur.fetchall()}
        print(f"   Mapped {len(group_map)} groups.")
        log_to_file(f"Mapped {len(group_map)} groups.")
        
        print(f"📂 Reading {INPUT_FILE}...")
        df = pd.read_csv(INPUT_FILE, dtype=str)
        print(f"   Rows: {len(df)}")
        log_to_file(f"CSV Rows: {len(df)}")
        
        insert_query = """
            INSERT INTO rel_contacto_grupo (documento, grupo_id)
            VALUES (%s, %s)
        """
        
        # 2. Cache Valid Documents
        print("🔍 Caching Valid Documents...")
        cur.execute("SELECT documento FROM contactos_hjs")
        valid_docs = set(row[0] for row in cur.fetchall())
        print(f"   Mapped {len(valid_docs)} valid documents.")
        log_to_file(f"Mapped {len(valid_docs)} valid documents.")

        print(f"📂 Reading {INPUT_FILE}...")
        df = pd.read_csv(INPUT_FILE, dtype=str)
        print(f"   Rows: {len(df)}")
        log_to_file(f"CSV Rows: {len(df)}")
        
        insert_query = """
            INSERT INTO rel_contacto_grupo (documento, grupo_id)
            VALUES (%s, %s)
        """
        
        data_to_insert = []
        batch_size = 5000
        count = 0
        skipped_group = 0
        skipped_doc = 0
        
        for idx, row in df.iterrows():
            doc = row['documento']
            grp_name = row['nombre_grupo']
            
            if doc not in valid_docs:
                skipped_doc += 1
                continue

            if grp_name in group_map:
                grp_id = group_map[grp_name]
                data_to_insert.append((doc, grp_id))
            else:
                skipped_group += 1
                
            if len(data_to_insert) >= batch_size:
                psycopg2.extras.execute_batch(cur, insert_query, data_to_insert)
                conn.commit()
                count += len(data_to_insert)
                data_to_insert = []
                print(f"   Linked {count} relations...")
                
        if data_to_insert:
            psycopg2.extras.execute_batch(cur, insert_query, data_to_insert)
            conn.commit()
            count += len(data_to_insert)
            
        final_msg = f"🏁 DONE! Linked {count} relations. Skipped {skipped_group} unknown groups."
        print(final_msg)
        log_to_file(final_msg)
        
    except Exception as e:
        err_msg = f"❌ Error: {e}\n{traceback.format_exc()}"
        print(err_msg)
        log_to_file(err_msg)
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    try:
        load_relaciones()
    except Exception as e:
        err_msg = f"❌ Fatal Error: {e}\n{traceback.format_exc()}"
        print(err_msg)
        log_to_file(err_msg)
        sys.exit(1)
