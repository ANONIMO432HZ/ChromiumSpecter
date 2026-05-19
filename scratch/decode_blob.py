import struct

hex_str = '2d00000002433a5c50726f6772616d20'
data = bytes.fromhex(hex_str)
print('Primeros 16 bytes del blob Brave:')
for i, b in enumerate(data):
    c = chr(b) if 32 <= b < 127 else '.'
    print(f'  [{i:2d}] 0x{b:02x} ({b:3d}) = {c}')

print()
header_len = struct.unpack_from('<I', data, 0)[0]
print(f'Header len (LE u32 @ offset 0): {header_len}')
print(f'Flag byte   (offset 4):         {data[4]} = 0x{data[4]:02x}')
print(f'Text @ offset 5+: {data[5:].decode("latin-1")}')
print()
print('INTERPRETACIÓN:')
print(f'  Flag=2 → Este blob sigue el formato de tipo 2 (app-bound con ruta de proceso)')
print(f'  La ruta del proceso de Chrome/Brave: C:\\Program ...')
print(f'  Blob total len: 85 bytes')
print(f'  Flag 232 (0xE8) es el byte de FLAG en el contenido DPAPI descifrado, NO en el blob v20 externo')
