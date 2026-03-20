import sys
from pathlib import Path
from tqdm import tqdm
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

    export_tracks(videos_path, gpx_path)

def export_tracks(videos_path: Path, gpx_path: Path):
    trips = split_trips(videos_path)
    pbar = tqdm(trips)
    for trip in pbar:
        trip_start = timestamp_from_filename(trip[0].name)
        trip_end = timestamp_from_filename(trip[-1].name)
        pbar.set_description(f'Processing trip {trip_start.strftime('%H:%M')} – {trip_end.strftime('%H:%M')} from {trip_start.strftime('%b %-d')}')
        export_track(trip, gpx_path)

    print(f'{sum(len(trip) for trip in trips)} videos were combined into {len(trips)} trips')

def export_track(trip: list[Path], gpx_path: Path):
    trip_data = []
    pbar = tqdm(trip, leave=False)
    for item in pbar:
        pbar.set_description(item.name)
        trip_data += extract_telemetry_from_mp4(item)
    
    track_path = gpx_path / (trip[0].stem + '.gpx')
    save_to_gpx_track(trip_data, track_path)

def save_to_gpx_track(telemetry: list[Packet], save_path: Path):
    pass


if __name__ == '__main__':
    main()
