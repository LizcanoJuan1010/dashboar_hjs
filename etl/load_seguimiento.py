import pandas as pd
import psycopg2
import os
import time
import re

# Configuration
INPUT_FILE = '/app/data/data/SEGUIMIENTO A LIDERES CAMPAÑA HJS 2023.xlsx'
LOG_FILE = '/app/data/processing.log'
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

def log(msg):
    print(msg)
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
            log(f"DB not ready, retrying... {e}")
            time.sleep(5)
            retries -= 1
    raise Exception("DB Connection failed")

def clean_int(val):
    if pd.isna(val) or val == 'NO' or str(val).strip() == '-' or str(val).lower() == 'nan':
        return 0
    try:
        val_str = str(val).replace(',','').replace('.0', '').strip()
        if not val_str: return 0
        return int(float(val_str))
    except:
        return 0

def load_tracking():
    # Clear log
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        
    conn = get_db_connection()
    cur = conn.cursor()
    # TRUNCATE to avoid dupes on re-run
    log("🗑️ Truncating tables...")
    cur.execute("TRUNCATE TABLE candidatos_gestion CASCADE;")
    cur.execute("TRUNCATE TABLE lideres_campana CASCADE;")
    
    log(f"📂 Reading {INPUT_FILE}...")
    
    try:
        xl = pd.ExcelFile(INPUT_FILE)
        log(f"   Sheets found: {xl.sheet_names}")
        
        # 1. Process Candidates
        candidate_sheets = [s for s in xl.sheet_names if "Candidatos" in s or "Otros partidos" in s]
        
        insert_cand_query = """
            INSERT INTO candidatos_gestion (
                nombre_candidato, partido, voto_estimado, publicidad_compartida,
                hojas_vida_entregadas, verificado, damas_gratis, boletas_bingo,
                pendones_entregados, reunion_info
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cand_count = 0
        for sheet in candidate_sheets:
            log(f"👉 Processing Candidates Sheet: {sheet}")
            df_raw = pd.read_excel(xl, sheet, header=None, nrows=10, dtype=str)
            
            header_row_idx = None
            for idx, row in df_raw.iterrows():
                row_str = " ".join([str(x).upper() for x in row.values])
                if ("CANDIDATO" in row_str or "NOMBRE" in row_str) and ("VOTOS" in row_str or "PUBLICIDAD" in row_str or "COMUNA" in row_str):
                     header_row_idx = idx
                     break
            
            if header_row_idx is None:
                log(f"   ⚠️ Could not find header row in {sheet}, trying default 0")
                header_row_idx = 0
            else:
                 log(f"   Found header at row {header_row_idx}")

            df = pd.read_excel(xl, sheet, header=header_row_idx, dtype=str)
            df.columns = [str(c).upper().strip() for c in df.columns]
            log(f"   Columns: {df.columns.tolist()}")
            
            for idx, row in df.iterrows():
                name = None
                for col in ['CANDIDATO', 'NOMBRE', 'NOMBRE CANDIDATO', 'CANDIDATOS', 'NOMBRES Y APELLIDOS', 'NOMBRES']:
                    if col in df.columns and pd.notna(row[col]):
                         val = str(row[col]).strip()
                         if val.upper() not in ['CANDIDATO', 'NOMBRE', 'NAN', 'NOMBRES Y APELLIDOS']:
                            name = val
                            break
                
                if not name: continue
                
                def get_val(possible_cols):
                    for c in possible_cols:
                        if c in df.columns:
                            return row[c]
                    return None

                votos = clean_int(get_val(['VOTOS OBTENIDOS', 'VOTOS']))
                pub = get_val(['PUBLICIDAD COMPARTIDA', 'PUBLICIDAD'])
                hv = clean_int(get_val(['HOJAS DE VIDA', 'HOJAS']))
                verif = get_val(['VERIFICADO'])
                damas = clean_int(get_val(['NUMERO DE BOLETAS DAMAS GRATIS', 'DAMAS GRATIS', 'DAMAS']))
                bingo = clean_int(get_val(['NUMERO DE BOLETAS BINGO', 'BOLETAS BINGO', 'BINGO', 'NUMERO DE BOLETAS']))
                pend = clean_int(get_val(['PENDONES']))
                reunion = get_val(['REUNIÓN', 'REUNION'])
                
                cur.execute(insert_cand_query, (
                    name, sheet, votos, pub, hv, verif, damas, bingo, pend, reunion
                ))
                cand_count += 1
                
        log(f"✅ Loaded {cand_count} candidates.")
        
        # 2. Process Leaders
        leader_sheet = next((s for s in xl.sheet_names if "LIDERES" in s.upper() or "LÍDERES" in s.upper()), None)
        
        if leader_sheet:
            log(f"👉 Processing Leaders Sheet: {leader_sheet}")
            
            df_raw_l = pd.read_excel(xl, leader_sheet, header=None, nrows=10, dtype=str)
            header_row_idx_l = None
            for idx, row in df_raw_l.iterrows():
                row_str = " ".join([str(x).upper() for x in row.values])
                if ("LIDER" in row_str or "NOMBRE" in row_str) and ("VOTOS" in row_str or "META" in row_str or "COMUNA" in row_str):
                     header_row_idx_l = idx
                     break
            
            if header_row_idx_l is None:
                 log(f"   ⚠️ Could not find header row for Leaders, trying default 0")
                 header_row_idx_l = 0
            else:
                 log(f"   Found Leaders header at row {header_row_idx_l}")
            
            df_lid = pd.read_excel(xl, leader_sheet, header=header_row_idx_l, dtype=str)
            df_lid.columns = [str(c).upper().strip() for c in df_lid.columns]
            log(f"   Columns: {df_lid.columns.tolist()}")
            
            insert_lid_query = """
                INSERT INTO lideres_campana (
                    nombre_completo, meta_votos, verificado,
                    hojas_vida_entregadas, boletas_bingo, damas_gratis,
                    pendones, reunion_info
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            lid_count = 0
            for idx, row in df_lid.iterrows():
                name = None
                for col in ['LIDER', 'NOMBRE', 'NOMBRE LIDER', 'LÍDER', 'LIDERES', 'NOMBRES Y APELLIDOS', 'NOMBRES']:
                    if col in df_lid.columns and pd.notna(row[col]):
                        val = str(row[col]).strip()
                        if val.upper() not in ['LIDER', 'NOMBRE', 'NAN', 'NOMBRES Y APELLIDOS', 'LIDERES', 'LÍDERES']:
                            name = val
                            break
                
                if not name: continue
                
                def get_val_l(possible_cols):
                    for c in possible_cols:
                        if c in df_lid.columns:
                            return row[c]
                    return None
                
                votos = clean_int(get_val_l(['VOTOS OBTENIDOS', 'META', 'VOTOS']))
                verif = get_val_l(['VERIFICADO'])
                hv = clean_int(get_val_l(['HOJAS DE VIDA', 'HOJAS']))
                bingo = clean_int(get_val_l(['NUMERO DE BOLETAS BINGO', 'BINGO']))
                damas = clean_int(get_val_l(['NUMERO DE BOLETAS DAMAS GRATIS', 'DAMAS']))
                pend = clean_int(get_val_l(['PENDONES']))
                reunion = get_val_l(['REUNIÓN', 'REUNION'])
                
                cur.execute(insert_lid_query, (
                    name, votos, verif, hv, bingo, damas, pend, reunion
                ))
                lid_count += 1
            log(f"✅ Loaded {lid_count} leaders.")
        else:
            log("⚠️ Leader sheet not found!")
            
        conn.commit()
        log("🏁 DONE! Tracking data loaded.")
        
    except Exception as e:
        log(f"❌ Error: {e}")
        conn.rollback()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    if os.path.exists(INPUT_FILE):
        load_tracking()
    else:
        log(f"❌ File not found: {INPUT_FILE}")
