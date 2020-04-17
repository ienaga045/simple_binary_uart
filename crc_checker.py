#CRC16-CCITT 0xFFFF
#dataはbytes型
import binascii

def crc16_ccitt(data):
    crc = 0xffff
    msb = crc >> 8
    lsb = crc & 255
    for c in data:
        x = c ^ msb
        x ^= (x >> 4)
        msb = (lsb ^ (x >> 3) ^ (x << 4)) & 255
        lsb = (x ^ (x << 5)) & 255
    return (msb << 8) + lsb

# 結果を表示

if __name__ == '__main__':
    key_input = input('input hex(0-f):')
    
    if (len(key_input) % 2) == 1 : #入力が奇数桁だった場合
        key_input = '0' + key_input

    print('hex: 0x' + key_input)

    command = binascii.unhexlify(key_input) #文字列(0-f)からhexコード
    print('crc:' + hex(crc16_ccitt(command)))

    input('press any key to Exit')
