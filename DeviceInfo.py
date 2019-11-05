# coding:utf-8

from CommonAPI import fomate_bytes
from BasicConfig import DeviceConfig

class DeviceInfoType:
    """
    设备信息封装类
    """

    def __init__(self):
        self.dev_id = DeviceConfig.dev_id
        self.dev_model = DeviceConfig.dev_model
        self.sub_dev_type = DeviceConfig.sub_dev_type
        self.soft_version = DeviceConfig.soft_version
        self.region_name = DeviceConfig.region_name
        self.region_count = DeviceConfig.region_count
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
            ...
