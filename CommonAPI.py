# coding:utf-8
import struct
import time
def get_log_name(folder_name = 'log', prefix_name = 'log',ext_name = '.log'):
    timeStr = time.strftime('%Y_%m_%d_%H%M%S', time.localtime(time.time()))
    return "{}/{}_{}{}".format(folder_name,prefix_name,timeStr,ext_name)

def disp_binary(data: bytes, split: str = r'\x', order: str = '>', sign: str = 'B'):
    """
    显示bytes字符串
    :param data: 源bytes
    :param split: 字符串分隔符，默认为\\x
    :param order: data struct.unpack解码顺序
    :param sign: data struct.unpack解码符号如B，H等
    :return: bytes对应的二进制字符串
    """
    f = '{}{}'.format(order, sign * len(data))
    return ''.join("{}{:02x}".format(split, b) for b in struct.unpack(f, data))


def fomate_bytes(data, reg_num: int = 0, encoding: str = 'utf-16be', reg_size: int = 2,
                 fill_info: bytes = b'\x00'):
    """
    将data编码成指定长度的bytes
    :param data: 要编码的对象，如果不是bytes就encode
    :param reg_num: 最长寄存器数目，默认为0，为0则不限制长度
    :param encoding: 编码方式，默认utf-16be
    :param reg_size: 寄存器大小，默认2个字节，为0则不限制大小
    :param fill_info: 长度不足的填充信息，默认填充\\x00
    :return: 返回编码后的bytes,如果输入为bytes不会修改编码
    """
    result: bytes = data
    expect_len = reg_num * reg_size
    # 如果传进来的是bytes就直接用，否则就encode一下
    if not isinstance(data, bytes):
        result = data.encode(encoding)
    fill_len = expect_len - len(result)
    if fill_len > 0:
        result += (fill_info * fill_len)
    if expect_len and len(result) > expect_len:
        result = result[:expect_len]
    return result
