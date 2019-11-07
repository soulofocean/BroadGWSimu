# coding:utf-8
import struct
import time


def get_log_name(folder_name='log', prefix_name='log', ext_name='.log'):
    """
    获取日志名称,默认为log/log_Y_m_d_HMS
    :param folder_name:日志所在目录，默认为log
    :param prefix_name:日志名称，默认为log
    :param ext_name: 日志后缀名，默认为.log
    :return: 日志全名，默认为log/log_yyyy_mm_dd_HHMMSS
    """
    timeStr = time.strftime('%Y_%m_%d_%H%M%S', time.localtime(time.time()))
    return "{}/{}_{}{}".format(folder_name, prefix_name, timeStr, ext_name)


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


def fomate_bytes(data, expect_len: int = 0, encoding: str = 'utf-16be', fill_info: bytes = b'\x00'):
    """
    将data编码成指定长度的bytes
    :param data: 要编码的对象，如果不是bytes就encode
    :param expect_len: 格式化后最大长度，默认为0，为0则不限制长度
    :param encoding: 编码方式，默认utf-16be
    :param fill_info: 长度不足的填充信息，默认填充\\x00
    :return: 返回编码后的bytes,如果输入为bytes不会修改编码
    """
    result: bytes = data
    # 如果传进来的是bytes就直接用，否则就encode一下
    if not isinstance(data, bytes):
        result = data.encode(encoding)
    fill_len = expect_len - len(result)
    if fill_len > 0:
        result += (fill_info * fill_len)
    if expect_len and len(result) > expect_len:
        result = result[:expect_len]
    return result


def fomate_str(data: str, expect_len: int = 0, fill_str: str = ' '):
    """
    将字符串格式化成指定长度的字符串，超出部分截取，不足则补上指定字符，可能抛出NotImplementedError
    :param data: 即将被格式化的字符串
    :param expect_len: 字符串格式化后的长度，默认为0即返回原字符串
    :param fill_str: 填充的字符串，默认为空格，目前仅支持传入长度为1的字符串,
    :return: 指定长度的字符串
    """
    result = ''
    data_len = 0
    if data:
        data_len = len(data)
        result = data
    fill_len = expect_len - data_len
    if fill_len > 0:
        if fill_str and len(fill_str) == 1:
            result += fill_str * fill_len
        else:
            raise NotImplementedError("Not support fill_str: it is null or len not 1")
    if expect_len and len(result) > expect_len:
        result = result[:expect_len]
    return result


if __name__ == '__main__':
    ...
