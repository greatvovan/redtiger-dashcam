import struct
from datetime import datetime
from dataclasses import dataclass


class Struct:
    def __init__(self, buffer):
        # Overwrite class members with same-name instance members.
        for var, val in self.__class__.__dict__.items():
            if not var.startswith('__'):
                setattr(self, var, self.unpack(buffer, val))

    @staticmethod
    def unpack(buffer, field):
        return struct.unpack_from(field[0], buffer, field[1])[0]


class PacketStruct(Struct):
    # In descendant classes, only types and offsets are required.
    lat_raw = '<f', 0x24
    lon_raw = '<f', 0x28
    flags =   '3s', 0x44
    speed =   '<f', 0x5c
    bearing = '<f', 0x60
    gx =      '<i', 0x78
    gy =      '<i', 0x7c
    gz =      '<i', 0x80
    hour =    '<I', 0x84
    minute =  '<I', 0x88
    second =  '<I', 0x8c
    year =    '<I', 0x90
    month =   '<I', 0x94
    day =     '<I', 0x98


@dataclass
class Packet:
    offset: int
    timestamp: datetime
    latitude: float
    longitude: float
    speed: float
    bearing: float
    acceleration: tuple[int, int, int]
