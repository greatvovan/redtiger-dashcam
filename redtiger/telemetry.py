import struct
from datetime import datetime
from dataclasses import dataclass


class Struct:
    """Parse the binary layout defined in descendant class."""
    def __init__(self, buffer):
        # Overwrite class members with same-name instance members.
        for var, val in self.__class__.__dict__.items():
            if not var.startswith('__'):
                setattr(self, var, self.unpack(buffer, val))

    @staticmethod
    def unpack(buffer, field):
        return struct.unpack_from(field[0], buffer, field[1])[0]
    
    @classmethod
    def length(cls) -> int:
        """Determine the size of payload parsable by the class"""
        right_max = 0
        for var, val in cls.__dict__.items():
            if not var.startswith('__'):
                field_right = val[1] + struct.calcsize(val[0])
                if right_max < field_right:
                    right_max = field_right
        return right_max


class PacketStruct(Struct):
    m_yg      = '10s', 0x00     # YOUQINGGPS
    # 0x0000000000000000000000000000 0x0a
    lat_raw =    '<f', 0x18
    lon_raw =    '<f', 0x1c
    utc_hour =   '<I', 0x20
    utc_minute = '<I', 0x24
    utc_second = '<I', 0x28
    utc_year =   '<I', 0x2c
    utc_month =  '<I', 0x30
    utc_day =    '<I', 0x34
    flags =      '3s', 0x38     # [Sat status][Lat direction][Lon direction]
    # 0x00             0x3b
    unknown =   '16s', 0x40
    speed =      '<f', 0x50
    bearing =    '<f', 0x54
    m_123 =     '20s', 0x58     # 1234567890123456YSKJ
    gx =         '<i', 0x6c
    gy =         '<i', 0x70
    gz =         '<i', 0x74
    hour =       '<I', 0x78
    minute =     '<I', 0x7c
    second =     '<I', 0x80
    year =       '<I', 0x84
    month =      '<I', 0x88
    day =        '<I', 0x8c


@dataclass
class Packet:
    timestamp: datetime
    utc_timestamp: datetime
    latitude: float
    longitude: float
    speed_kmh: float
    bearing: float
    nmea_status: str
    gx: int
    gy: int
    gz: int
    unknown: bytearray
