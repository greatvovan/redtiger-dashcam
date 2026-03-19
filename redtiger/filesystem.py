from pathlib import Path
from datetime import datetime, timedelta


def split_trips(dir) -> list[list[Path]]:
    """
    Returns a list of file groups representing a "trip",
    defined as non-interrupted recording session.
    Going in alphanumeric order from the earliest files,
    based on the naming pattern 20260312190947_000504A.MP4,
    we check if the comsecutive files differ by exact number of minutes (within limit).
    As long as this condition is fulfilled, we accumulate the group.
    When a gap is met, the group is "closed" and a new group begins.
    """
    groups = []

    dir_path = Path(dir)
    files = sorted(f for f in dir_path.glob('*.MP4') if not f.name.startswith('._'))
    total = len(files)
    if total == 0:
        return groups
    
    def is_in_trip_delta(ts1: datetime, ts2: datetime):
        """Defines the condition to assume adjacent videos are from the same trip"""
        delta = ts2 - ts1
        minutes = delta.seconds // 60
        seconds = delta.seconds % 60
        return seconds == 0 and minutes < 10
    
    current_group = []
    groups.append(current_group)
    previous_item = files[0]
    current_group.append(previous_item)
    previous_ts = timestamp_from_filename(previous_item.name)

    i = 1
    while i < total:
        current_item = files[i]
        current_ts = timestamp_from_filename(current_item.name)
        if not is_in_trip_delta(previous_ts, current_ts):
            # Start new group
            current_group = []
            groups.append(current_group)
        current_group.append(current_item)
        previous_ts = current_ts
        i += 1
    
    return groups

def timestamp_from_filename(filename: str) -> datetime:
    return datetime.strptime(filename[:14], '%Y%m%d%H%M%S')
