"""QR code generation and scanning components for GYM BUDDY.

Supports generating member QR codes, downloading PNGs, and scanning via
camera or image upload with manual member ID fallback.
"""

from __future__ import annotations
import io
import base64
from typing import Optional, Tuple
import qrcode
from PIL import Image
import streamlit as st


def generate_qr_code(data: str, box_size: int = 10, border: int = 2) -> Image.Image:
    """Generate a clean black/white QR code image for reliable scanner reading."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img


def render_member_qr(member_code: str, member_name: str, gym_name: str) -> None:
    """Display member QR card with download button and styling."""
    qr_img = generate_qr_code(member_code)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    b64 = base64.b64encode(byte_im).decode()

    st.markdown(
        f"""
        <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 20px; padding: 2rem; text-align: center; max-width: 380px; margin: 0 auto; box-shadow: 0 10px 30px rgba(139, 92, 246, 0.15);">
            <div style="font-size: 0.78rem; font-weight: 700; color: #06D6C9; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 0.25rem;">{gym_name}</div>
            <div style="font-family: 'Outfit', sans-serif; font-size: 1.4rem; font-weight: 800; color: #F8FAFC; margin-bottom: 0.2rem;">{member_name}</div>
            <div style="display: inline-block; background: rgba(139, 92, 246, 0.2); border: 1px solid #8B5CF6; border-radius: 8px; padding: 3px 12px; font-size: 0.85rem; font-weight: 700; color: #A78BFA; letter-spacing: 0.08em; margin-bottom: 1.25rem;">
                ID: {member_code}
            </div>
            <div style="background: #FFFFFF; padding: 16px; border-radius: 16px; display: inline-block; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                <img src="data:image/png;base64,{b64}" width="220" height="220" style="display: block;" />
            </div>
            <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 1rem;">Show this QR code at gym reception for check-in</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📥 Download Pass (QR Code)",
            data=byte_im,
            file_name=f"gymbuddy_pass_{member_code}.png",
            mime="image/png",
            use_container_width=True,
        )


def decode_qr_image(img_file) -> Optional[str]:
    """Decode a QR code from an uploaded image file using pyzbar or OpenCV."""
    try:
        from pyzbar.pyzbar import decode
        image = Image.open(img_file)
        decoded_objects = decode(image)
        if decoded_objects:
            return decoded_objects[0].data.decode("utf-8")
    except Exception:
        pass
    
    try:
        import cv2
        import numpy as np
        image_bytes = img_file.getvalue() if hasattr(img_file, "getvalue") else img_file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img_np)
        if data:
            return data
    except Exception:
        pass
    return None


def render_qr_scanner(key_prefix: str = "reception_qr") -> Optional[str]:
    """Render QR scanning interface with upload and manual fallback."""
    st.markdown(
        """
        <div style="font-family: 'Outfit', sans-serif; font-size: 1.05rem; font-weight: 700; color: #F8FAFC; margin-bottom: 0.5rem;">
            📸 Member Check-in Scanner
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    tabs = st.tabs(["📁 Upload QR Image", "⌨️ Manual Member ID", "📷 Live Camera"])
    
    with tabs[0]:
        uploaded_file = st.file_uploader(
            "Upload member QR pass",
            type=["png", "jpg", "jpeg"],
            key=f"{key_prefix}_file",
            help="Upload the QR code image from the member's phone or card",
        )
        if uploaded_file is not None:
            decoded = decode_qr_image(uploaded_file)
            if decoded:
                return decoded.strip()
            else:
                st.error("Could not detect a valid QR code in this image. Please enter Member ID manually.")
                
    with tabs[1]:
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            manual_id = st.text_input(
                "Enter Member ID or Code",
                placeholder="e.g. GMB-2026-001 or Phone number",
                key=f"{key_prefix}_manual",
            )
        with col_btn:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Check-in", key=f"{key_prefix}_manual_btn", use_container_width=True):
                if manual_id:
                    return manual_id.strip()

    with tabs[2]:
        cam_picture = st.camera_input("Scan Member QR with Camera", key=f"{key_prefix}_camera")
        if cam_picture is not None:
            decoded = decode_qr_image(cam_picture)
            if decoded:
                return decoded.strip()
            else:
                st.warning("QR Code not clear in frame. Try holding it steadier or use Image Upload.")

    return None
