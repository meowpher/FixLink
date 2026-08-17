"""
Centralized Cache Module for FixLink.
Provides a shared cache instance and invalidation helpers.
"""
from flask_caching import Cache

cache = Cache()


import os

def init_cache(app):
    """Initialize the cache with the Flask app using FileSystemCache for serverless persistence."""
    # Vercel allows writing to /tmp which can persist across warm starts better than memory
    cache_dir = '/tmp/fixlink_cache' if os.environ.get('VERCEL') else os.path.join(app.root_path, '.cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_config = {
        'CACHE_TYPE': 'FileSystemCache',
        'CACHE_DIR': cache_dir,
        'CACHE_DEFAULT_TIMEOUT': 3600,  # 1 hour default
        'CACHE_THRESHOLD': 256,
    }
    app.config.from_mapping(cache_config)
    cache.init_app(app)
    return cache


def invalidate_floor_cache(floor_id):
    """Invalidate cached map data for a specific floor.
    Call this when a ticket is created/updated or an asset status changes.
    """
    # Keys match the patterns used in @cache.cached() decorators
    cache.delete(f'map_floor_{floor_id}')
    cache.delete(f'admin_floor_{floor_id}')


def invalidate_all_map_cache():
    """Nuclear option: clear all cached map data."""
    cache.clear()

def get_cached_floor_data(floor_id):
    """
    Fetch and cache room data for a floor to optimize rendering on both SSR and API.
    Uses eager loading for relationships to prevent N+1 query problems.
    """
    cache_key = f'map_floor_{floor_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return cached_data
        
    from sqlalchemy.orm import joinedload
    from .models import Room, RoomBooking, Timetable
    
    rooms = Room.query.options(
        joinedload(Room.tickets),
        joinedload(Room.assets),
        joinedload(Room.room_bookings).joinedload(RoomBooking.faculty),
        joinedload(Room.timetables).joinedload(Timetable.faculty)
    ).filter_by(floor_id=floor_id).all()
    
    rooms_data = [room.to_map_dict() for room in rooms]
    cache.set(cache_key, rooms_data, timeout=3600)  # Cache for 1 hour
    
    return rooms_data
