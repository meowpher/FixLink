"""
Interactive Map & Floor SVG Service for FixLink.
Provides zero-latency floor SVG delivery, digital twin caching, and room status mapping.
"""
import os
import logging
from flask import current_app
from app.cache import cache

logger = logging.getLogger(__name__)

# In-memory Floor Plan SVG cache for instantaneous zero-latency template rendering
_floor_svg_memory_cache = {}


def get_floor_svg(level, app=None):
    """
    Retrieve SVG floor plan markup for a given building level with in-memory caching.
    
    Args:
        level (int or str): Floor level (e.g. 0 to 7).
        app (Flask, optional): Current Flask application context.
        
    Returns:
        str: Raw SVG markup or empty string if not found.
    """
    lvl = str(level)
    if lvl in _floor_svg_memory_cache:
        return _floor_svg_memory_cache[lvl]

    root_path = app.root_path if app else current_app.root_path
    candidates = [
        os.path.join(root_path, 'static', 'images', 'floors', f'VY{lvl}.svg'),
        os.path.join(root_path, 'static', 'svg_maps', f'VY{lvl}.svg'),
    ]
    svg_content = ''
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                break
            except Exception as e:
                logger.warning(f"Error reading floor SVG from {path}: {e}")
                svg_content = ''

    _floor_svg_memory_cache[lvl] = svg_content
    return svg_content


def get_cached_floor_data(floor_id):
    """
    Fetch and cache room data for a floor to optimize rendering on both SSR and API.
    Uses eager loading for relationships to prevent N+1 query bottlenecks.
    """
    cache_key = f'map_floor_{floor_id}'
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    from sqlalchemy.orm import joinedload
    from app.models import Room, RoomBooking, Timetable, EventBooking

    rooms = Room.query.options(
        joinedload(Room.tickets),
        joinedload(Room.assets),
        joinedload(Room.room_bookings).joinedload(RoomBooking.faculty),
        joinedload(Room.timetables).joinedload(Timetable.faculty),
        joinedload(Room.booked_events).joinedload(EventBooking.faculty)
    ).filter_by(floor_id=floor_id).all()

    rooms_data = [room.to_map_dict() for room in rooms]
    cache.set(cache_key, rooms_data, timeout=3600)
    return rooms_data


def invalidate_floor_cache(floor_id):
    """Invalidate cached map data for a specific floor when tickets or status changes."""
    try:
        cache.delete(f'map_floor_{floor_id}')
        cache.delete(f'admin_floor_{floor_id}')
    except Exception as e:
        logger.warning(f"Failed to invalidate floor cache for floor {floor_id}: {e}")


def invalidate_all_map_cache():
    """Clear all cached map data."""
    try:
        cache.clear()
        _floor_svg_memory_cache.clear()
    except Exception as e:
        logger.warning(f"Failed to clear map cache: {e}")

