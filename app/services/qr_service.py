"""
QR Generation Service for FixLink Smart-Room Maintenance Tracker.
Provides unified QR code generation for rooms, assets, and reporting URLs.
"""
import os
import io
import qrcode
from PIL import Image

DEFAULT_BASE_URL = os.environ.get("APP_BASE_URL", "https://fixlink26.vercel.app")


def get_room_report_url(room_number, base_url=None):
    """Generate the public issue reporting URL for a given room number."""
    base = (base_url or DEFAULT_BASE_URL).rstrip("/")
    return f"{base}/report?room={room_number}"


def generate_qr_code(data, box_size=10, border=2, fill_color="#000000", back_color="#FFFFFF"):
    """
    Generate a QR code image as a PIL Image object.
    
    Args:
        data (str): URL or text to encode.
        box_size (int): Size of each box/pixel.
        border (int): Border box padding.
        fill_color (str): QR code foreground color.
        back_color (str): QR code background color.
        
    Returns:
        PIL.Image: Generated QR code image.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color=fill_color, back_color=back_color)


def generate_qr_bytes(data, format="PNG", **kwargs):
    """Generate QR code and return raw byte buffer."""
    img = generate_qr_code(data, **kwargs)
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return buffer.getvalue()


def save_room_qr_code(room_number, output_dir=None, base_url=None):
    """
    Generate and save a room QR code PNG to disk.
    
    Returns:
        str: Absolute file path of the saved QR code.
    """
    if not output_dir:
        # Default to app/static/qr_codes
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "static", "qr_codes")
    os.makedirs(output_dir, exist_ok=True)
    
    url = get_room_report_url(room_number, base_url)
    img = generate_qr_code(url)
    filename = f"Vyas_{room_number}_QR.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath, "PNG")
    return filepath

