# coding:utf-8
import configparser

config = configparser.ConfigParser()
config.read('config.ini',encoding='utf-8')
# print(config.get('DeviceConfig','dev_id'))


class SocketConfig:
    # 本地IP和端口
    server_addr = (config.get('SocketConfig','server_addr'), 502)#172.26.92.159
    # 下面的不用管
    recv_buff = 8192
    lister_num = int(config.get('SocketConfig','lister_num'))#2


class RegionConfig:
    # 分区子设备类型编号
    sub_dev_type = int(config.get('RegionConfig','sub_dev_type'))#3022
    # 起始分区名，真实名字为分区0001/分区0002
    region_name = config.get('RegionConfig','region_name')#'分区'
    # 音源状态寄存器默认值3bit
    vol_type_reg = 0b000
    # 故障状态寄存器默认值1bit
    ex_type_reg = 0b0
    # 紧急状态寄存器默认值1bit
    em_type_reg = 0b0
    # 优先级寄存器默认值1byte
    prio_reg = 0x15
    # 音量值寄存器默认值1byte
    vol_num_reg = 0x00
    # 每个分区的ID占用寄存器数目
    region_id_reg_num = 30
    # 每个分区的Name占用寄存器数目
    region_name_reg_num = 30
    # 每个分区的状态占用寄存器数目
    region_status_reg_num = 2


class DeviceConfig:
    # 设备ID
    dev_id = config.get('DeviceConfig','dev_id')#'10212019201988800001'
    # 设备型号10个字符以内
    dev_model = config.get('DeviceConfig','dev_model')#'ITC-7800A'
    # 设备软件版本30个字符内
    soft_version = config.get('DeviceConfig','soft_version')#'5.2'
    # 启用的分区数目最多64个
    region_count = int(config.get('DeviceConfig','region_count'))#2
    # region 设备基本配置，一般无需更改
    # 通信采用编码
    dev_encode = 'utf-16be'
    # 每个寄存器2字节
    dev_reg_size = 2
    # 设备最大分区数，目前为64
    max_region_count = 64
    # 每个分区的ID和名字分别占用30个寄存器
    region_reg_num = 30
    # 每个设备的会话数，默认为800
    session_num = 800
    # endregion
