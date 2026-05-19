"""
Extrae GUIDs del elevation_service.exe de Brave buscando patrones de CLSID
"""
import re, sys

path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\148.1.90.122\elevation_service.exe"

with open(path, "rb") as f:
    data = f.read()

# Buscar strings ASCII que parezcan GUIDs
ascii_data = data.decode("latin-1", errors="replace")
guids = re.findall(r'\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}', ascii_data)
unique = sorted(set(guids))

print(f"Found {len(unique)} unique GUIDs in elevation_service.exe:")
for g in unique:
    print(f"  {g}")
