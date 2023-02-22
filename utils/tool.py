import struct
from Crypto.Cipher import AES


def prepare_data(filepath: str):
    """
    准备数据
    :param filepath:  文件路径
    :return:
    """
    with open(filepath, 'r') as f:
        data = f.readlines()
        return [i.rstrip('\n').split(' ') for i in data]


def padding(data: bytes) -> bytes:
    """
    补位
    @param data:
    @return:
    """
    add_num = 16 - (len(data) % 16)
    pad_data = data + b'\0' * add_num
    return pad_data


def encrypt(_key: bytes, data: bytes) -> bytes:
    """
    加密方法
    :param _key: 加密密钥
    :param data: 发包数据
    :return:
    """
    if len(_key) % 16 == 0:
        key = _key
    else:
        key = padding(_key)
    head_data = struct.pack("<i", len(data)) + data
    data = padding(head_data)
    aes = AES.new(key, AES.MODE_CBC, iv=bytes(16))
    return aes.encrypt(data)


def decrypt(_key: bytes, packet: bytes) -> bytes:
    """
    解密
    :param _key: 解密密钥
    :param packet: 回包
    :return:
    """
    if len(_key) % 16 == 0:
        key = _key
    else:
        key = padding(_key)
    cipher = AES.new(key, AES.MODE_CBC, bytes(16))
    return cipher.decrypt(packet)


def record_result(filepath: str, res: str):
    """记录结果"""
    with open(filepath, 'a+', encoding="utf-8") as f:
        f.write(res)
