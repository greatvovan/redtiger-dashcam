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


class PacketStruct(Struct):
    # freeGPS+0x20     0x00
    unknown_0 =  '<I', 0x08
    # YOUQINGGPS+0x0000000000000000000000000000 0x0c
    lat_raw =    '<f', 0x24
    lon_raw =    '<f', 0x28
    utc_hour =   '<I', 0x2c
    utc_minute = '<I', 0x30
    utc_second = '<I', 0x34
    utc_year =   '<I', 0x38
    utc_month =  '<I', 0x3c
    utc_day =    '<I', 0x40
    flags =      '3s', 0x44     # [Sat status][Lat direction][Lon direction]
    # 0x00             0x47
    unknown_1 =  '<d', 0x4c
    unknown_2 =  '<d', 0x54
    speed =      '<f', 0x5c
    bearing =    '<f', 0x60
    # 1234567890123456YSKJ 0x64
    gx =         '<i', 0x78
    gy =         '<i', 0x7c
    gz =         '<i', 0x80
    hour =       '<I', 0x84
    minute =     '<I', 0x88
    second =     '<I', 0x8c
    year =       '<I', 0x90
    month =      '<I', 0x94
    day =        '<I', 0x98


@dataclass
class Packet:
    offset: int
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
    unknown_0: int
    unknown_1: float
    unknown_2: float
