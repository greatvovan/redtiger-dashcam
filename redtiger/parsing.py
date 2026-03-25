import mmap
import struct
from datetime import datetime, UTC
from redtiger.telemetry import Packet, PacketStruct

try:
    from tqdm import tqdm
    _TQDM = True
except ImportError:
    _TQDM = False


def ddmm_to_decimal(x):
    deg = round(x / 100)
    minutes = x - deg * 100
    dec = deg + minutes / 60
    return dec


def parse_mp4_boxes(mm):
    """Yield (type, start, size) for top-level MP4 boxes."""
    pos = 0
    size = len(mm)

    while pos < size:
        if pos + 8 > size:
            break

        box_size = struct.unpack_from('>I', mm, pos)[0]
        box_type = mm[pos+4:pos+8]

        if box_size == 0:
            box_size = size - pos
        elif box_size == 1:
            # 64-bit extended size
            box_size = struct.unpack_from('>Q', mm, pos+8)[0]
            header = 16
        else:
            header = 8

        yield box_type, pos, box_size

        pos += box_size


def parse_gps_packet(mm, pos):
    """Parse telemetry packet at given offset."""
    try:
        # Structure: [GPS ][len32][packet]
        plen = struct.unpack_from('<I', mm, pos+4)[0]
        ppos = pos + 4 + 4

        if plen != PacketStruct.length():
            raise ValueError('Unsupported packet size')

        mv = memoryview(mm)[ppos:ppos+plen]
        ps = PacketStruct(mv)

        # Check magic markers
        if ps.m_yg != b'YOUQINGGPS' or ps.m_123 != b'1234567890123456YSKJ':
            raise ValueError('Unexpected packet structure')

        ns = ps.flags[1:2].decode()
        ew = ps.flags[2:3].decode()
        lat = ddmm_to_decimal(ps.lat_raw)
        lon = ddmm_to_decimal(ps.lon_raw)
        if ns == 'S':
            lat = -lat
        if ew == 'W':
            lon = -lon

        NAUT_MILE_KM = 1.852
        CENTURY = 2000

        timestamp = datetime(ps.year, ps.month, ps.day,
                             ps.hour, ps.minute, ps.second)
        utc_timestamp = datetime(CENTURY + ps.utc_year, ps.utc_month, ps.utc_day,
                                 ps.utc_hour, ps.utc_minute, ps.utc_second, tzinfo=UTC)

        return Packet(
            timestamp=timestamp,
            utc_timestamp=utc_timestamp,
            latitude=lat,
            longitude=lon,
            speed_kmh=ps.speed * NAUT_MILE_KM,
            bearing=ps.bearing,
            nmea_status=ps.flags[0:1].decode(),
            gx=ps.gx,
            gy=ps.gy,
            gz=ps.gz,
            unknown=ps.unknown.hex(),
        )

    except Exception:
        return None


def extract_telemetry_from_mp4(filename):
    results = []

    with open(filename, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        # 1. Find mdat box
        mdat_ranges = []
        for box_type, pos, size in parse_mp4_boxes(mm):
            if box_type == b'mdat':
                mdat_ranges.append((pos, size))

        # fallback: if no mdat found, scan whole file
        if not mdat_ranges:
            mdat_ranges = [(0, len(mm))]

        # 2. Scan inside mdat only
        # This is not a proper parsing algorithm.
        # The binary data suggests that 'free' block is organized in a similar
        # fashion as MP4 'free' box, but it is not it (in fact, we skip proper
        # 'free' boxes above). Below 'free' is a 16kB block beginning with 'GPS '
        # marker, hence we a searching for:
        marker = b'freeGPS '

        if _TQDM:
            pbar = tqdm(desc='Bytes processed', total=size, unit='B', leave=False)

        for start, size in mdat_ranges:
            end = start + size
            pos = start

            while True:
                pos = mm.find(marker, pos, end)
                if pos == -1:
                    break

                if _TQDM:
                    pbar.n = pos
                    pbar.refresh()

                rec = parse_gps_packet(mm, pos + 4)   # account for 'free'
                if rec:
                    results.append(rec)

                pos += 1

        mm.close()

    return results
