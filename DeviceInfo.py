# coding:utf-8

from CommonAPI import fomate_bytes, fomate_str
from BasicConfig import DeviceConfig, RegionConfig
import typing


class RegionInfoType:
    """
    设备分区封装类
    """

    def __init__(self, dev_mac: str, offset: int = 1):
        # 分区子设备类型编号
        self.sub_dev_type = RegionConfig.sub_dev_type
        # 子设备MAC，一般和主设备一致
        self.sub_dev_mac = dev_mac
        # 子设备编号
        self.sub_dev_num = offset
        # 音源状态寄存器3bit
        self.vol_type_reg = RegionConfig.vol_type_reg
        # 故障状态寄存器1bit
        self.ex_type_reg = RegionConfig.ex_type_reg
        # 紧急状态寄存器1bit
        self.em_type_reg = RegionConfig.em_type_reg
        # 优先级寄存器1byte
        self.prio_reg = RegionConfig.prio_reg
        # 音量值寄存器1byte
        self.vol_num_reg = 0x00
        # 分区ID
        self.region_id = str(self.sub_dev_type) + self.sub_dev_mac + "{:04d}".format(self.sub_dev_num)[:4]
        # 分区名
        self.region_name = RegionConfig.region_name + "{:04d}".format(self.sub_dev_num)[:4]


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
        self.init_region_info_list()

    def init_region_info_list(self):
        if self.region_count and self.dev_id:
            if self.region_count > self.max_region_count:
                self.region_count = self.max_region_count
            for i in range(self.region_count):
                region = RegionInfoType(dev_mac=self.dev_id[8:20], offset=i + 1)
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
                    new_dev_id = fomate_str(region.region_id, self.region_reg_num)
                    tmp_br.extend(
                        fomate_bytes(new_dev_id, self.region_reg_num * self.reg_size, encoding=self.dev_encode))
                    new_region_name = fomate_str(region.region_name, self.region_reg_num)
                    tmp_br.extend(
                        fomate_bytes(new_region_name, self.region_reg_num * self.reg_size, encoding=self.dev_encode))
            self.region_id_name_bytes = bytes(tmp_br)

    def get_region_status_bytes(self):
        """
        获取分区状态bytes
        :return:分区状态的bytes
        """
        tmp_br = bytearray()
        if self.region_list:
            for region in self.region_list:
                tmp_int = 0
                if region.em_type_reg:
                    tmp_int += region.em_type_reg << 7
                if region.ex_type_reg:
                    tmp_int += region.ex_type_reg << 6
                # 添加第一个寄存器的8到15bit
                tmp_br.append(tmp_int)
                # 添加第一个寄存器的0到7bit,其中0-2bit是音源类型，其余bit是0
                tmp_br.append(region.vol_type_reg)
                # 添加第二个寄存器的8-15bit,表示音量，范围0-100，和研发确认文档0-19描述有误
                tmp_br.append(region.vol_num_reg)
                # 添加第二个寄存器的0-7bit,表示优先级
                tmp_br.append(region.prio_reg)
        return bytes(tmp_br)
