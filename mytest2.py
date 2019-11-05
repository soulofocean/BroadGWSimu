# coding:utf-8
import time
import socket
import struct


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
    :param fill_info: 长度不足的填充信息，默认填充\x00
    :return: 返回编码后的bytes,如果输入为bytes不会修改编码
    """
    result: bytes = b''
    expect_len = reg_num * reg_size
    # 如果传进来的是bytes就直接用，否则就encode一下
    if not isinstance(data, bytes):
        result = data.encode(encoding)
    else:
        result = data
    fill_len = expect_len - len(result)
    if fill_len > 0:
        result += (fill_info * fill_len)
    if expect_len and len(result) > expect_len:
        return result[:expect_len]
    else:
        return result


def get_time_str():
    """
    获取当前时间的字符串
    :return: 当前时间字符串
    """
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))


class DeviceInfoType:
    """
    设备信息封装类
    """
    def __init__(self):
        self.dev_id = ''
        self.dev_model = ''
        self.sub_dev_type = 3022
        self.soft_version = ''
        self.region_name = ''
        self.region_count = 0
        self.region_id_name_bytes = b''
        self.region_status_bytes = b''
        # 最多64个分区
        self.max_region_count = 64
        # 每个分区的ID和名字分别占用30个寄存器
        self.region_reg_num = 30

    def get_region_info_bytes(self):
        """
        获取分区表的bytes存放在self.region_bytes中
        :return: None
        """
        if not self.region_id_name_bytes:
            tmp_br = bytearray()
            if self.dev_id and self.region_name:
                if self.region_count > self.max_region_count:
                    self.region_count = self.max_region_count
                for c in range(self.region_count):
                    new_dev_id = str(self.sub_dev_type) + self.dev_id[8:20] + "{:04d}".format(c + 1)[:4]
                    tmp_br.extend(fomate_bytes(new_dev_id, self.region_reg_num))
                    new_region_name = self.region_name + "{:04d}".format(c + 1)[:4]
                    tmp_br.extend(fomate_bytes(new_region_name, self.region_reg_num))
                # left_count = self.max_region_count - self.region_count
                # if left_count:
                #     tmp_br.extend(fomate_bytes('', left_count * 30 * 2))
            self.region_id_name_bytes = bytes(tmp_br)

    def get_region_status_bytes(self):
        """
        获取分区状态bytes
        :return:分区状态的bytes
        """
        if not self.region_status_bytes:
            tmp_br = bytearray()

class ModbusType:
    def __init__(self, data: bytes = b''):
        self.recv_valid = False
        self.reg_size = 2
        self.dev_info = DeviceInfoType()
        self.dev_info.dev_id = '10212019201988800001'
        self.dev_info.dev_model = 'ITC-7800A'
        self.dev_info.soft_version = '5.2'
        self.dev_info.region_name = '分区'
        self.dev_info.region_count = 2
        # 事务标识
        self.seq = b''
        # 协议标识，modbus为固定\x00\x00
        self.pro_tag = b''
        # 消息长度1,指的modbus协议中报文头中那个2个字节的长度
        self.recv_msg_len = b''
        self.send_msg_len = b''
        # 单元标识，一般固定为\xff
        self.unit_tag = b''
        # 命令类型目前仅支持两个 \x04为读寄存器，\x01为写寄存器
        self.recv_cmd_type = b''
        self.send_cmd_type = b''
        # 要读写的寄存器起始地址
        self.reg_addr = b''
        # 读写寄存器的数目
        self.reg_num = 0
        # 收到的二进制
        self.recv_data: bytes = data
        self.send_data_bytes: bytes = b''
        self.init_basic_info()

    def init_basic_info(self):
        data = self.recv_data
        print("[{}]recv:{}".format(get_time_str(), disp_binary(data)))
        if data and len(data) >= 12:
            self.recv_valid = True
            # 事务标识
            self.seq = data[0:2]
            # 协议标识，modbus为固定\x00\x00
            self.pro_tag = data[2:4]
            # 消息长度
            self.recv_msg_len = data[4:6]
            # 单元标识，一般固定为\xff
            self.unit_tag = data[6:7]
            # 命令类型 \x04为读寄存器，\x01为写寄存器
            self.recv_cmd_type = data[7:8]
            # 要读写的寄存器起始地址
            self.reg_addr = data[8:10]
            # 读写寄存器的数目
            self.reg_num = struct.unpack('>H', data[10:12])[0]
            print("seq:{} cmd_type:{} reg_addr:{} reg_num:{}".format(self.seq, self.recv_cmd_type,
                                                                     struct.unpack(">H", self.reg_addr)[0],
                                                                     self.reg_num))
        else:
            self.recv_valid = False
            print("Invalid recive, ignore!")

    def get_reply_msg(self):
        if self.reg_addr == b'\x10\x69':
            self.build_1069_4201_reply()
        elif self.reg_addr == b'\x10\x7d':
            self.build_107D_4221_reply()
        elif self.reg_addr == b'\x52\x08':
            # \x00\x03\x00\x00\x00\x06\xff\x04\x52\x08\x0f\x00
            # 查询分区名称和编码
            self.build_5208_21000_reply()
        elif self.reg_addr == b'\x27\x10':
            # \x00\x04\x00\x00\x00\x06\xff\x04\x27\x10\x03\x20
            # 查询所有会话状态
            self.build_2710_10000_reply()
        elif self.reg_addr == b'\x00\x01':
            # \x00\x08\x00\x00\x00\x06\xff\x04\x00\x01\x00\x80
            # 查询分区状态
            self.build_0001_1_reply()
        else:
            print("Not support reg_addr:", disp_binary(self.reg_addr))

    def build_read_reg_reply(self, data_str, send_msg_len: bytes = None, send_data_len: bytes = None, fill=False):
        bytes_len = self.reg_num if fill else 0
        data_bytes = fomate_bytes(data_str, bytes_len)
        send_msg_len_int = len(data_bytes) + 3
        if not send_msg_len:
            send_msg_len = struct.pack('>H', send_msg_len_int)
        if not send_data_len:
            if send_msg_len_int - 3 > 0xFF:
                send_data_len = b'\xFF'
            else:
                send_data_len = struct.pack('>B', send_msg_len_int - 3)
        self.send_data_bytes = (self.seq + self.pro_tag) + send_msg_len + (
                self.unit_tag + self.recv_cmd_type) + send_data_len + data_bytes

    def build_1069_4201_reply(self):
        '''查询设备ID'''
        self.build_read_reg_reply(self.dev_info.dev_id + self.dev_info.dev_model)

    def build_107D_4221_reply(self):
        '''查询软件版本'''
        self.build_read_reg_reply(self.dev_info.soft_version)

    def build_5208_21000_reply(self):
        '''查询分区名称和编码'''
        self.dev_info.get_region_info_bytes()
        self.build_read_reg_reply(self.dev_info.region_id_name_bytes)

    def build_2710_10000_reply(self):
        '''查询所有会话状态'''
        self.build_read_reg_reply('',fill=True)

    def build_0001_1_reply(self):
        '''查询分区状态'''
        self.dev_info.get_region_status_bytes()
        self.build_read_reg_reply(self.dev_info.region_status_bytes)


if __name__ == '__main__':
    print("[{}] start...".format(get_time_str()))
    address = ('172.26.92.152', 502)
    resv_buff = 1024
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # s = socket.socket()
    s.bind(address)
    s.listen(5)
    ss, addr = s.accept()
    print('[{}]got connected from{}'.format(get_time_str(), addr))
    while True:
        ra = ss.recv(resv_buff)
        while len(ra) <= 0:
            continue
        resv_info = ModbusType(ra)
        if not resv_info.recv_valid:
            continue
        resv_info.get_reply_msg()
        if resv_info.send_data_bytes:
            print("[{}]send:{}".format(get_time_str(), disp_binary(resv_info.send_data_bytes)))
            ss.send(resv_info.send_data_bytes)
        # continue
        # send_bytes: bytes = b''
        # # 事务标识
        # seq = ra[0:2]
        # # 协议标识，modbus为固定\x00\x00
        # pro_tag = ra[2:4]
        # # 消息长度
        # msg_len = ra[4:6]
        # # 单元标识，一般固定为\xff
        # unit_tag = ra[6:7]
        # # 命令类型 \x04为读寄存器，\x01为写寄存器
        # cmd_type = ra[7:8]
        # # 要读写的寄存器起始地址
        # reg_addr = ra[8:10]
        # # 读写寄存器的数目
        # reg_num = ra[10:12]
        # # print("seq:{} cmd_type:{} reg_addr:{} reg_num:{}".format(seq, cmd_type, struct.unpack(">H", reg_addr)[0],
        # #                                                          struct.unpack(">H", reg_num)[0]))
        # if reg_addr == b'\x10\x69':
        #     # \x00\x01\x00\x00\x00\x06\xff\x04\x10\x69\x00\x1e
        #     # 查询设备ID
        #     # dev_id = b'\x00\x01\x00\x00\x00\x3f\xff\x04\x3c' + fomate_bytes(b'10202019201988800001') + (b'\x00' * 20)
        #     send_msg_len = b'\x00\x3f'
        #     data_len = b'\x3c'
        #     send_bytes = seq + pro_tag + send_msg_len + unit_tag + cmd_type + data_len + fomate_bytes(
        #         '10202019201988800002', 30)
        # elif reg_addr == b'\x10\x7d':
        #     # \x00\x02\x00\x00\x00\x06\xff\x04\x10\x7d\x00\x20
        #     # 查询软件版本
        #     # send_bytes = b'\x00\x02\x00\x00\x00\x43\xff\x04\x40' + fomate_bytes(b'BoschCallStation_3.0.0.1023') + (
        #     #         b'\x00' * 10)
        #     send_msg_len = b'\x00\x43'
        #     data_len = b'\x40'
        #     send_bytes = seq + pro_tag + send_msg_len + unit_tag + cmd_type + data_len + fomate_bytes(
        #         'BoschCallStation_3.0.0.1023', 32)
        # elif reg_addr == b'\x52\x08':
        #     # \x00\x03\x00\x00\x00\x06\xff\x04\x52\x08\x0f\x00
        #     # 查询分区名称和编码
        #     send_msg_len = b'\x1E\x03'
        #     data_len = b'\x00'
        #     send_bytes = seq + pro_tag + send_msg_len + unit_tag + cmd_type + data_len + fomate_bytes(
        #         '30222019888000020001', 30) + fomate_bytes('分区0001', 30) + fomate_bytes('', 3780)
        # elif reg_addr == b'\x27\x10':
        #     # \x00\x04\x00\x00\x00\x06\xff\x04\x27\x10\x03\x20
        #     # 查询所有会话状态
        #     send_msg_len = b'\x06\x43'
        #     data_len = b'\x40'
        #     send_bytes = seq + pro_tag + send_msg_len + unit_tag + cmd_type + data_len + fomate_bytes('', 800)
        # elif reg_addr == b'\x00\x01':
        #     # \x00\x08\x00\x00\x00\x06\xff\x04\x00\x01\x00\x80
        #     # 查询分区状态
        #     send_msg_len = b'\x01\x03'
        #     data_len = b'\x00'
        #     send_bytes = seq + pro_tag + send_msg_len + unit_tag + cmd_type + data_len + fomate_bytes('', 128)
        # if send_bytes:
        #     print("[{}]send:{}".format(get_time_str(), disp_binary(send_bytes)))
        #     ss.send(send_bytes)
