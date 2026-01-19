import pandas as pd
import psycopg2
import os
import time
from io import StringIO
import datetime

# Configuration
INPUT_FILE = '/app/data/data/EMPRESAS.csv'
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

def load_empresas():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("🚀 Preparing database for EMPRESAS load...")
    
    # Check if table exists (should exist from DDL)
    
    print(f"📂 Reading {INPUT_FILE}...")
    try:
        # Load CSV
        # Format: "company_id";"legal_name";...
        df = pd.read_csv(INPUT_FILE, sep=';', quotechar='"', dtype=str)
        
        print(f"   Rows found: {len(df)}")
        
        # Mapping Columns
        # Source -> Destination
        # company_id -> empresa_id (PK)
        # identification_number -> nit
        # legal_name -> razon_social
        # legal_representative -> representante_legal
        # company_type -> tipo_empresa
        # status -> estado_actual
        # created_time -> fecha_constitucion
        # phone_number -> telefono_contacto
        # phone_extension -> extension
        # address -> direccion_fisica
        # municipality_code -> municipio_cod
        
        # Clean Data
        
        # 1. Parse Dates: created_time '2025-08-05 17:33:52.492' -> '2025-08-05'
        # Some might be empty
        df['fecha_constitucion'] = pd.to_datetime(df['created_time'], errors='coerce').dt.date
        
        # 2. Municipality Code
        # In EMPRESAS.csv: '43' (sometimes short?), '700'
        # In dim_divipole: usually 5 digits '05001'.
        # The CSV has separate 'department_code' and 'municipality_code'.
        # We might need to construct the full code if 'municipio_cod' in DB expects 5 digits.
        # Let's check the schema logic or assumption. 
        # The user didn't explicitly specify, but standard Colombia logic is Dept(2) + Muni(3).
        # Sample row: Dept=1, Muni=43. -> '01043'? 
        # Sample row: Dept=12, Muni=700 -> '12700'.
        # Let's construct it to be safe if both cols exist
        
        if 'department_code' in df.columns and 'municipality_code' in df.columns:
             # Pad Dept to 2 chars, Muni to 3 chars
             df['dept_pad'] = df['department_code'].str.zfill(2)
             df['muni_pad'] = df['municipality_code'].str.zfill(3)
             df['municipio_cod_full'] = df['dept_pad'] + df['muni_pad']
        else:
            df['municipio_cod_full'] = df['municipality_code'] # Fallback
            
        # Select and Rename for Staging
        output_data = []
        for index, row in df.iterrows():
            output_data.append((
                row['company_id'],
                row['identification_number'], # nit
                row['legal_name'],
                row['legal_representative'],
                row['company_type'],
                row['status'],
                row['fecha_constitucion'] if pd.notnull(row['fecha_constitucion']) else None,
                str(row['phone_number']).replace('.0', '')[:20] if pd.notnull(row['phone_number']) else None, # Clean floats
                row['phone_extension'],
                row['address'],
                row['municipio_cod_full']
            ))

        print("📥 Inserting into core_empresas (Row-by-Row for validation)...")
        
        insert_query = """
            INSERT INTO core_empresas (
                empresa_id, nit, razon_social, representante_legal, tipo_empresa, 
                estado_actual, fecha_constitucion, telefono_contacto, extension, 
                direccion_fisica, municipio_cod
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (empresa_id) DO UPDATE SET
                nit = EXCLUDED.nit,
                razon_social = EXCLUDED.razon_social,
                representante_legal = EXCLUDED.representante_legal,
                tipo_empresa = EXCLUDED.tipo_empresa,
                estado_actual = EXCLUDED.estado_actual,
                fecha_constitucion = EXCLUDED.fecha_constitucion,
                telefono_contacto = EXCLUDED.telefono_contacto,
                extension = EXCLUDED.extension,
                direccion_fisica = EXCLUDED.direccion_fisica,
                municipio_cod = EXCLUDED.municipio_cod;
        """
        
        success_count = 0
        skipped_count = 0
        
        for row in output_data:
            try:
                cur.execute(insert_query, row)
                success_count += 1
            except psycopg2.IntegrityError as e:
                conn.rollback() # Important: rollback the failed transaction part
                print(f"⚠️ Skipping duplicate/invalid row ID={row[0]} NIT={row[1]}: {e}")
                skipped_count += 1
                continue
            except Exception as e:
                conn.rollback()
                print(f"❌ Error on row ID={row[0]}: {e}")
                continue
                
        conn.commit()
        
        print(f"🏁 DONE! Inserted/Updated {success_count} companies. Skipped {skipped_count} due to errors.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    # Need extras for execute_batch
    import psycopg2.extras 
    if os.path.exists(INPUT_FILE):
        load_empresas()
    else:
        print(f"❌ File not found: {INPUT_FILE}")
