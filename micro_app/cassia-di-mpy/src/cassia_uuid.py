import uos, binascii


def uuid4():
    """返回形如 'a1b2c3d4-e5f6-7890-abcd-1234567890ab' 的字符串"""
    b = uos.urandom(16)
    # 把第7、9字节的高4位分别设为 0x40、0x80，符合 RFC 4122
    b = bytearray(b)
    b[6] = (b[6] & 0x0F) | 0x40
    b[8] = (b[8] & 0x3F) | 0x80
    hex = binascii.hexlify(b).decode()
    return "{}-{}-{}-{}-{}".format(hex[:8], hex[8:12], hex[12:16], hex[16:20], hex[20:])