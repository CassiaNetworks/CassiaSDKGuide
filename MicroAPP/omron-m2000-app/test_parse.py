import math

def sfloat_to_float(byte1, byte2):
    raw = (byte2 << 8) | byte1
    if raw == 0x07FF: return float('nan')
    if raw == 0x07FE: return float('inf')
    if raw == 0x0802: return float('-inf')
    mantissa = raw & 0x0FFF
    if mantissa >= 0x0800: mantissa = -((0x1000) - mantissa)
    exponent = raw >> 12
    if exponent >= 0x0008: exponent = -((0x0010) - exponent)
    return mantissa * (10 ** exponent)

hex_str = "1E840049005C00000000000000004C00010000"
data = bytes.fromhex(hex_str)
flags = data[0]

sys_val = sfloat_to_float(data[1], data[2])
dia_val = sfloat_to_float(data[3], data[4])
map_val = sfloat_to_float(data[5], data[6])

print(f"Flags: {flags:02X}")
print(f"Sys: {sys_val}")
print(f"Dia: {dia_val}")
print(f"MAP: {map_val}")

current_offset = 7
if (flags & 0x02): # Timestamp
    current_offset += 7

if (flags & 0x04): # Pulse
    pulse = sfloat_to_float(data[current_offset], data[current_offset+1])
    print(f"Pulse: {pulse}")

