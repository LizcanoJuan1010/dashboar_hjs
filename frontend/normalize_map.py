import json

# Path matches where we copied it
input_path = '/mnt/e/Data_Horacio/Dashboard/frontend/public/maps/colombia.json'
output_path = '/mnt/e/Data_Horacio/Dashboard/frontend/public/maps/colombia.json'

with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for feature in data['features']:
    # Ensure ID is the Divipole code (DPTO)
    # User specifically asked for Divipole codes. In this file DPTO is the 2-digit code.
    if 'DPTO' in feature['properties']:
        feature['id'] = feature['properties']['DPTO']
    
    # Clean up properties if needed, but keeping them is safer for tooltips
    # Ensure projection compatibility? standard CRS84 is fine for D3

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f)

print(f"Normalized {len(data['features'])} features.")
