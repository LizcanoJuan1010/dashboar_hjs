import pdfplumber
import os
import psycopg2
from psycopg2 import sql
import time

# Configuration
pdf_path = "/app/data/DIVIPOLE 2026 GEORREFERENCIACIÓN 15122025.pdf"

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

def extract_and_load(pdf_path):
    conn = get_db_connection()
    cur = conn.cursor()
    
    print(f"Starting extraction from {pdf_path}...")
    
    rows_inserted = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        
        for i, page in enumerate(pdf.pages):
            table = page.extract_table()
            
            if table:
                for row in table:
                    # Clean up row data
                    clean_row = [str(cell).replace('\n', ' ').strip() if cell is not None else '' for cell in row]
                    
                    # Row Check: First column must be digits (DD code)
                    # Expected columns in PDF:
                    # 0: DD, 1: MM, 2: ZZ, 3: PP
                    # 4: DEPARTAMENTO, 5: MUNICIPIO, 6: PUESTO, 7: DIRECCIÓN, 8: COMUNA
                    # 9: MUJERES, 10: HOMBRES, 11: TOTAL, 12: MESAS
                    # 13: LATITUD, 14: LONGITUD
                    
                    if len(clean_row) >= 15 and clean_row[0].isdigit():
                        try:
                            # Map to DB columns
                            cod_departamento = clean_row[0]
                            cod_municipio = clean_row[1]
                            cod_zona = clean_row[2]
                            cod_puesto = clean_row[3]
                            nom_departamento = clean_row[4]
                            nom_municipio = clean_row[5]
                            nombre_puesto = clean_row[6]
                            direccion_puesto = clean_row[7]
                            tipo_zona = clean_row[8]
                            # clean_row[9], [10], [11] are census counts - ignored
                            mesa = clean_row[12]
                            
                            # Handle coordinates (remove thousand separators if any, handle dots)
                            lat_str = clean_row[13].replace(',', '.')
                            lon_str = clean_row[14].replace(',', '.')
                            
                            # Handle coordinates (remove thousand separators if any, handle dots)
                            lat_str = clean_row[13].replace(',', '.')
                            lon_str = clean_row[14].replace(',', '.')
                            
                            def normalize_coordinate(val_str, is_lat):
                                if not val_str:
                                    return None
                                try:
                                    # Remove distinct invalid chars but keep negative sign and dot
                                    clean_val = val_str.replace(' ', '')
                                    # If multiple dots, keep first? Or assumption is it might be missing dot.
                                    
                                    val = float(clean_val)
                                    
                                    # Heuristic for Colombia: 
                                    # Lat: -5 to 13
                                    # Lon: -85 to -65
                                    
                                    if is_lat:
                                        # Fix integer-like large numbers (e.g. 10277349 -> 10.277349)
                                        while abs(val) > 90:
                                            val /= 10.0
                                        # If still weird (e.g. 0.0001), maybe multiply? No, usually it's missing dot.
                                    else:
                                        # Lon
                                        while abs(val) > 180:
                                            val /= 10.0
                                            
                                    return val
                                except ValueError:
                                    return None

                            latitud = normalize_coordinate(lat_str, True)
                            longitud = normalize_coordinate(lon_str, False)

                            insert_query = sql.SQL("""
                                INSERT INTO dim_divipole (
                                    cod_departamento, cod_municipio, cod_zona, cod_puesto,
                                    nom_departamento, nom_municipio, nombre_puesto, direccion_puesto,
                                    tipo_zona, mesa, latitud, longitud
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (cod_departamento, cod_municipio, cod_zona, cod_puesto) 
                                DO UPDATE SET
                                    nom_departamento = EXCLUDED.nom_departamento,
                                    nom_municipio = EXCLUDED.nom_municipio,
                                    nombre_puesto = EXCLUDED.nombre_puesto,
                                    direccion_puesto = EXCLUDED.direccion_puesto,
                                    tipo_zona = EXCLUDED.tipo_zona,
                                    mesa = EXCLUDED.mesa,
                                    latitud = EXCLUDED.latitud,
                                    longitud = EXCLUDED.longitud;
                            """)
                            
                            cur.execute(insert_query, (
                                cod_departamento, cod_municipio, cod_zona, cod_puesto,
                                nom_departamento, nom_municipio, nombre_puesto, direccion_puesto,
                                tipo_zona, mesa, latitud, longitud
                            ))
                            rows_inserted += 1
                            
                        except Exception as e:
                            print(f"Error inserting row {clean_row}: {e}")
                            conn.rollback()
                            continue

            if (i + 1) % 50 == 0:
                conn.commit()
                print(f"Processed {i + 1}/{total_pages} pages. Rows inserted: {rows_inserted}")
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Extraction complete. {rows_inserted} rows inserted into DB.")

if __name__ == "__main__":
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
    else:
        extract_and_load(pdf_path)
