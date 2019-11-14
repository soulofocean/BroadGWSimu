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
        # 收到的二进制
        self.recv_data: bytes = data
        # 发送的bytes
        self.send_data_bytes: bytes = b''
        self.send_msg_len = self.recv_msg_len
        self.send_function_code = self.recv_function_code
        # self.init_basic_info()

    # region 属性
    @property
    def recv_seq(self):
        """
        MBPA事务标识字段，2 bytes, 俗称消息序列号
        :return:MBPA事务标识字段，2 bytes, 俗称消息序列号
        """
        return self.recv_data[0:2]

    @property
    def recv_pro_tag(self):
        """
        MBPA头协议标识字段，2bytes 一般为固定0x0000
        :return: MBPA头协议标识字段，一般为固定0x0000
        """
        return self.recv_data[2:4]

    @property
    def recv_msg_len(self):
        """
        MBPA头报文长度字段，2bytes
        :return: 接收的报文长度字段，2bytes
        """
        return self.recv_data[4:6]

    @property
    def recv_unit_tag(self):
        """
        MPBA头单元标识，1 byte 一般固定为0xff
        :return: 单元标识，1byte 一般固定为0xff
        """
        return self.recv_data[6:7]

    @property
    def send_MBPA_Header(self):
        """
        返回MB协议MBPA头，由4个字段组成，共计2+2+2+1 =7 bytes
        :return: 返回MB协议MBPA头
        """
        return self.recv_seq + self.recv_pro_tag + self.send_msg_len + self.recv_unit_tag

    @property
    def recv_data_data(self):
        """
        MBPA报文DATA域，参照wireshark取第7个bytes后的内容,即取Header后的内容都算DATA
        :return: MBPA报文DATA域，取第7个bytes后的内容
        """
        return self.recv_data[7:]

    @property
    def recv_function_code(self):
        """
        MB协议功能码字段，1个bytes,0x04是读寄存器，0x10是写寄存器，异常回复功能码会加上0x80
        :return: MB协议功能码字段，1个bytes,0x04是读寄存器，0x10是写寄存器，会影响后面DATA域的格式
        """
        return self.recv_data_data[:1]

    @property
    def recv_reg_addr(self):
        """
        读写寄存器的初始地址，2 bytes,目前协议0x04和0x10的DATA域前2bytes都是寄存器初始地址
        :return: 读写寄存器的初始地址，2 bytes
        """
        # return self.recv_data[8:10]
        return self.recv_data_data[1:3]

    @property
    def recv_reg_num(self):
        """
        读写寄存器的数目，2个bytes，读写寄存器的初始地址，2 bytes,目前协议0x04和0x10的DATA域2-4bytes都是寄存器数量
        :return: 读写寄存器的数目，2个bytes
        """
        # return self.recv_data[10:12]
        return self.recv_data_data[3:5]

    @property
    def recv_byte_count(self):
        """
        表明后面字节长度，只有一个byte
        :return:表明后面字节长度，只有一个byte
        """
        return self.recv_data_data[5:6]

    @property
    def recv_reg_num_int(self):
        """
        读写寄存器的数目,返回的是recv_reg_num转换成的一个int
        :return: 读写寄存器的数目,返回的是recv_reg_num转换成的一个int
        """
        if self.recv_reg_num:
            return struct.unpack('>H', self.recv_reg_num)[0]
        return 0

    # endregion
    def recv_new_msg(self,new_data:bytes):
        self.recv_valid = False
        # 收到的二进制
        self.recv_data: bytes = new_data
        # 发送的bytes
        self.send_data_bytes: bytes = b''
        self.send_msg_len = self.recv_msg_len
        self.send_function_code = self.recv_function_code
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
            self.log.info("seq:{} function_code:{} reg_addr:{} reg_num:{}".format(disp_binary(self.recv_seq),
                                                                                  disp_binary(self.recv_function_code),
                                                                                  struct.unpack(">H",
                                                                                                self.recv_reg_addr)[0],
                                                                                  self.recv_reg_num_int))
        else:
            self.recv_valid = False
            self.log.error("Invalid recive, ignore!")

    def handle_reply_msg(self):
        """
        处理回复信息
        :return:
        """
        if self.recv_function_code == b'\x04':
            self.handle_04_reply_msg()
        elif self.recv_function_code == b'\x10':
            self.handle_10_reply_msg()
        else:
            self.log.error("Not support recv_function_code:{}".format(disp_binary(self.recv_function_code)))

    def get_function_obj(self, cmd_str):
        """
        获取包含了cmd_str的和self.regaddr的类方法对象
        :param cmd_str: 10为读寄存器相关实例方法，04为写寄存器的相关实例方法，此字段为防止读写恰好寄存器地址相同时候冲突
        :return: callable的实例方法，找不到则返回空
        """
        if self.recv_reg_addr:
            fname = '_{}_{}_'.format(cmd_str, ''.join(map(lambda x: "{:02x}".format(x), self.recv_reg_addr)))
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
        self.send_function_code = bytes([ord(self.recv_function_code) + ex_offset, ])
        self.send_msg_len = ex_msg_len
        self.send_data_bytes = self.send_MBPA_Header + self.send_function_code + exp_code

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
        expect_len = self.recv_reg_num_int * self.dev_info.reg_size if fill else 0
        data_bytes = fomate_bytes(data_str, expect_len)
        send_msg_len_int = len(data_bytes) + 3
        if not send_msg_len:
            send_msg_len = struct.pack('>H', send_msg_len_int)
        if not send_data_len:
            if send_msg_len_int - 3 > 0xFF:
                send_data_len = b'\xFF'
            else:
                send_data_len = struct.pack('>B', send_msg_len_int - 3)
        self.send_msg_len = send_msg_len
        self.send_data_bytes = self.send_MBPA_Header + self.send_function_code + (send_data_len + data_bytes)

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
        self.build_read_reg_reply(self.dev_info.session_status_bytes, fill=True)

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
        self.send_data_bytes = self.send_MBPA_Header + self.send_function_code + (
                self.recv_reg_addr + self.recv_reg_num)

    def handle_10_03e8_action(self):
        """
        即时播放/停止广播
        :return:
        """
        logTmp = 'Try to Begin Session:'
        session_id = self.recv_data_data[6:8]
        # 0001代表正在播放
        session_val = b'\x00\x01'
        if self.recv_reg_num_int == 2:
            # 表示停止播放
            session_val = b'\x00\x00'
            logTmp = 'Try to Stop Session:'
        logTmp += disp_binary(session_id)
        self.log.info(logTmp)
        self.log.info("sessionid:{} session_val:{}".format(disp_binary(session_id),disp_binary(session_val)))
        self.dev_info.set_seesion_status(session_id,session_val)
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
    br = bytearray(b'\x00'*10)
    print(br)
    b2_v = b'\x01\x01'
    br[2:4]=b2_v[:2]
    print(br)
    b2_v = b'\x02\x02'
    print(br)
    # testlog = LogHelper('testlog')
    # mbinfo = ModbusType(testlog, b'\x00\x01\x00\x00\x00\x06\xff\x04')
    # print('recv_seq:', disp_binary(mbinfo.recv_seq))
    # print('recv_pro_tag:', disp_binary(mbinfo.recv_pro_tag))
    # print('recv_cmd_len:', disp_binary(mbinfo.recv_msg_len))
    # print('recv_unit_tag:', disp_binary(mbinfo.recv_unit_tag))
    # print('send_msg_len:', disp_binary(mbinfo.send_msg_len))
    # mbinfo.send_msg_len = b'\x00\x08'
    # print('send_msg_len:', disp_binary(mbinfo.send_msg_len))
    # print('recv_cmd_len:', disp_binary(mbinfo.recv_msg_len))
