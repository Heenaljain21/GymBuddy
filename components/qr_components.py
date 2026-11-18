"""QR code generation and decoding for GYM BUDDY member passes."""

from __future__ import annotations
import base64
import io
from typing import Optional

import qrcode
import streamlit as st
from PIL import Image

from .ui import esc, html_block


def generate_qr_png(data: str, box_size: int = 10, border: int = 2) -> bytes:
    """Return a black-on-white QR code PNG (highest contrast for scanners)."""
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=box_size, border=border)
    qr.add_data(data)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    return buf.getvalue()


def render_member_pass(member_code: str, member_name: str, gym_name: str, footer: str = "Show this pass at the front desk to check in", key: str = "pass") -> None:
    png = generate_qr_png(member_code)
    b64 = base64.b64encode(png).decode()
    html_block(
        f"""
        <div class="gb-pass">
          <div class="gb-eyebrow">{esc(gym_name)}</div>
          <div class="gb-pass-name">{esc(member_name)}</div>
          <span class="gb-badge brand">{esc(member_code)}</span>
          <div><div class="gb-pass-qr"><img alt="QR code for {esc(member_code)}" src="data:image/png;base64,{b64}"></div></div>
          <div class="gb-pass-foot">{esc(footer)}</div>
        </div>
        """
    )
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        st.download_button(
            "Download pass", data=png, file_name=f"gymbuddy_pass_{member_code}.png", mime="image/png",
            icon=":material/download:", width="stretch", key=f"dl_{key}_{member_code}",
        )


def decode_qr_image(img_file) -> Optional[str]:
    """Decode a QR code from an uploaded/camera image using OpenCV (pyzbar as fallback)."""
    raw = img_file.getvalue() if hasattr(img_file, "getvalue") else img_file.read()
    try:
        import cv2
        import numpy as np
        img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            padded = cv2.copyMakeBorder(gray, 32, 32, 32, 32, cv2.BORDER_CONSTANT, value=255)
            detectors = []
            if hasattr(cv2, "QRCodeDetectorAruco"):
                detectors.append(cv2.QRCodeDetectorAruco())  # more robust, esp. on OpenCV 5
            detectors.append(cv2.QRCodeDetector())
            for detector in detectors:
                for candidate in (img, padded):
                    try:
                        data, _, _ = detector.detectAndDecode(candidate)
                    except cv2.error:
                        continue
                    if data:
                        return data.strip()
    except Exception:
        pass
    try:
        from pyzbar.pyzbar import decode
        decoded = decode(Image.open(io.BytesIO(raw)))
        if decoded:
            return decoded[0].data.decode("utf-8").strip()
    except Exception:
        pass
    return None
