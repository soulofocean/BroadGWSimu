# coding:utf-8
from LogHelper import LogHelper
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
        # 发送的bytes
        self.send_data_bytes: bytes = b''
        # region 异常回复的相关变量
        # endregion
        self.init_basic_info()

    def init_basic_info(self):
        """
        将收到的self.recv_data进行拆分和解析，存放在各个变量中
        :return:
        """
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
            self.send_cmd_type = self.recv_cmd_type[:]
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
            self.log.error("Invalid recive, ignore!")

    def handle_reply_msg(self):
        """
        处理回复信息
        :return:
        """
        if self.recv_cmd_type == b'\x04':
            self.handle_04_reply_msg()
        elif self.recv_cmd_type == b'\x10':
            self.handle_10_reply_msg()
        else:
            self.log.error("Not support recv_cmd_type:{}".format(disp_binary(self.recv_cmd_type)))

    def get_function_obj(self, cmd_str):
        """
        获取包含了cmd_str的和self.regaddr的类方法对象
        :param cmd_str: 10为读寄存器相关实例方法，04为写寄存器的相关实例方法，此字段为防止读写恰好寄存器地址相同时候冲突
        :return: callable的实例方法，找不到则返回空
        """
        if self.reg_addr:
            fname = '_{}_{}_'.format(cmd_str, ''.join(map(lambda x: "{:02x}".format(x), self.reg_addr)))
            funs = [x for x in self.__dir__() if fname in x]
            if funs:
                self.log.info("get funs:{}".format(funs))
                callfun = self.__getattribute__(funs[0].lower())
                if callfun and callable(callfun):
                    return callfun
                else:
                    self.log.error("callfun:{} is None or not callable".format(callfun))
            else:
                self.log.error('get function by fname:{} fail'.format(fname))

    def handle_04_reply_msg(self):
        """
        处理04读寄存器指令的各项操作回复
        :return:
        """
        call_obj = self.get_function_obj(cmd_str='04')
        if call_obj:
            call_obj()

    def handle_10_reply_msg(self):
        """
        处理10读寄存器指令的各项操作回复
        :return:
        """
        self.send_msg_len = b'\x00\x06'
        call_obj = self.get_function_obj(cmd_str='10')
        if call_obj:
            call_obj()

    def build_ex_msg_reply(self, ex_msg_len=b'\x00\x06', exp_code=b'\x04', ex_offset=0x80):
        self.send_cmd_type = bytes([ord(self.recv_cmd_type) + ex_offset, ])
        self.send_data_bytes = self.seq + self.pro_tag + ex_msg_len + self.unit_tag + self.send_cmd_type + exp_code

    # region 04 build reply msg
    def build_read_reg_reply(self, data_str, send_msg_len: bytes = None, send_data_len: bytes = None, fill=False):
        """
        组装读寄存器的回复bytes存放到self.send_data_bytes中
        :param data_str: 要组包的数据
        :param send_msg_len: 第一个长度指定值，默认不指定
        :param send_data_len: 第二个长度指定值，默认不指定
        :param fill: 长度不足是否需要填充，默认不填充
        :return:
        """
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
        self.send_data_bytes = self.seq + self.pro_tag + send_msg_len + (
                self.unit_tag + self.recv_cmd_type + send_data_len + data_bytes)

    def handle_04_1069_action(self):
        """查询设备ID"""
        self.build_read_reg_reply(self.dev_info.dev_id + self.dev_info.dev_model)

    def handle_04_107d_action(self):
        """查询软件版本"""
        self.build_read_reg_reply(self.dev_info.soft_version)

    def handle_04_5208_action(self):
        """查询分区名称和编码"""
        self.dev_info.get_region_info_bytes()
        self.build_read_reg_reply(self.dev_info.region_id_name_bytes)

    def handle_04_2710_action(self):
        """查询所有会话状态"""
        self.build_read_reg_reply('', fill=True)

    def handle_04_0001_action(self):
        """查询分区状态"""
        tmp_bytes = self.dev_info.get_region_status_bytes()
        self.build_read_reg_reply(tmp_bytes)

    def handl_04_1770_action(self):
        """
        查询正在播放的音频文件名称
        :return:
        """
        # 00 01 00 00 00 06 FF 04 17 70 0B 00
        # 查询正在播放的音频文件名称 暂不支持 直接回复异常
        self.build_ex_msg_reply()

    def handl_04_7922_action(self):
        """
        查询设备SDP
        :return:
        """
        # 00 01 00 00 00 06 FF 04 79 22 01 F4
        # 查询设备SDP 暂不支持，仅当异常回复
        self.build_ex_msg_reply()

    # endregion

    # region 10 build reply msg
    def build_write_reg_reply(self):
        """
        组合写寄存器的回包，存放在self.send_data_bytes中
        :return:
        """
        reg_num_bytes = struct.pack('>H', self.reg_num)
        self.send_data_bytes = self.seq + self.pro_tag + self.send_msg_len + (
                self.unit_tag + self.send_cmd_type + self.reg_addr + reg_num_bytes)

    def handle_10_03e8_action(self):
        """
        即时播放/停止广播
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_07d1_action(self):
        """
        音量控制
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_07da_action(self):
        """
        播放上一首/下一首
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_07e4_action(self):
        """
        播放暂停/恢复
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_0bb8_action(self):
        """
        日定时配置下载
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_0fa0_action(self):
        """
        周定时配置下载
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_1004_action(self):
        """
        特别定时配置下载
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_1388_action(self):
        """
        删除所有定时配置
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_1389_action(self):
        """
        删除某个日定时配置
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_13ec_action(self):
        """
        删除周定时配置
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_1450_action(self):
        """
        删除特别定时配置
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_4e20_action(self):
        """
        设置AES秘钥
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_4e84_action(self):
        """
        固件升级
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_7918_action(self):
        """
        开始直播
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_791f_action(self):
        """
        停止直播
        :return:
        """
        self.build_write_reg_reply()

    def handle_10_7b0c_action(self):
        """
        设备重启
        :return:
        """
        self.build_write_reg_reply()
    # endregion


if __name__ == '__main__':
    ...
