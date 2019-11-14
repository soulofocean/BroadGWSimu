# coding:utf-8
from BasicConfig import RegionConfig, DeviceConfig
from CommonAPI import fomate_bytes, fomate_str,disp_binary


class RegionInfoType:
    """
    设备分区封装类
    """

    def __init__(self, dev_mac: str, region_index: int = 1):
        # 分区子设备类型编号
        self.sub_dev_type = RegionConfig.sub_dev_type
        # 子设备MAC，一般和主设备一致
        self.sub_dev_mac = dev_mac
        # 子设备编号
        self.sub_dev_num = region_index
        # 分区状态查询返回的二进制，每个分区2个寄存器
        reg_num_tmp = RegionConfig.region_status_reg_num
        self.__region_status_bytes = bytearray(reg_num_tmp * DeviceConfig.dev_reg_size)
        # 分区ID和名字查询返回的二进制，每个分区30个寄存器表示ID，30个寄存器表示Name
        reg_num_tmp = RegionConfig.region_id_reg_num + RegionConfig.region_name_reg_num
        self.__regin_id_name_bytes = bytearray(reg_num_tmp * DeviceConfig.dev_reg_size)
        # 音源状态寄存器3bit
        self.vol_type = RegionConfig.vol_type_reg
        # 故障状态寄存器1bit
        self.ex_status = RegionConfig.ex_type_reg
        # 紧急状态寄存器1bit
        self.em_status = RegionConfig.em_type_reg
        # 优先级寄存器1byte
        self.prio_info = RegionConfig.prio_reg
        # 音量值寄存器1byte
        self.vol_num = 0x00
        # 分区ID
        self.region_id_str = str(self.sub_dev_type) + self.sub_dev_mac + "{:04d}".format(self.sub_dev_num)[:4]
        # 分区名
        self.region_name_str = RegionConfig.region_name + "{:04d}".format(self.sub_dev_num)[:4]

    # region 查询分区ID和Name相关操作
    @property
    def region_id_str(self):
        return self.__regin_id_name_bytes[:60].decode(DeviceConfig.dev_encode)

    @region_id_str.setter
    def region_id_str(self, val):
        rid = val
        if isinstance(val, str):
            rid = fomate_str(val, RegionConfig.region_id_reg_num)
        size = RegionConfig.region_id_reg_num * DeviceConfig.dev_reg_size
        self.__regin_id_name_bytes[:60] = fomate_bytes(rid, size)

    @property
    def region_name_str(self):
        return self.__regin_id_name_bytes[60:].decode(DeviceConfig.dev_encode)

    @region_name_str.setter
    def region_name_str(self, val):
        rname = val
        if isinstance(val, str):
            rname = fomate_str(val, RegionConfig.region_name_reg_num)
        size = RegionConfig.region_name_reg_num * DeviceConfig.dev_reg_size
        self.__regin_id_name_bytes[60:] = fomate_bytes(rname, size)

    @property
    def region_basic_info_data(self):
        return self.__regin_id_name_bytes
    # endregion恢复


    # region 分区状态
    @property
    def em_status(self):
        """紧急状态，1 bit"""
        return self.__region_status_bytes[0] & 0x8


    @em_status.setter
    def em_status(self, val):
        """紧急状态，1 bit"""
        new_val = (val & 0x1) << 0x7
        self.__region_status_bytes[0] |= new_val


    @property
    def ex_status(self):
        """故障状态，1 bit"""
        return self.__region_status_bytes[0] & 0x40


    @ex_status.setter
    def ex_status(self, val):
        """紧急状态，1 bit"""
        new_val = (val & 0x1) << 0x6
        self.__region_status_bytes[0] |= new_val


    @property
    def vol_type(self):
        """音源类型，3 bits"""
        return self.__region_status_bytes[1] & 0x07


    @vol_type.setter
    def vol_type(self, val):
        new_val = val & 0x7
        self.__region_status_bytes[1] |= new_val


    @property
    def vol_num(self):
        """音量，8 bits"""
        return self.__region_status_bytes[2]


    @vol_num.setter
    def vol_num(self, val):
        self.__region_status_bytes[2] = val & 0xFF


    @property
    def prio_info(self):
        """优先级，8 bits"""
        return self.__region_status_bytes[3]


    @prio_info.setter
    def prio_info(self, val):
        self.__region_status_bytes[3] = val & 0xFF


    @property
    def region_status_data(self):
        """返回分区状态表 4 bytes"""
        return self.__region_status_bytes


# endregion


if __name__ == '__main__':
    a = RegionInfoType('201988800001', 2)
    print(a.region_status_data)
    print(a.vol_type)
    print(a.ex_status)
    print(a.em_status)
    print(a.prio_info)
    print(a.vol_num)
    print(disp_binary(a.region_status_data))
    a.vol_type = 0b110
    a.vol_num = 9
    a.ex_status = 1
    a.em_status = 1
    a.prio_info = 3
    print(a.vol_type)
    print(a.ex_status)
    print(a.em_status)
    print(a.prio_info)
    print(a.vol_num)
    print(disp_binary(a.region_status_data))
