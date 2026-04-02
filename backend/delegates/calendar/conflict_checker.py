"""Calendar conflict checking and slot finding utilities."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone, time as dt_time


# IST is UTC+5:30
_IST = timezone(timedelta(hours=5, minutes=30))


def find_available_slots(
    busy_periods: list[dict],  # [{start: datetime, end: datetime}]
    duration_minutes: int = 60,
    days_ahead: int = 14,
    working_hours: tuple[int, int] = (9, 18),  # 9am-6pm
    max_slots: int = 3,
) -> list[dict]:
    """
    Find available time slots avoiding busy periods and weekends.

    Parameters
    ----------
    busy_periods : list[dict]
        List of dicts with ``start`` and ``end`` datetime keys representing
        existing calendar commitments.
    duration_minutes : int
        Required slot duration in minutes.
    days_ahead : int
        Number of calendar days to search forward from tomorrow.
    working_hours : tuple[int, int]
        Start and end hour (inclusive, exclusive) in IST.
    max_slots : int
        Maximum number of slots to return.

    Returns
    -------
    list[dict]
        Each dict has ``start`` (datetime), ``end`` (datetime), and
        ``label`` (human-readable string like "Tuesday, Apr 8 at 10:00 AM").
    """
    if duration_minutes <= 0:
        return []

    work_start_hour, work_end_hour = working_hours
    duration = timedelta(minutes=duration_minutes)
    slots: list[dict] = []

    # Normalise busy periods to UTC-aware datetimes for comparison
    normalised_busy = _normalise_busy(busy_periods)

    # Start from tomorrow in IST
    now_ist = datetime.now(_IST)
    search_date = (now_ist + timedelta(days=1)).date()
    end_date = (now_ist + timedelta(days=days_ahead)).date()

    while search_date <= end_date and len(slots) < max_slots:
        # Skip weekends (Saturday=5, Sunday=6)
        if search_date.weekday() >= 5:
            search_date += timedelta(days=1)
            continue

        # Walk through the working-hours window in 30-min increments
        candidate_start = datetime.combine(
            search_date, dt_time(work_start_hour, 0), tzinfo=_IST
        )
        day_end = datetime.combine(
            search_date, dt_time(work_end_hour, 0), tzinfo=_IST
        )

        while candidate_start + duration <= day_end and len(slots) < max_slots:
            candidate_end = candidate_start + duration

            if not _has_conflict(candidate_start, candidate_end, normalised_busy):
                label = candidate_start.strftime("%A, %b %-d at %-I:%M %p") + " IST"
                slots.append(
                    {
                        "start": candidate_start,
                        "end": candidate_end,
                        "label": label,
                    }
                )
                # Jump past this slot to avoid overlapping proposals
                candidate_start = candidate_end
            else:
                candidate_start += timedelta(minutes=30)

        search_date += timedelta(days=1)

    return slots


def _normalise_busy(busy_periods: list[dict]) -> list[tuple[datetime, datetime]]:
    """
    Convert busy period dicts to a sorted list of (start, end) tuples
    with timezone-aware datetimes.
    """
    result: list[tuple[datetime, datetime]] = []
    for period in busy_periods:
        start = period.get("start")
        end = period.get("end")
        if start is None or end is None:
            continue

        # Ensure timezone awareness
        if isinstance(start, datetime) and start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if isinstance(end, datetime) and end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        result.append((start, end))

    result.sort(key=lambda x: x[0])
    return result


def _has_conflict(
    start: datetime,
    end: datetime,
    busy: list[tuple[datetime, datetime]],
) -> bool:
    """Return True if the proposed [start, end) overlaps any busy period."""
    for busy_start, busy_end in busy:
        # Two intervals overlap if one starts before the other ends
        if start < busy_end and end > busy_start:
            return True
    return False
