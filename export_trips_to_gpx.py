import sys
from pathlib import Path
from tqdm import tqdm
from gpx import GPX, Metadata, Track, TrackSegment, Waypoint, Extensions
from redtiger.filesystem import split_trips, timestamp_from_filename
from redtiger.telemetry import Packet
from redtiger.parsing import extract_telemetry_from_mp4


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 1 and sys.argv[1] == '--help':
        print('Split video directory into trips and export their tracks in GPX format.')
        print(f'Usage: {Path(sys.argv[0]).name} <path/to/videos> <where/to/save/gpx>')
        print('Warning: if you have locked videos, they may be moved into different directory.')
        print('Combine them in a single directory before exporting to avoid having gaps in tracks.')
        exit(1)

    videos_path = Path(sys.argv[1])
    if not videos_path.exists():
        print('Path not found:', videos_path)

    gpx_path = Path(sys.argv[2])
    if not gpx_path.exists():
        print('Path not found:', gpx_path)

    process_path(videos_path, gpx_path)

def process_path(video_path: Path, gpx_path: Path):
    if video_path.is_file():
        trips = [[video_path]]  # In case of a file, produce a trivial, single-video trip.
    else:
        trips = split_trips(video_path)
        print(f'{sum(len(trip) for trip in trips)} videos were combined into {len(trips)} trips')

    pbar = tqdm(trips)
    for trip in pbar:
        pbar.set_description(f'Processing trip {get_trip_name(trip)}')
        process_trip(trip, gpx_path)

def process_trip(trip: list[Path], gpx_path: Path):
    trip_data = []
    pbar = tqdm(trip, leave=False)
    for item in pbar:
        pbar.set_description(item.name)
        trip_data += extract_telemetry_from_mp4(item)
    
    track_path = gpx_path / (trip[0].stem + '.gpx')
    save_to_gpx_track(trip_data, get_trip_name(trip), track_path)

def save_to_gpx_track(telemetry: list[Packet], trip_name, save_path: Path):
    import xml.etree.ElementTree as ET
    from datetime import datetime, UTC
    from gpx import Waypoint, Extensions

    REDTIGER_DASHCAM_TPX = "https://github.com/greatvovan/redtiger-dashcam/xmlschemas/TrackPointExtension/v1"
    ET.register_namespace("rd", REDTIGER_DASHCAM_TPX)

    points = []
    for t in telemetry:
        tpx = ET.Element(f"{{{REDTIGER_DASHCAM_TPX}}}TrackPointExtension")
        speed = ET.SubElement(tpx, f"{{{REDTIGER_DASHCAM_TPX}}}speed_kmh")
        speed.text = str(round(t.speed_kmh, 2))
        bearing = ET.SubElement(tpx, f"{{{REDTIGER_DASHCAM_TPX}}}bearing_deg")
        bearing.text = str(round(t.bearing, 2))
        nmea_status = ET.SubElement(tpx, f"{{{REDTIGER_DASHCAM_TPX}}}nmea_status")
        nmea_status.text = t.nmea_status
        gx = ET.SubElement(tpx, f"{{{REDTIGER_DASHCAM_TPX}}}gx")
        gx.text = str(t.gx)
        gy = ET.SubElement(tpx, f"{{{REDTIGER_DASHCAM_TPX}}}gy")
        gy.text = str(t.gy)
        gz = ET.SubElement(tpx, f"{{{REDTIGER_DASHCAM_TPX}}}gz")
        gz.text = str(t.gz)

        trkpt = Waypoint(
            lat=round(t.latitude, 6),
            lon=round(t.longitude, 6),
            time=t.utc_timestamp,
            ele=0.0,
            extensions=Extensions(elements=[tpx])
        )
        points.append(trkpt)

    segment = TrackSegment(trkpt=points)
    track = Track(trkseg=[segment])

    metadata = Metadata(
        name='Road trip ' + trip_name,
        desc='RedTiger dash camera GPS track',
        time=datetime.now(UTC),
    )

    gpx = GPX(
        creator="Redtiger-dashcam (home on GitHub)",
        metadata=metadata,
        trk=[track],
    )

    with open(save_path, 'wt') as file:
        file.write(gpx.to_string())

def get_trip_name(trip: list) -> str:
    trip_start = timestamp_from_filename(trip[0].name)
    trip_end = timestamp_from_filename(trip[-1].name)
    return f'{trip_start.strftime('%H:%M')} – {trip_end.strftime('%H:%M')} ' \
           f'from {trip_start.strftime('%b %-d')}'


if __name__ == '__main__':
    main()
