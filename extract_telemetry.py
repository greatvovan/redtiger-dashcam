import argparse
from pathlib import Path
from tqdm import tqdm
from redtiger.filesystem import split_trips, timestamp_from_filename
from redtiger.telemetry import Packet
from redtiger.parsing import extract_telemetry_from_mp4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Redtiger video telemetry extractor',
        epilog='Warning: if you have locked videos, they may be moved into a different directory '
               'on your SD card (such as "LOCK"). Combine them in a single directory before exporting '
               'to avoid having gaps in tracks.'
    )
    parser.add_argument('video_path', type=str, help='Path to video file or directory')
    parser.add_argument('save_path', type=str, help='Where to save extracted data (directory)')
    parser.add_argument('format', type=str, help='GPX or CSV')
    return parser

def process_path(video_path: Path, save_path: Path, format: str):
    if video_path.is_file():
        trips = [[video_path]]  # In case of a file, produce a trivial, single-video trip.
    else:
        trips = split_trips(video_path)
        print(f'{sum(len(trip) for trip in trips)} videos were combined into {len(trips)} trips')

    pbar = tqdm(trips)
    for trip in pbar:
        pbar.set_description(f'Processing trip {get_trip_name(trip)}')
        process_trip(trip, save_path, format)

def process_trip(trip: list[Path], save_path: Path, format: str):
    trip_data = []
    pbar = tqdm(trip, leave=False)
    for item in pbar:
        pbar.set_description(item.name)
        trip_data += extract_telemetry_from_mp4(item)
    
    if format == 'gpx':
        track_path = save_path / (trip[0].stem + '.gpx')
        save_to_gpx_track(trip_data, get_trip_name(trip), track_path)
    elif format == 'csv':
        track_path = save_path / (trip[0].stem + '.csv')
        save_to_csv(trip_data, track_path)

def save_to_gpx_track(telemetry: list[Packet], trip_name, save_path: Path):
    import xml.etree.ElementTree as ET
    from datetime import datetime, UTC
    from gpx import GPX, Metadata, Track, TrackSegment, Waypoint, Extensions

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

def save_to_csv(data, path):
    import csv
    from dataclasses import asdict

    with open(path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=asdict(data[0]).keys())
        writer.writeheader()
        writer.writerows(asdict(p) for p in data)

def get_trip_name(trip: list) -> str:
    trip_start = timestamp_from_filename(trip[0].name)
    trip_end = timestamp_from_filename(trip[-1].name)
    return f'{trip_start.strftime('%H:%M')} – {trip_end.strftime('%H:%M')} ' \
           f'from {trip_start.strftime('%b %-d')}'

def main():
    parser = build_parser()
    args = parser.parse_args()

    video_path = Path(args.video_path)
    if not video_path.exists():
        print('Path not found:', video_path)
        exit(1)

    save_path = Path(args.save_path)
    if not save_path.exists():
        print('Path not found:', save_path)
        exit(1)

    format = args.format.lower()
    if format not in ('csv', 'gpx'):
        print(f'Unknown save format: {format}. Use --help option.')
        exit(1)

    process_path(video_path, save_path, format)


if __name__ == '__main__':
    main()
