# coding:utf-8
import LogHelper
import struct
from CommonAPI import disp_binary, fomate_bytes
from DeviceInfo import DeviceInfoType


class ModbusType:
    def __init__(self, log: LogHelper, data: bytes = b''):
        self.recv_valid = False
        self.log: LogHelper = log
        self.dev_info = DeviceInfoType()
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
        self.log.info("recv:{}".format(disp_binary(data)))
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
            self.log.info("seq:{} cmd_type:{} reg_addr:{} reg_num:{}".format(disp_binary(self.seq),
                                                                             disp_binary(self.recv_cmd_type),
                                                                             struct.unpack(">H", self.reg_addr)[0],
                                                                             self.reg_num))
        else:
            self.recv_valid = False
            self.log.info("Invalid recive, ignore!")

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
            self.log.warn("Not support reg_addr:{}".format(disp_binary(self.reg_addr)))

    def build_read_reg_reply(self, data_str, send_msg_len: bytes = None, send_data_len: bytes = None, fill=False):
        expect_len = self.reg_num * self.dev_info.reg_size if fill else 0
        data_bytes = fomate_bytes(data_str, expect_len)
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
        """查询设备ID"""
        self.build_read_reg_reply(self.dev_info.dev_id + self.dev_info.dev_model)

    def build_107D_4221_reply(self):
        """查询软件版本"""
        self.build_read_reg_reply(self.dev_info.soft_version)

    def build_5208_21000_reply(self):
        """查询分区名称和编码"""
        self.dev_info.get_region_info_bytes()
        self.build_read_reg_reply(self.dev_info.region_id_name_bytes)

    def build_2710_10000_reply(self):
        """查询所有会话状态"""
        self.build_read_reg_reply('', fill=True)

    def build_0001_1_reply(self):
        """查询分区状态"""
        tmp_bytes = self.dev_info.get_region_status_bytes()
        self.build_read_reg_reply(tmp_bytes)
