# coding:utf-8

from CommonAPI import fomate_bytes, fomate_str
from BasicConfig import DeviceConfig, RegionConfig
import typing
import struct
from RegionInfo import  RegionInfoType




class DeviceInfoType:
    """
    设备信息封装类
    """

    def __init__(self):
        self.dev_id = DeviceConfig.dev_id
        self.dev_model = DeviceConfig.dev_model
        self.soft_version = DeviceConfig.soft_version
        self.region_count = DeviceConfig.region_count
        self.region_list: typing.List[RegionInfoType] = list()
        self.region_id_name_bytes = b''
        # 最多64个分区
        self.max_region_count = DeviceConfig.max_region_count
        # 每个分区的ID和名字分别占用30个寄存器
        self.region_reg_num = DeviceConfig.region_reg_num
        # 每个寄存器占用的字节数
        self.reg_size = DeviceConfig.dev_reg_size
        # 编码方式
        self.dev_encode = DeviceConfig.dev_encode
        # 设备会话列表
        self.session_status_bytes = bytearray(b'\x00\x00' * DeviceConfig.session_num)
        self.init_region_info_list()

    def set_seesion_status(self, session_num: bytes, status_val: bytes):
        session_num_int = struct.unpack('>H',session_num)[0]
        if session_num_int > 200 or session_num_int < 1:
            raise IndexError('session_num {} invalid [1-200]!'.format(session_num_int))
        start_index = (session_num_int - 1) * 2
        self.session_status_bytes[start_index:start_index + 2] = status_val[:2]

    def init_region_info_list(self):
        if self.region_count and self.dev_id:
            if self.region_count > self.max_region_count:
                self.region_count = self.max_region_count
            for i in range(self.region_count):
                region = RegionInfoType(dev_mac=self.dev_id[8:20], region_index=i + 1)
                self.region_list.append(region)

    def get_region_info_bytes(self):
        """
        获取分区表的bytes存放在self.region_bytes中
        :return: None
        """
        if not self.region_id_name_bytes:
            tmp_br = bytearray()
            if self.region_list:
                for region in self.region_list:
                    tmp_br.extend(region.region_basic_info_data)
                    # new_dev_id = fomate_str(region.region_id, self.region_reg_num)
                    # tmp_br.extend(
                    #     fomate_bytes(new_dev_id, self.region_reg_num * self.reg_size, encoding=self.dev_encode))
                    # new_region_name = fomate_str(region.region_name, self.region_reg_num)
                    # tmp_br.extend(
                    #     fomate_bytes(new_region_name, self.region_reg_num * self.reg_size, encoding=self.dev_encode))
            self.region_id_name_bytes = bytes(tmp_br)

    def get_region_status_bytes(self):
        """
        获取分区状态bytes
        :return:分区状态的bytes
        """
        tmp_br = bytearray()
        if self.region_list:
            for region in self.region_list:
                tmp_br.extend(region.region_status_data)
                # tmp_int = 0
                # if region.em_type_reg:
                #     tmp_int += region.em_type_reg << 7
                # if region.ex_type_reg:
                #     tmp_int += region.ex_type_reg << 6
                # # 添加第一个寄存器的8到15bit
                # tmp_br.append(tmp_int)
                # # 添加第一个寄存器的0到7bit,其中0-2bit是音源类型，其余bit是0
                # tmp_br.append(region.vol_type_reg)
                # # 添加第二个寄存器的8-15bit,表示音量，范围0-100，和研发确认文档0-19描述有误
                # tmp_br.append(region.vol_num_reg)
                # # 添加第二个寄存器的0-7bit,表示优先级
                # tmp_br.append(region.prio_reg)
        return bytes(tmp_br)
