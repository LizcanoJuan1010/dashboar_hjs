import json

# DANE to DIVIPOLE mapping
DANE_TO_DIVIPOLE = {
    "05": "01", # Antioquia
    "08": "03", # Atlántico
    "11": "16", # Bogotá D.C.
    "13": "05", # Bolívar
    "15": "07", # Boyacá
    "17": "09", # Caldas
    "18": "11", # Caquetá
    "19": "13", # Cauca
    "20": "15", # Cesar
    "23": "17", # Córdoba
    "25": "19", # Cundinamarca
    "27": "21", # Chocó
    "41": "23", # Huila
    "44": "25", # La Guajira
    "47": "27", # Magdalena
    "50": "29", # Meta
    "52": "31", # Nariño
    "54": "33", # Norte de Santander
    "63": "35", # Quindío
    "66": "37", # Risaralda
    "68": "39", # Santander
    "70": "41", # Sucre
    "73": "43", # Tolima
    "76": "45", # Valle del Cauca
    "81": "47", # Arauca
    "85": "49", # Casanare
    "86": "51", # Putumayo
    "88": "53", # San Andrés
    "91": "55", # Amazonas
    "94": "57", # Guainía
    "95": "59", # Guaviare
    "97": "61", # Vaupés
    "99": "63"  # Vichada
}

# Read the GeoJSON file
with open(r'E:\Data_Horacio\Dashboard\frontend\mapa_departamentos_colombia\colombia.geo.json', 'r', encoding='utf-8') as f:
    geojson = json.load(f)

# Update DPTO codes
updated_count = 0
for feature in geojson['features']:
    old_code = feature['properties'].get('DPTO')
    if old_code in DANE_TO_DIVIPOLE:
        feature['properties']['DPTO'] = DANE_TO_DIVIPOLE[old_code]
        updated_count += 1
        print(f"Updated: {old_code} -> {DANE_TO_DIVIPOLE[old_code]} ({feature['properties'].get('NOMBRE_DPT', 'Unknown')})")
    else:
        print(f"WARNING: No mapping for DANE code {old_code} ({feature['properties'].get('NOMBRE_DPT', 'Unknown')})")

# Write updated GeoJSON
with open(r'E:\Data_Horacio\Dashboard\frontend\mapa_departamentos_colombia\colombia.geo.json', 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False)

print(f"\nTotal features updated: {updated_count}")
