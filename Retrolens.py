"""
Retro Lens - Real-time Hand & Face Gesture Filter Pipeline
Powered by Faisaldev
"""

from dataclasses import dataclass
import random
import time
from typing import Dict, List, Tuple, Callable, Optional

import cv2
import mediapipe as mp
import numpy as np


# ══════════════════════════════════════════════════════════════════════════════
# WATERMARK & PRICING SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

WATERMARK_TEXT   = "Powered by Faisaldev"
PRICING_PLANS    = [
    {"label": "Pro",     "price": 74_900,       "desc": "Hilangkan watermark + semua filter"},
    {"label": "Max",     "price": 2_500_000,    "desc": "Akses seumur hidup + source code"},
]


class WatermarkUI:
    def __init__(self, frame_w: int, frame_h: int):
        self.fw = frame_w
        self.fh = frame_h
        self.show_modal   = False
        self.toast_msg    = ""
        self.toast_until  = 0.0
        self.selected_plan: Optional[int] = None

        self.wm_font       = cv2.FONT_HERSHEY_SIMPLEX
        self.wm_scale      = 0.52
        self.wm_thick      = 1
        (tw, th), _ = cv2.getTextSize(WATERMARK_TEXT, self.wm_font, self.wm_scale, self.wm_thick)
        pad = 6
        self.wm_x  = frame_w - tw - 36 - pad * 2 - 4
        self.wm_y  = frame_h - 12
        btn_size   = 18
        self.x_rect = (
            frame_w - btn_size - 4,
            frame_h - btn_size - 4,
            frame_w - 4,
            frame_h - 4,
        )

        self.modal_w = 420
        self.modal_h = 260
        self.modal_x = (frame_w - self.modal_w) // 2
        self.modal_y = (frame_h - self.modal_h) // 2
        self.beli_rects: List[Tuple[int,int,int,int]] = []

    def handle_click(self, mx: int, my: int) -> None:
        if self.show_modal:
            self._handle_modal_click(mx, my)
        else:
            self._handle_watermark_click(mx, my)

    def draw(self, frame: np.ndarray) -> np.ndarray:
        self._draw_watermark(frame)
        if self.show_modal:
            self._draw_modal(frame)
        self._draw_toast(frame)
        return frame

    def _draw_watermark(self, frame: np.ndarray) -> None:
        x1, y1, x2, y2 = self.x_rect
        overlay = frame.copy()
        cv2.rectangle(overlay,
                       (self.wm_x - 6, self.fh - 26),
                       (self.fw - 2,   self.fh - 2),
                       (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)
        cv2.putText(frame, WATERMARK_TEXT,
                    (self.wm_x, self.wm_y),
                    self.wm_font, self.wm_scale,
                    (255, 215, 0), self.wm_thick, cv2.LINE_AA)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (60, 60, 60), -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (180, 180, 180), 1)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        cv2.line(frame, (cx-4, cy-4), (cx+4, cy+4), (255, 80, 80), 2)
        cv2.line(frame, (cx+4, cy-4), (cx-4, cy+4), (255, 80, 80), 2)

    def _handle_watermark_click(self, mx: int, my: int) -> None:
        x1, y1, x2, y2 = self.x_rect
        if x1 <= mx <= x2 and y1 <= my <= y2:
            self.show_modal = True
            self.beli_rects = []

    def _draw_modal(self, frame: np.ndarray) -> None:
        mx, my = self.modal_x, self.modal_y
        mw, mh = self.modal_w, self.modal_h
        self.beli_rects = []
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.fw, self.fh), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
        cv2.rectangle(frame, (mx, my), (mx+mw, my+mh), (28, 28, 35), -1)
        cv2.rectangle(frame, (mx, my), (mx+mw, my+mh), (80, 80, 100), 2)
        cv2.putText(frame, "Hapus Watermark",
                    (mx+18, my+34), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                    (255, 215, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, "Pilih paket untuk melanjutkan:",
                    (mx+18, my+58), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (180, 180, 180), 1, cv2.LINE_AA)
        cv2.line(frame, (mx+12, my+68), (mx+mw-12, my+68), (70, 70, 90), 1)
        for i, plan in enumerate(PRICING_PLANS):
            row_y = my + 88 + i * 72
            is_sel = (self.selected_plan == i)
            border_col = (0, 200, 120) if is_sel else (70, 70, 90)
            cv2.rectangle(frame, (mx+14, row_y), (mx+mw-14, row_y+54), (38, 38, 48), -1)
            cv2.rectangle(frame, (mx+14, row_y), (mx+mw-14, row_y+54), border_col, 1)
            cv2.putText(frame, f"  {plan['label']}  —  Rp {plan['price']:,}".replace(",", "."),
                        (mx+22, row_y+22), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                        (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"  {plan['desc']}",
                        (mx+22, row_y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                        (150, 150, 150), 1, cv2.LINE_AA)
            bx1 = mx + mw - 82
            bx2 = mx + mw - 18
            by1 = row_y + 12
            by2 = row_y + 38
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 160, 80), -1)
            cv2.putText(frame, "Beli",
                        (bx1+14, by2-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255, 255, 255), 1, cv2.LINE_AA)
            self.beli_rects.append((bx1, by1, bx2, by2))
        cv2.putText(frame, "[ ESC ] Tutup",
                    (mx + mw - 100, my + mh - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36,
                    (100, 100, 100), 1, cv2.LINE_AA)

    def _handle_modal_click(self, mx: int, my: int) -> None:
        for i, (bx1, by1, bx2, by2) in enumerate(self.beli_rects):
            if bx1 <= mx <= bx2 and by1 <= my <= by2:
                self.selected_plan = i
                plan = PRICING_PLANS[i]
                self._show_toast(
                    f"Gagal! Saldo anda kurang  (butuh Rp {plan['price']:,})".replace(",", ".")
                )
                return
        cx1, cy1 = self.modal_x, self.modal_y
        cx2, cy2 = cx1 + self.modal_w, cy1 + self.modal_h
        if not (cx1 <= mx <= cx2 and cy1 <= my <= cy2):
            self.show_modal = False

    def _show_toast(self, msg: str, duration: float = 2.8) -> None:
        self.toast_msg   = msg
        self.toast_until = time.time() + duration

    def _draw_toast(self, frame: np.ndarray) -> None:
        if not self.toast_msg or time.time() > self.toast_until:
            self.toast_msg = ""
            return
        (tw, th), _ = cv2.getTextSize(self.toast_msg, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        tx = (self.fw - tw) // 2
        ty = self.fh - 55
        overlay = frame.copy()
        cv2.rectangle(overlay, (tx-14, ty-22), (tx+tw+14, ty+10), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        cv2.putText(frame, self.toast_msg,
                    (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (80, 80, 255), 1, cv2.LINE_AA)


# ══════════════════════════════════════════════════════════════════════════════
# PHOTO CAPTURE + THUMBNAIL HUD
# ══════════════════════════════════════════════════════════════════════════════

class PhotoCapture:
    """
    - Tombol kamera (CENTER-BOTTOM HUD):  klik → simpan foto + prank popup
    - Thumbnail (kiri tombol kamera)    : klik → preview fullscreen
    - Fullscreen preview ada tombol [X] (tutup) dan [⬇ Download]
    """

    BTN_SIZE  = 48   # ukuran tombol kamera
    THUMB_W   = 64
    THUMB_H   = 48
    THUMB_GAP = 10   # jarak thumbnail ke tombol kamera

    def __init__(self, fw: int, fh: int):
        self.fw = fw
        self.fh = fh

        # Posisi tombol kamera (center-bottom)
        self.btn_cx = fw // 2
        self.btn_cy = fh - self.BTN_SIZE // 2 - 12
        bs = self.BTN_SIZE // 2
        self.btn_rect = (self.btn_cx - bs, self.btn_cy - bs,
                         self.btn_cx + bs, self.btn_cy + bs)

        # Posisi thumbnail (kiri tombol)
        tx2 = self.btn_rect[0] - self.THUMB_GAP
        tx1 = tx2 - self.THUMB_W
        ty1 = self.btn_cy - self.THUMB_H // 2
        ty2 = ty1 + self.THUMB_H
        self.thumb_rect = (tx1, ty1, tx2, ty2)

        # State
        self.last_photo: Optional[np.ndarray] = None   # full-res
        self.thumb_img:  Optional[np.ndarray] = None   # kecil
        self.show_preview = False
        self.last_filename = ""

        # Prank toast
        self.prank_msg   = ""
        self.prank_until = 0.0

        # Preview close & download button rects (diisi saat draw)
        self.prev_close_rect    = (0, 0, 0, 0)
        self.prev_download_rect = (0, 0, 0, 0)

    # ── public ────────────────────────────────────────────────────────────────

    def trigger_capture(self, frame: np.ndarray) -> None:
        ts = int(time.time())
        fn = f"photo_{ts}.png"
        cv2.imwrite(fn, frame)
        self.last_photo    = frame.copy()
        self.last_filename = fn
        self.thumb_img     = cv2.resize(frame, (self.THUMB_W, self.THUMB_H))
        self.prank_msg   = f"Foto disimpan: {fn}"
        self.prank_until = time.time() + 2.5
        print(f"[SNAP] Foto disimpan: {fn}")

    def handle_click(self, mx: int, my: int) -> bool:
        """
        Return True jika klik mengenai tombol kamera.
        Juga handle klik thumbnail & preview.
        """
        if self.show_preview:
            return self._handle_preview_click(mx, my)

        # Klik tombol kamera
        x1, y1, x2, y2 = self.btn_rect
        if x1 <= mx <= x2 and y1 <= my <= y2:
            return True   # sinyal ke luar supaya trigger_capture dipanggil dengan frame

        # Klik thumbnail
        if self.thumb_img is not None:
            tx1, ty1, tx2, ty2 = self.thumb_rect
            if tx1 <= mx <= tx2 and ty1 <= my <= ty2:
                self.show_preview = True
        return False

    def draw(self, frame: np.ndarray) -> np.ndarray:
        """Gambar tombol kamera, thumbnail, preview, dan prank toast."""
        if self.show_preview and self.last_photo is not None:
            self._draw_preview(frame)
        else:
            self._draw_camera_btn(frame)
            self._draw_thumbnail(frame)
        self._draw_prank(frame)
        return frame

    # ── kamera button ─────────────────────────────────────────────────────────

    def _draw_camera_btn(self, frame: np.ndarray) -> None:
        x1, y1, x2, y2 = self.btn_rect
        cx, cy = self.btn_cx, self.btn_cy

        # Background lingkaran
        cv2.circle(frame, (cx, cy), self.BTN_SIZE // 2, (40, 40, 40), -1)
        cv2.circle(frame, (cx, cy), self.BTN_SIZE // 2, (200, 200, 200), 2)

        # Ikon kamera — body
        bw, bh = 26, 18
        bx1 = cx - bw // 2
        by1 = cy - bh // 2
        bx2 = bx1 + bw
        by2 = by1 + bh
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (220, 220, 220), -1)
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (80, 80, 80), 1)

        # Tonjolan atas (viewfinder bump)
        cv2.rectangle(frame, (cx-6, by1-5), (cx+6, by1), (220, 220, 220), -1)

        # Lensa
        cv2.circle(frame, (cx, cy), 6, (60, 60, 60), -1)
        cv2.circle(frame, (cx, cy), 6, (180, 180, 180), 1)
        cv2.circle(frame, (cx-2, cy-2), 2, (255, 255, 255), -1)   # kilap

        # Flash dot kiri atas
        cv2.circle(frame, (bx1+4, by1+4), 2, (255, 220, 50), -1)

    # ── thumbnail ─────────────────────────────────────────────────────────────

    def _draw_thumbnail(self, frame: np.ndarray) -> None:
        tx1, ty1, tx2, ty2 = self.thumb_rect
        if self.thumb_img is not None:
            frame[ty1:ty2, tx1:tx2] = self.thumb_img
            cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), (0, 220, 255), 1)
            # Label kecil
            cv2.putText(frame, "TAP", (tx1+2, ty2-3),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.28, (0, 220, 255), 1, cv2.LINE_AA)
        else:
            # Placeholder kosong
            cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), (60, 60, 60), -1)
            cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), (100, 100, 100), 1)
            cv2.putText(frame, "?", (tx1 + self.THUMB_W//2 - 5, ty1 + self.THUMB_H//2 + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)

    # ── preview fullscreen ────────────────────────────────────────────────────

    def _draw_preview(self, frame: np.ndarray) -> None:
        fw, fh = self.fw, self.fh

        # Overlay gelap
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (fw, fh), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Foto di tengah
        ph = int(fh * 0.75)
        pw = int(ph * fw / fh)
        px = (fw - pw) // 2
        py = (fh - ph) // 2
        resized = cv2.resize(self.last_photo, (pw, ph))
        frame[py:py+ph, px:px+pw] = resized
        cv2.rectangle(frame, (px, py), (px+pw, py+ph), (0, 220, 255), 2)

        # ── Tombol [X] Tutup ──────────────────────────────────────────────────
        cx1, cy1 = px + pw - 36, py + 8
        cx2, cy2 = px + pw - 8, py + 36
        cv2.rectangle(frame, (cx1, cy1), (cx2, cy2), (60, 40, 40), -1)
        cv2.rectangle(frame, (cx1, cy1), (cx2, cy2), (200, 80, 80), 1)
        ccx, ccy = (cx1+cx2)//2, (cy1+cy2)//2
        cv2.line(frame, (ccx-6, ccy-6), (ccx+6, ccy+6), (255, 80, 80), 2)
        cv2.line(frame, (ccx+6, ccy-6), (ccx-6, ccy+6), (255, 80, 80), 2)
        self.prev_close_rect = (cx1, cy1, cx2, cy2)

        # ── Tombol [⬇ Download] ───────────────────────────────────────────────
        dw, dh = 130, 32
        dx1 = (fw - dw) // 2
        dy1 = py + ph + 12
        dx2 = dx1 + dw
        dy2 = dy1 + dh
        cv2.rectangle(frame, (dx1, dy1), (dx2, dy2), (0, 140, 60), -1)
        cv2.rectangle(frame, (dx1, dy1), (dx2, dy2), (0, 220, 100), 1)
        cv2.putText(frame, "Simpan / Download", (dx1+6, dy2-9),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
        self.prev_download_rect = (dx1, dy1, dx2, dy2)

        # Nama file
        cv2.putText(frame, self.last_filename, (px, py - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (160, 160, 160), 1, cv2.LINE_AA)

    def _handle_preview_click(self, mx: int, my: int) -> bool:
        # Tutup
        cx1, cy1, cx2, cy2 = self.prev_close_rect
        if cx1 <= mx <= cx2 and cy1 <= my <= cy2:
            self.show_preview = False
            return False

        # Download — buka file manager / copy path (OpenCV tidak bisa open dialog,
        # jadi kita cetak path ke console dan tambahkan toast)
        dx1, dy1, dx2, dy2 = self.prev_download_rect
        if dx1 <= mx <= dx2 and dy1 <= my <= dy2:
            import os
            abs_path = os.path.abspath(self.last_filename)
            print(f"[DOWNLOAD] File tersimpan di: {abs_path}")
            self.prank_msg   = f"Disimpan: {self.last_filename}"
            self.prank_until = time.time() + 2.5
            return False
        return False

    # ── prank toast ───────────────────────────────────────────────────────────

    def _draw_prank(self, frame: np.ndarray) -> None:
        if not self.prank_msg or time.time() > self.prank_until:
            self.prank_msg = ""
            return
        font  = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.52; thick = 1
        (tw, _), _ = cv2.getTextSize(self.prank_msg, font, scale, thick)
        tx = (self.fw - tw) // 2
        ty = self.fh - 70
        ovl = frame.copy()
        cv2.rectangle(ovl, (tx-14, ty-20), (tx+tw+14, ty+8), (15, 15, 15), -1)
        cv2.addWeighted(ovl, 0.75, frame, 0.25, 0, frame)
        cv2.rectangle(frame, (tx-14, ty-20), (tx+tw+14, ty+8), (0, 200, 120), 1)
        cv2.putText(frame, self.prank_msg, (tx, ty), font, scale, (0, 220, 140), thick, cv2.LINE_AA)


# ══════════════════════════════════════════════════════════════════════════════
# THUMBS UP GESTURE DETECTOR
# ══════════════════════════════════════════════════════════════════════════════

class ThumbsUpChecker:
    """
    Deteksi gesture 👍 (jempol naik):
    - Ibu jari (tip 4) jauh lebih tinggi dari pangkalnya (CMC 2)
    - Keempat jari lain menekuk (tip y > pip y)
    """

    @staticmethod
    def is_thumbs_up(landmarks) -> bool:
        lm = landmarks

        # Ibu jari tegak: tip.y jauh lebih kecil (atas) dari IP joint
        thumb_tip = lm[4]
        thumb_ip  = lm[3]
        thumb_mcp = lm[2]
        thumb_up  = (thumb_tip.y < thumb_ip.y - 0.04) and (thumb_tip.y < thumb_mcp.y - 0.06)

        # Keempat jari menekuk: tip.y > pip.y
        fingers_curled = all(
            lm[tip].y > lm[pip].y + 0.02
            for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]
        )

        return thumb_up and fingers_curled


# ══════════════════════════════════════════════════════════════════════════════
# SARANGEO (ILY 🤟) GESTURE DETECTOR
# ══════════════════════════════════════════════════════════════════════════════

SARANGEO_QUOTES = [
    "Saranghae~ 💕",
    "I love you to the moon and back 🌙",
    "Cinta itu buta, tapi hati yang melihat ❤️",
    "Kamu bintang di langit malamku ✨",
    "Stay in love, stay alive 💖",
    "Love is the answer 🌸",
    "Hatiku milikmu selamanya 💗",
    "사랑해요~ (Saranghaeyo) 🥰",
    "You make my heart go boom 💓",
    "Dimana kamu, di situ hatiku 🫀",
    "Love without limits 💝",
    "Kamu adalah alasan senyumku 😊",
    "세상에서 제일 사랑해 (Cinta terbesar di dunia) ❤️",
    "My heart beats only for you 💞",
    "Jangan pergi, aku butuh kamu 🥺",
]


class SarangeoChecker:
    """
    Deteksi gesture 🤟 ILY / Sarangeo:
    - Ibu jari (4) naik
    - Telunjuk (8) naik
    - Kelingking (20) naik
    - Jari tengah (12) & manis (16) menekuk
    """

    @staticmethod
    def is_sarangeo(landmarks) -> bool:
        lm = landmarks

        # Ibu jari tegak
        thumb_up = lm[4].y < lm[3].y - 0.03

        # Telunjuk tegak
        index_up = lm[8].y < lm[6].y - 0.03

        # Kelingking tegak
        pinky_up = lm[20].y < lm[18].y - 0.03

        # Jari tengah & manis menekuk
        middle_curled = lm[12].y > lm[10].y + 0.02
        ring_curled   = lm[16].y > lm[14].y + 0.02

        return thumb_up and index_up and pinky_up and middle_curled and ring_curled


# ══════════════════════════════════════════════════════════════════════════════
# FILTER BANK
# ══════════════════════════════════════════════════════════════════════════════

class FilterBank:
    @staticmethod
    def dual_tone(roi):
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY)
        out = np.zeros_like(roi)
        out[mask == 255] = (10, 140, 255)
        out[mask == 0]   = (180, 30, 220)
        return out

    @staticmethod
    def thermal(roi):
        return cv2.applyColorMap(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), cv2.COLORMAP_JET)

    @staticmethod
    def sketch(roi):
        gray  = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        inv   = 255 - gray
        blur  = cv2.GaussianBlur(inv, (21, 21), 0)
        sk    = cv2.divide(gray, 255 - blur, scale=256)
        return cv2.cvtColor(sk, cv2.COLOR_GRAY2BGR)

    @staticmethod
    def pixelate(roi, block_size=14):
        h, w = roi.shape[:2]
        if h < 2 or w < 2: return roi
        small = cv2.resize(roi, (max(1, w//block_size), max(1, h//block_size)), interpolation=cv2.INTER_LINEAR)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

    @staticmethod
    def glitch(roi):
        h, w = roi.shape[:2]
        if h < 2 or w < 2: return roi
        b, g, r = cv2.split(roi)
        s = random.randint(4, 12)
        r = np.roll(r, s, axis=1); b = np.roll(b, -s, axis=1)
        out = cv2.merge([b, g, r])
        for _ in range(2):
            y = random.randint(0, h-1)
            out[y:y+1, :] = np.random.randint(0, 255, (1, w, 3), dtype=np.uint8)
        return out

    @staticmethod
    def invert(roi): return 255 - roi

    @staticmethod
    def red_channel(roi):
        b, g, r = cv2.split(roi)
        z = np.zeros_like(b)
        return cv2.merge([z, z, r])

    @staticmethod
    def edge(roi):
        gray  = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 60, 150)
        col   = cv2.applyColorMap(edges, cv2.COLORMAP_SUMMER)
        return cv2.bitwise_and(col, col, mask=edges)

    @staticmethod
    def blur(roi): return cv2.GaussianBlur(roi, (25, 25), 0)

    @staticmethod
    def cartoon(roi):
        gray  = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.adaptiveThreshold(cv2.medianBlur(gray, 5), 255,
                                      cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(roi, 9, 250, 250)
        return cv2.bitwise_and(color, cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR))

    @staticmethod
    def rainbow_wave(roi):
        h, w  = roi.shape[:2]
        t     = time.time() * 5.0
        xc, yc = np.meshgrid(np.arange(w), np.arange(h))
        pat   = np.sin((xc + yc) * 0.05 + t) * 127 + 128
        rb    = cv2.applyColorMap(pat.astype(np.uint8), cv2.COLORMAP_HSV)
        return cv2.addWeighted(roi, 0.3, rb, 0.7, 0)


# ══════════════════════════════════════════════════════════════════════════════
# GEOMETRY UTILS
# ══════════════════════════════════════════════════════════════════════════════

class GeometryUtils:
    @staticmethod
    def euclidean_dist(p1, p2):
        return float(np.hypot(p1[0]-p2[0], p1[1]-p2[1]))

    @staticmethod
    def is_fist_closed(landmarks, w, h, threshold):
        wrist = np.array([landmarks[0].x*w, landmarks[0].y*h])
        dists = [np.linalg.norm(np.array([landmarks[t].x*w, landmarks[t].y*h]) - wrist) for t in [8,12,16,20]]
        return float(np.mean(dists)) < threshold

    @staticmethod
    def is_hand_rotated(thumb, index):
        dx, dy = index[0]-thumb[0], index[1]-thumb[1]
        return (dy > 25) or (abs(dx) > abs(dy)*1.1)

    @staticmethod
    def sort_quad_clean(pts):
        arr = np.array(pts, dtype=np.float32)
        xs  = arr[np.argsort(arr[:,0]),:]
        L   = xs[:2,:][np.argsort(xs[:2,1]),:]
        R   = xs[2:,:][np.argsort(xs[2:,1]),:]
        return np.array([L[0],R[0],R[1],L[1]], dtype=np.int32)

    @staticmethod
    def sort_quad_bowtie(pts):
        arr = np.array(pts, dtype=np.float32)
        xs  = arr[np.argsort(arr[:,0]),:]
        L   = xs[:2,:][np.argsort(xs[:2,1]),:]
        R   = xs[2:,:][np.argsort(xs[2:,1]),:]
        return np.array([L[0],R[1],R[0],L[1]], dtype=np.int32)

    @staticmethod
    def is_peace(landmarks, w: int, h: int) -> bool:
        def tip_above_pip(tip_idx, pip_idx):
            return landmarks[tip_idx].y < landmarks[pip_idx].y
        def tip_below_pip(tip_idx, pip_idx):
            return landmarks[tip_idx].y > landmarks[pip_idx].y + 0.04
        index_up  = tip_above_pip(8, 6)
        middle_up = tip_above_pip(12, 10)
        ring_down = tip_below_pip(16, 14)
        pinky_down= tip_below_pip(20, 18)
        return index_up and middle_up and ring_down and pinky_down

    @staticmethod
    def face_oval_points(face_lm, w, h):
        OVAL = [10,338,297,332,284,251,389,356,454,323,361,288,
                397,365,379,378,400,377,152,148,176,149,150,136,
                172,58,132,93,234,127,162,21,54,103,67,109]
        return np.array([(int(face_lm.landmark[i].x*w), int(face_lm.landmark[i].y*h)) for i in OVAL], dtype=np.int32)


# ══════════════════════════════════════════════════════════════════════════════
# FACE FILTER
# ══════════════════════════════════════════════════════════════════════════════

# ── Emoji list yang muncul di atas wajah — bisa diganti sesuka hati ──────────
FACE_EMOJIS = ["😎", "🤩", "👻", "🤖", "🐸", "😂", "🔥", "💀"]
# Index emoji aktif (0 = 😎). Tekan E di keyboard untuk ganti.
_active_emoji_idx = 0


def _draw_emoji_on_frame(frame: np.ndarray, cx: int, cy: int, size: int, emoji: str) -> None:
    """
    Render emoji pakai PIL supaya bisa unicode, lalu blend ke frame OpenCV.
    Kalau PIL tidak ada, fallback ke teks ASCII.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os

        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw    = ImageDraw.Draw(pil_img)

        # Cari font emoji — Windows / Linux / Mac
        font_paths = [
            "C:/Windows/Fonts/seguiemj.ttf",      # Windows Segoe UI Emoji
            "C:/Windows/Fonts/seguisym.ttf",
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
            "/System/Library/Fonts/Apple Color Emoji.ttc",
        ]
        font = None
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, size)
                    break
                except Exception:
                    continue
        if font is None:
            font = ImageFont.load_default()

        # Gambar emoji di atas kepala
        draw.text((cx - size // 2, cy - size - 10), emoji, font=font, embedded_color=True)
        frame[:] = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception:
        # Fallback ASCII jika PIL tidak ada
        label = {
            "😎": ":)", "🤩": "*_*", "👻": "BOO", "🤖": "[AI]",
            "🐸": "PEPE", "😂": "LOL", "🔥": "HOT", "💀": "DEAD"
        }.get(emoji, "?")
        cv2.putText(frame, label, (cx - 20, cy - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 200), 2, cv2.LINE_AA)


class FaceFilterProcessor:
    def __init__(self, cfg):
        self.cfg = cfg
        self.mp_face = mp.solutions.face_mesh
        self.detector = self.mp_face.FaceMesh(
            static_image_mode=False, max_num_faces=2, refine_landmarks=True,
            min_detection_confidence=0.7, min_tracking_confidence=0.6)

    def apply(self, frame, filter_fn):
        global _active_emoji_idx
        h, w = frame.shape[:2]
        results = self.detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        face_count = 0
        if not results.multi_face_landmarks:
            return frame, 0
        for face_lm in results.multi_face_landmarks:
            face_count += 1
            oval_pts = GeometryUtils.face_oval_points(face_lm, w, h)
            x, y, bw, bh = cv2.boundingRect(oval_pts)
            x, y = max(0,x), max(0,y)
            bw, bh = min(bw, w-x), min(bh, h-y)
            if bw < 10 or bh < 10: continue
            roi = frame[y:y+bh, x:x+bw].copy()
            filtered = filter_fn(roi)
            mask = np.zeros((bh, bw), dtype=np.uint8)
            cv2.fillPoly(mask, [oval_pts - [x,y]], 255)
            mask = cv2.GaussianBlur(mask, (15,15), 0)
            m = cv2.merge([mask,mask,mask]).astype(np.float32)/255.0
            frame[y:y+bh, x:x+bw] = (filtered*m + roi*(1-m)).astype(np.uint8)
            cv2.polylines(frame, [oval_pts], True, (0,220,255), 1)

        return frame, face_count

    def close(self): self.detector.close()


# ══════════════════════════════════════════════════════════════════════════════
# FPV DRONE HUD
# ══════════════════════════════════════════════════════════════════════════════

import psutil, platform, datetime

class FPVHud:
    FONT       = cv2.FONT_HERSHEY_SIMPLEX
    MONO       = cv2.FONT_HERSHEY_PLAIN
    C_GREEN    = (0, 255, 120)
    C_CYAN     = (0, 220, 255)
    C_WHITE    = (220, 220, 220)
    C_YELLOW   = (0, 215, 255)
    C_RED      = (60, 60, 255)
    C_ORANGE   = (0, 165, 255)
    C_DIM      = (90, 90, 90)
    C_TEAL     = (180, 255, 100)
    FINGER_LABELS = {4: "THB", 8: "IDX", 12: "MID", 16: "RNG", 20: "PNK"}
    _fps_buf: List[float] = []
    _last_ts: float = 0.0

    @classmethod
    def draw(cls, frame: np.ndarray, proc, is_bowtie: bool,
             face_count: int, all_tips: list,
             peace_active: bool, fist_count: int) -> None:

        h, w = frame.shape[:2]
        now  = time.time()

        if cls._last_ts:
            cls._fps_buf.append(1.0 / max(now - cls._last_ts, 1e-6))
            if len(cls._fps_buf) > 30: cls._fps_buf.pop(0)
        cls._last_ts = now
        fps = sum(cls._fps_buf) / len(cls._fps_buf) if cls._fps_buf else 0.0

        ram      = psutil.virtual_memory()
        cpu_pct  = psutil.cpu_percent(interval=None)
        ram_used = ram.used  / (1024**2)
        ram_tot  = ram.total / (1024**2)
        ram_pct  = ram.percent
        ts_str   = datetime.datetime.now().strftime("%H:%M:%S")
        date_str = datetime.datetime.now().strftime("%d/%m/%Y")
        os_str   = platform.system().upper()[:3]

        def panel(x1, y1, x2, y2, alpha=0.35):
            ovl = frame.copy()
            cv2.rectangle(ovl, (x1, y1), (x2, y2), (0, 0, 0), -1)
            cv2.addWeighted(ovl, alpha, frame, 1-alpha, 0, frame)

        def txt(text, x, y, color=None, scale=0.45, thick=1, font=None):
            cv2.putText(frame, text, (x, y),
                        font or cls.FONT, scale, color or cls.C_WHITE,
                        thick, cv2.LINE_AA)

        def bar_h(x, y, bw, bh, pct, fg, bg=(40,40,40)):
            cv2.rectangle(frame, (x, y), (x+bw, y+bh), bg, -1)
            cv2.rectangle(frame, (x, y), (x+int(bw*pct/100), y+bh), fg, -1)
            cv2.rectangle(frame, (x, y), (x+bw, y+bh), cls.C_DIM, 1)

        # ══ TOP-LEFT
        panel(4, 4, 310, 115)
        cv2.rectangle(frame, (4,4), (310,115), cls.C_CYAN, 1)
        mode_str  = "3D-MESH" if proc.is_3d_mode else ("2D-BOWTIE" if is_bowtie else "2D-QUAD")
        face_str  = f"FACE {face_count}" if proc.face_mode else "FACE OFF"
        txt(f"MODE   {mode_str}",          14, 24,  cls.C_CYAN,   0.50, 1)
        txt(f"FILTER {proc.current_filter.upper()}", 14, 44, cls.C_WHITE, 0.50, 1)
        txt(f"HANDS  {len(all_tips)}  |  {face_str}", 14, 64, cls.C_TEAL,  0.45, 1)
        gestures = []
        if peace_active:       gestures.append("V BLUR")
        if fist_count == 2:    gestures.append("FIST2 MODE")
        if fist_count == 1:    gestures.append("FIST")
        g_str = "  ".join(gestures) if gestures else "-"
        txt(f"GESTURE {g_str}", 14, 84, cls.C_ORANGE, 0.45, 1)
        txt(f"NEXT   {proc.secondary_filter.upper()}", 14, 104, cls.C_DIM, 0.40, 1)

        # ══ TOP-RIGHT
        panel(w-220, 4, w-4, 155)
        cv2.rectangle(frame, (w-220,4), (w-4,155), cls.C_GREEN, 1)
        rx = w - 210
        txt(f"{ts_str}  {date_str}",  rx, 22,  cls.C_YELLOW, 0.48, 1)
        txt(f"FPS  {fps:5.1f}",       rx, 42,  cls.C_GREEN,  0.48, 1)
        txt(f"OS   {os_str}",         rx, 62,  cls.C_WHITE,  0.45, 1)
        txt(f"CPU  {cpu_pct:4.1f}%",  rx, 80,  cls.C_WHITE,  0.45, 1)
        bar_h(rx, 86, 190, 5, cpu_pct,
              cls.C_GREEN if cpu_pct < 60 else cls.C_ORANGE if cpu_pct < 85 else cls.C_RED)
        txt(f"RAM  {ram_used:.0f}/{ram_tot:.0f} MB", rx, 106, cls.C_WHITE, 0.45, 1)
        bar_h(rx, 112, 190, 5, ram_pct,
              cls.C_CYAN if ram_pct < 60 else cls.C_ORANGE if ram_pct < 85 else cls.C_RED)
        txt(f"     {ram_pct:.1f}%",   rx, 128, cls.C_DIM,   0.38, 1)
        txt(f"RES  {w}x{h}", rx, 148, cls.C_DIM, 0.40, 1)

        # ══ BOTTOM-LEFT fingertip coords
        if all_tips:
            hand_labels = ["L-HAND","R-HAND"]
            base_y = h - 10 - len(all_tips) * 75
            panel(4, base_y - 14, 220, h - 4)
            cv2.rectangle(frame, (4, base_y-14), (220, h-4), cls.C_CYAN, 1)
            for hi, tips in enumerate(all_tips):
                label = hand_labels[hi] if hi < 2 else f"HAND{hi}"
                txt(f"-- {label} --", 10, base_y + hi*75, cls.C_CYAN, 0.42, 1)
                tip_indices = [4, 8, 12, 16, 20]
                for fi, (tx, ty) in enumerate(tips):
                    fname = cls.FINGER_LABELS.get(tip_indices[fi], f"F{fi}")
                    col = cls.C_YELLOW if fi == 1 else cls.C_WHITE
                    txt(f"  {fname}  X:{tx:4d}  Y:{ty:4d}",
                        10, base_y + hi*75 + 14 + fi*12,
                        col, 0.37, 1)

        # ══ SCAN LINE
        for y_sl in range(0, h, 6):
            cv2.line(frame, (0, y_sl), (w, y_sl), (0,0,0), 1)
        ovl2 = frame.copy()
        cv2.addWeighted(ovl2, 0.92, frame, 0.08, 0, frame)


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineConfig:
    cam_index: int = 0
    frame_width: int = 1920
    frame_height: int = 1080
    pinch_threshold_px: float = 45.0
    filter_cooldown_sec: float = 0.15
    mode_cooldown_sec: float = 1.2
    fist_dist_threshold_px: float = 80.0
    face_filter_enabled: bool = True


# ══════════════════════════════════════════════════════════════════════════════
# PORTAL PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════

class PortalProcessor:
    def __init__(self, cfg: PipelineConfig):
        self.cfg = cfg
        self.filters: Dict[str, Callable] = {
            "dual-tone":    FilterBank.dual_tone,
            "thermal":      FilterBank.thermal,
            "sketch":       FilterBank.sketch,
            "pixelate":     FilterBank.pixelate,
            "glitch":       FilterBank.glitch,
            "invert":       FilterBank.invert,
            "red-channel":  FilterBank.red_channel,
            "edge":         FilterBank.edge,
            "blur":         FilterBank.blur,
            "cartoon":      FilterBank.cartoon,
            "rainbow-wave": FilterBank.rainbow_wave,
        }
        self.filter_keys         = list(self.filters.keys())
        self.active_filter_idx   = 0
        self.is_3d_mode          = False
        self.face_mode           = cfg.face_filter_enabled
        self.last_switch_time    = 0.0
        self.last_mode_toggle    = 0.0

        self.mp_hands  = mp.solutions.hands
        self.mp_draw   = mp.solutions.drawing_utils
        self.detector  = self.mp_hands.Hands(
            static_image_mode=False, max_num_hands=2, model_complexity=1,
            min_detection_confidence=0.8, min_tracking_confidence=0.8)

        self.face_proc    = FaceFilterProcessor(cfg)
        self.watermark_ui = WatermarkUI(cfg.frame_width, cfg.frame_height)
        self.photo_cap    = PhotoCapture(cfg.frame_width, cfg.frame_height)

        # Flag jempol untuk animasi close
        self._thumbsup_triggered = False
        self._thumbsup_frame_start = 0.0

        # Flag sarangeo 🤟
        self._sarangeo_triggered  = False
        self._sarangeo_quote      = ""
        self._sarangeo_quote_until = 0.0

        # Tombol EXIT
        self._exit_requested = False
        self._exit_btn_rect  = (cfg.frame_width - 70, 4, cfg.frame_width - 4, 30)

    @property
    def current_filter(self): return self.filter_keys[self.active_filter_idx]
    @property
    def secondary_filter(self): return self.filter_keys[(self.active_filter_idx+1) % len(self.filter_keys)]

    def cycle_filter(self, step=1):
        self.active_filter_idx = (self.active_filter_idx+step) % len(self.filter_keys)

    def render_portal(self, frame, pts, filter_key):
        poly = np.array(pts, dtype=np.int32)
        x, y, w, h = cv2.boundingRect(poly)
        x, y = max(0,x), max(0,y)
        w, h = min(w, frame.shape[1]-x), min(h, frame.shape[0]-y)
        if w <= 10 or h <= 10: return frame
        roi  = frame[y:y+h, x:x+w].copy()
        proc = self.filters[filter_key](roi)
        mask = np.zeros((h,w), dtype=np.uint8)
        cv2.fillPoly(mask, [poly-[x,y]], 255)
        m3   = cv2.merge([mask,mask,mask])
        frame[y:y+h, x:x+w] = cv2.add(cv2.bitwise_and(roi, cv2.bitwise_not(m3)),
                                        cv2.bitwise_and(proc, m3))
        cv2.polylines(frame, [poly], True, (255,255,255), 2)
        return frame

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Return processed_frame."""
        frame   = cv2.flip(frame, 1)
        h_cam, w_cam = frame.shape[:2]
        if w_cam != self.cfg.frame_width or h_cam != self.cfg.frame_height:
            frame = cv2.resize(frame, (self.cfg.frame_width, self.cfg.frame_height),
                               interpolation=cv2.INTER_LINEAR)
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.detector.process(rgb)
        now     = time.time()

        all_tips    = []
        fist_count  = 0
        is_bowtie   = False
        peace_count = 0
        thumbsup    = False

        if results.multi_hand_landmarks:
            for hand_lm in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_lm, self.mp_hands.HAND_CONNECTIONS)
                lm   = hand_lm.landmark
                tips = [(int(lm[i].x*self.cfg.frame_width), int(lm[i].y*self.cfg.frame_height)) for i in [4,8,12,16,20]]
                all_tips.append(tips)

                if GeometryUtils.euclidean_dist(tips[0], tips[4]) < self.cfg.pinch_threshold_px:
                    if now - self.last_switch_time > self.cfg.filter_cooldown_sec:
                        self.cycle_filter(1); self.last_switch_time = now

                if GeometryUtils.is_fist_closed(lm, self.cfg.frame_width, self.cfg.frame_height, self.cfg.fist_dist_threshold_px):
                    fist_count += 1

                if GeometryUtils.is_peace(lm, self.cfg.frame_width, self.cfg.frame_height):
                    peace_count += 1

                if ThumbsUpChecker.is_thumbs_up(lm):
                    thumbsup = True

                if SarangeoChecker.is_sarangeo(lm):
                    if not self._sarangeo_triggered:
                        self._sarangeo_triggered   = True
                        self._sarangeo_quote       = random.choice(SARANGEO_QUOTES)
                        self._sarangeo_quote_until = now + 3.0
                else:
                    self._sarangeo_triggered = False

            if fist_count == 2 and now - self.last_mode_toggle > self.cfg.mode_cooldown_sec:
                self.is_3d_mode = not self.is_3d_mode; self.last_mode_toggle = now

            if self.is_3d_mode:
                if len(all_tips) == 2:
                    t1,t2 = all_tips
                    self.render_portal(frame, [t1[0],t1[1],t1[2],t2[2],t2[1],t2[0]], self.current_filter)
                    self.render_portal(frame, [t1[2],t1[3],t1[4],t2[4],t2[3],t2[2]], self.secondary_filter)
                elif len(all_tips)==1:
                    self.render_portal(frame, all_tips[0], self.current_filter)
            else:
                if len(all_tips)==2:
                    c = [all_tips[0][0],all_tips[0][1],all_tips[1][0],all_tips[1][1]]
                    if GeometryUtils.is_hand_rotated(c[0],c[1]) or GeometryUtils.is_hand_rotated(c[2],c[3]):
                        quad = GeometryUtils.sort_quad_bowtie(c); is_bowtie=True
                    else:
                        quad = GeometryUtils.sort_quad_clean(c)
                    self.render_portal(frame, quad, self.current_filter)
                elif len(all_tips)==1:
                    t=all_tips[0]; self.render_portal(frame, [t[0],t[1],t[2],t[4]], self.current_filter)

        # ── Peace → blur seluruh frame ─────────────────────────────────────────
        if peace_count > 0:
            frame = cv2.GaussianBlur(frame, (31, 31), 0)
            cv2.putText(frame, "V BLUR MODE", (15, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 180), 2, cv2.LINE_AA)

        # ── 👍 Thumbs Up → blur background + teks "Mas Faisal Ganteng" ───────
        if thumbsup:
            if not self._thumbsup_triggered:
                self._thumbsup_triggered   = True
                self._thumbsup_frame_start = now
            # Blur seluruh background
            frame[:] = cv2.GaussianBlur(frame, (45, 45), 0)
            # Teks di tengah
            name_text = "Mas Faisal Ganteng"
            font  = cv2.FONT_HERSHEY_SIMPLEX
            scale = 1.6; thick = 3
            fw_f, fh_f = self.cfg.frame_width, self.cfg.frame_height
            (tw, th), _ = cv2.getTextSize(name_text, font, scale, thick)
            tx = (fw_f - tw) // 2
            ty = fh_f // 2 + th // 2
            cv2.putText(frame, name_text, (tx+3, ty+3), font, scale, (0, 0, 0), thick+3, cv2.LINE_AA)
            cv2.putText(frame, name_text, (tx, ty), font, scale, (255, 255, 255), thick, cv2.LINE_AA)
        else:
            self._thumbsup_triggered = False

        # ── 🤟 Sarangeo → tampilkan kata-kata random di tengah layar ──────────
        if now < self._sarangeo_quote_until and self._sarangeo_quote:
            quote = self._sarangeo_quote
            font  = cv2.FONT_HERSHEY_SIMPLEX
            scale = 1.2; thick = 2
            fw_f, fh_f = self.cfg.frame_width, self.cfg.frame_height
            (tw, th), _ = cv2.getTextSize(quote, font, scale, thick)
            tx = (fw_f - tw) // 2
            ty = fh_f // 2

            # Background semi-transparan
            pad = 20
            ovl = frame.copy()
            cv2.rectangle(ovl,
                          (tx - pad, ty - th - pad),
                          (tx + tw + pad, ty + pad),
                          (20, 10, 40), -1)
            cv2.addWeighted(ovl, 0.65, frame, 0.35, 0, frame)

            # Border pink
            cv2.rectangle(frame,
                          (tx - pad, ty - th - pad),
                          (tx + tw + pad, ty + pad),
                          (180, 80, 220), 2)

            # Shadow + teks
            cv2.putText(frame, quote, (tx+2, ty+2), font, scale, (0, 0, 0), thick+2, cv2.LINE_AA)
            cv2.putText(frame, quote, (tx, ty), font, scale, (255, 180, 255), thick, cv2.LINE_AA)

        face_count = 0
        if self.face_mode:
            frame, face_count = self.face_proc.apply(frame, self.filters[self.current_filter])

        self._draw_hud(frame, is_bowtie, face_count, all_tips, peace_count > 0, fist_count)
        self.watermark_ui.draw(frame)
        self.photo_cap.draw(frame)

        return frame

    def _draw_hud(self, frame, is_bowtie, face_count, all_tips=None, peace_active=False, fist_count=0):
        FPVHud.draw(frame, self, is_bowtie, face_count,
                    all_tips or [], peace_active, fist_count)
        # Tombol EXIT — pojok kanan atas
        ex1, ey1, ex2, ey2 = self._exit_btn_rect
        ovl = frame.copy()
        cv2.rectangle(ovl, (ex1, ey1), (ex2, ey2), (30, 20, 20), -1)
        cv2.addWeighted(ovl, 0.8, frame, 0.2, 0, frame)
        cv2.rectangle(frame, (ex1, ey1), (ex2, ey2), (60, 60, 200), 1)
        cv2.putText(frame, "EXIT", (ex1 + 8, ey2 - 7),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (80, 80, 255), 1, cv2.LINE_AA)

    def close(self):
        self.face_proc.close()
        self.detector.close()


# ══════════════════════════════════════════════════════════════════════════════
# INTRO SCREEN — input nama + animasi typewriter
# ══════════════════════════════════════════════════════════════════════════════

class IntroScreen:
    """
    Fase 1 : Form input nama (keyboard + tombol OK di layar)
    Fase 2 : Animasi typewriter baris per baris, lalu launch app
    """

    LINES_TEMPLATE = [
        "Halo, {name}.",
        "Selamat datang di Tracking Engine.",
        "Sistem siap digunakan.",
        "",
        "Requested by Mas Rofiqz RJS",
        "",
        "In engineer we trust.",
        "— Faisaldev",
    ]

    CHAR_DELAY   = 0.045   # detik per karakter
    LINE_PAUSE   = 0.35    # jeda antar baris
    HOLD_AFTER   = 1.6     # tahan di akhir sebelum masuk app

    def __init__(self, fw: int, fh: int):
        self.fw = fw
        self.fh = fh
        self.name       = ""          # input user
        self.phase      = "input"     # "input" | "typing" | "done"
        self.cursor_vis = True
        self._cursor_t  = time.time()

        # State typewriter
        self._lines: list  = []
        self._line_idx     = 0
        self._char_idx     = 0
        self._next_char_t  = 0.0
        self._done_t       = 0.0

        # Tombol OK
        bw, bh = 100, 36
        self._ok_rect = (fw//2 - bw//2, fh//2 + 60, fw//2 + bw//2, fh//2 + 60 + bh)

    # ── public ────────────────────────────────────────────────────────────────

    def handle_key(self, key: int) -> None:
        if self.phase != "input":
            return
        if key == 13 or key == 10:          # Enter → submit
            self._submit()
        elif key == 8 or key == 127:        # Backspace
            self.name = self.name[:-1]
        elif 32 <= key <= 126:              # Printable ASCII
            if len(self.name) < 24:
                self.name += chr(key)

    def handle_click(self, mx: int, my: int) -> None:
        if self.phase != "input":
            return
        x1, y1, x2, y2 = self._ok_rect
        if x1 <= mx <= x2 and y1 <= my <= y2:
            self._submit()

    def is_finished(self) -> bool:
        return self.phase == "done" and time.time() >= self._done_t

    def draw(self, canvas: np.ndarray) -> np.ndarray:
        if self.phase == "input":
            self._draw_input(canvas)
        else:
            self._draw_typing(canvas)
        return canvas

    # ── private ───────────────────────────────────────────────────────────────

    def _submit(self):
        name = self.name.strip() or "Anonim"
        self._lines = [l.format(name=name) for l in self.LINES_TEMPLATE]
        self._line_idx    = 0
        self._char_idx    = 0
        self._next_char_t = time.time() + 0.3
        self.phase        = "typing"

    def _draw_input(self, frame: np.ndarray) -> None:
        fw, fh = self.fw, self.fh
        frame[:] = (12, 12, 18)

        font = cv2.FONT_HERSHEY_SIMPLEX
        now  = time.time()

        # ── Judul
        title = "TRACKING ENGINE"
        (tw, _), _ = cv2.getTextSize(title, font, 2.2, 4)
        cv2.putText(frame, title, ((fw - tw) // 2, fh // 2 - 200),
                    font, 2.2, (0, 220, 255), 4, cv2.LINE_AA)

        # ── Sub
        sub = "Siapa nama Anda?"
        (sw, _), _ = cv2.getTextSize(sub, font, 1.1, 2)
        cv2.putText(frame, sub, ((fw - sw) // 2, fh // 2 - 100),
                    font, 1.1, (160, 160, 160), 2, cv2.LINE_AA)

        # ── Input box
        bx1, bx2 = fw // 2 - 380, fw // 2 + 380
        by1, by2 = fh // 2 - 50,  fh // 2 + 24
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (30, 30, 40), -1)
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 180, 255), 2)

        # Cursor blink
        if now - self._cursor_t > 0.5:
            self.cursor_vis = not self.cursor_vis
            self._cursor_t  = now
        display = self.name + ("|" if self.cursor_vis else " ")
        cv2.putText(frame, display, (bx1 + 18, by2 - 12),
                    font, 1.2, (255, 255, 255), 2, cv2.LINE_AA)

        # ── Tombol OK (recalc supaya sesuai resolusi)
        bw_ok, bh_ok = 280, 68
        ox1 = fw // 2 - bw_ok // 2
        oy1 = fh // 2 + 60
        ox2 = ox1 + bw_ok
        oy2 = oy1 + bh_ok
        self._ok_rect = (ox1, oy1, ox2, oy2)
        cv2.rectangle(frame, (ox1, oy1), (ox2, oy2), (0, 140, 60), -1)
        cv2.rectangle(frame, (ox1, oy1), (ox2, oy2), (0, 220, 100), 2)
        (ltw, _), _ = cv2.getTextSize("OK  /  Enter", font, 0.95, 2)
        cv2.putText(frame, "OK  /  Enter", ((fw - ltw) // 2, oy2 - 18),
                    font, 0.95, (255, 255, 255), 2, cv2.LINE_AA)

        # ── Footer
        cv2.putText(frame, "Powered by Faisaldev", (20, fh - 20),
                    font, 0.7, (50, 50, 60), 1, cv2.LINE_AA)

    def _draw_typing(self, frame: np.ndarray) -> None:
        fw, fh = self.fw, self.fh
        frame[:] = (12, 12, 18)

        font   = cv2.FONT_HERSHEY_SIMPLEX
        now    = time.time()
        line_h = 72

        # Advance typewriter
        if self._line_idx < len(self._lines):
            cur_line = self._lines[self._line_idx]
            if now >= self._next_char_t:
                if self._char_idx < len(cur_line):
                    self._char_idx    += 1
                    self._next_char_t  = now + self.CHAR_DELAY
                else:
                    # Baris selesai → lanjut baris berikut
                    self._line_idx   += 1
                    self._char_idx    = 0
                    self._next_char_t = now + self.LINE_PAUSE
        else:
            # Semua baris selesai
            if self._done_t == 0.0:
                self._done_t = now + self.HOLD_AFTER
            self.phase = "done"

        # Hitung posisi mulai agar vertikal center
        total_h = len(self._lines) * line_h
        start_y = (fh - total_h) // 2 + line_h

        for i, line in enumerate(self._lines):
            if i < self._line_idx:
                rendered = line              # baris sudah selesai
            elif i == self._line_idx:
                rendered = line[:self._char_idx]   # baris sedang diketik
            else:
                break                        # baris belum sampai

            # Pilih warna per baris
            if i == 0:
                color = (0, 220, 255)        # cyan — "Halo, nama"
                scale = 1.5; thick = 3
            elif i == len(self._lines) - 1:
                color = (180, 180, 180)      # abu — "— Faisaldev"
                scale = 0.9; thick = 2
            elif "Requested by" in line:
                color = (0, 215, 255)        # gold — "Requested by Mas Rofiqz RJS"
                scale = 1.1; thick = 3
            elif "In engineer" in line:
                color = (0, 215, 255)        # kuning
                scale = 1.1; thick = 2
            else:
                color = (200, 200, 200)
                scale = 1.05; thick = 2

            (tw, _), _ = cv2.getTextSize(rendered, font, scale, thick)
            tx = (fw - tw) // 2
            ty = start_y + i * line_h

            # Kursor blink di baris aktif
            disp = rendered
            if i == self._line_idx and self.phase == "typing":
                now2 = time.time()
                if now2 - self._cursor_t > 0.4:
                    self.cursor_vis = not self.cursor_vis
                    self._cursor_t  = now2
                disp += "|" if self.cursor_vis else " "

            cv2.putText(frame, disp, (tx, ty), font, scale, color, thick, cv2.LINE_AA)

        # Footer
        cv2.putText(frame, "Powered by Faisaldev", (20, fh - 20),
                    font, 0.7, (50, 50, 60), 1, cv2.LINE_AA)


# ══════════════════════════════════════════════════════════════════════════════
# MOUSE CALLBACK
# ══════════════════════════════════════════════════════════════════════════════

_processor_ref: Optional[PortalProcessor] = None
_intro_ref: Optional[object] = None
_pending_capture = False

def _on_mouse(event, x, y, flags, param):
    global _pending_capture
    if event == cv2.EVENT_LBUTTONDOWN:
        if _intro_ref and not _intro_ref.is_finished():
            _intro_ref.handle_click(x, y)
            return
        if _processor_ref:
            # Cek tombol EXIT
            ex1, ey1, ex2, ey2 = _processor_ref._exit_btn_rect
            if ex1 <= x <= ex2 and ey1 <= y <= ey2:
                _processor_ref._exit_requested = True
                return
            # Cek watermark dulu
            _processor_ref.watermark_ui.handle_click(x, y)
            # Cek photo capture
            if _processor_ref.photo_cap.handle_click(x, y):
                _pending_capture = True


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    global _processor_ref, _intro_ref, _pending_capture

    cfg       = PipelineConfig()
    processor = PortalProcessor(cfg)
    _processor_ref = processor

    cap = cv2.VideoCapture(cfg.cam_index)
    if not cap.isOpened():
        print("[ERROR] Kamera tidak terdeteksi!"); return

    # Set resolusi kamera ke HD secara hardware
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)

    win = "Tracking Engine"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback(win, _on_mouse)

    # ── INTRO SCREEN ──────────────────────────────────────────────────────────
    intro = IntroScreen(cfg.frame_width, cfg.frame_height)
    _intro_ref = intro
    canvas = np.zeros((cfg.frame_height, cfg.frame_width, 3), dtype=np.uint8)

    # Tampilkan dulu biar window dapat fokus
    intro.draw(canvas)
    cv2.imshow(win, canvas)
    cv2.waitKey(1)

    while not intro.is_finished():
        canvas[:] = 0
        intro.draw(canvas)
        cv2.imshow(win, canvas)

        raw = cv2.waitKey(1)        # non-blocking, 1ms — cegah freeze
        if raw == -1:
            raw = 0
        key = raw & 0xFFFF          # ambil 16-bit supaya tangkap karakter non-ASCII juga

        if key == 27:               # ESC — skip intro
            break
        if key == ord("q") and intro.phase != "input":
            break                   # Q hanya skip di fase typing, bukan saat ketik nama

        if intro.phase == "input":
            if key in (13, 10):                     # Enter
                intro._submit()
            elif key in (8, 127, 65288):            # Backspace (Linux/Mac/Win)
                intro.name = intro.name[:-1]
            elif 32 <= key <= 126:                  # Printable ASCII
                if len(intro.name) < 24:
                    intro.name += chr(key)

    _intro_ref = None
    # ── END INTRO ─────────────────────────────────────────────────────────────

    print("=== RetroLens Engine — Powered by Faisaldev ===")
    print("Q / EXIT btn : Keluar")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # Capture foto jika tombol kamera diklik
        if _pending_capture:
            _pending_capture = False
            processor.photo_cap.trigger_capture(
                cv2.resize(cv2.flip(frame, 1), (cfg.frame_width, cfg.frame_height))
            )

        out = processor.process_frame(frame)
        cv2.imshow(win, out)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or processor._exit_requested:
            break
        elif key == ord("c"):
            processor.is_3d_mode = not processor.is_3d_mode
        elif key == ord("n"):
            processor.cycle_filter(1)
        elif key == ord("p"):
            processor.cycle_filter(-1)
        elif key == ord("f"):
            processor.face_mode = not processor.face_mode
        elif key == ord("e"):
            import Retrolens as _rl
            _rl._active_emoji_idx = (_rl._active_emoji_idx + 1) % len(_rl.FACE_EMOJIS)
            print(f"[EMOJI] Ganti ke: {_rl.FACE_EMOJIS[_rl._active_emoji_idx]}")
        elif key == 27:
            processor.watermark_ui.show_modal = False

    processor.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
