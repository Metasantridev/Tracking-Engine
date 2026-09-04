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

WATERMARK_TEXT   = "Powered by: Faisaldev"
PRICING_PLANS    = [
    {"label": "Pro",     "price": 74_900,       "desc": "Hilangkan watermark + semua filter"},
    {"label": "Max",     "price": 2_500_000,    "desc": "Akses seumur hidup + source code"},
]


class WatermarkUI:
    """
    Draws persistent watermark on every frame.
    Clicking the [X] button → shows pricing modal.
    Clicking a 'Beli' button → shows 'saldo kurang' toast.
    All rendered with OpenCV — no external GUI library needed.
    """

    def __init__(self, frame_w: int, frame_h: int):
        self.fw = frame_w
        self.fh = frame_h

        # State
        self.show_modal   = False
        self.toast_msg    = ""
        self.toast_until  = 0.0
        self.selected_plan: Optional[int] = None   # index into PRICING_PLANS

        # Watermark geometry (bottom-right)
        self.wm_font       = cv2.FONT_HERSHEY_SIMPLEX
        self.wm_scale      = 0.52
        self.wm_thick      = 1
        (tw, th), _ = cv2.getTextSize(WATERMARK_TEXT, self.wm_font, self.wm_scale, self.wm_thick)
        pad = 6
        self.wm_x  = frame_w - tw - 36 - pad * 2 - 4
        self.wm_y  = frame_h - 12
        # [X] button rect
        btn_size   = 18
        self.x_rect = (
            frame_w - btn_size - 4,
            frame_h - btn_size - 4,
            frame_w - 4,
            frame_h - 4,
        )  # x1,y1,x2,y2

        # Modal geometry (centered)
        self.modal_w = 420
        self.modal_h = 260
        self.modal_x = (frame_w - self.modal_w) // 2
        self.modal_y = (frame_h - self.modal_h) // 2

        # Beli button rects per plan (built in _draw_modal)
        self.beli_rects: List[Tuple[int,int,int,int]] = []

    # ── public ────────────────────────────────────────────────────────────────

    def handle_click(self, mx: int, my: int) -> None:
        """Call this whenever the user clicks (mx, my)."""
        if self.show_modal:
            self._handle_modal_click(mx, my)
        else:
            self._handle_watermark_click(mx, my)

    def draw(self, frame: np.ndarray) -> np.ndarray:
        """Overlay watermark (and modal if active) onto frame. Mutates frame."""
        self._draw_watermark(frame)
        if self.show_modal:
            self._draw_modal(frame)
        self._draw_toast(frame)
        return frame

    # ── watermark ─────────────────────────────────────────────────────────────

    def _draw_watermark(self, frame: np.ndarray) -> None:
        # Semi-transparent background pill
        x1, y1, x2, y2 = self.x_rect
        overlay = frame.copy()
        cv2.rectangle(overlay,
                       (self.wm_x - 6, self.fh - 26),
                       (self.fw - 2,   self.fh - 2),
                       (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

        # Text
        cv2.putText(frame, WATERMARK_TEXT,
                    (self.wm_x, self.wm_y),
                    self.wm_font, self.wm_scale,
                    (255, 215, 0), self.wm_thick, cv2.LINE_AA)

        # [X] button
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

    # ── modal ─────────────────────────────────────────────────────────────────

    def _draw_modal(self, frame: np.ndarray) -> None:
        mx, my = self.modal_x, self.modal_y
        mw, mh = self.modal_w, self.modal_h
        self.beli_rects = []

        # Backdrop blur-ish (darkened overlay)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.fw, self.fh), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        # Modal card
        cv2.rectangle(frame, (mx, my), (mx+mw, my+mh), (28, 28, 35), -1)
        cv2.rectangle(frame, (mx, my), (mx+mw, my+mh), (80, 80, 100), 2)

        # Title
        cv2.putText(frame, "Hapus Watermark",
                    (mx+18, my+34), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                    (255, 215, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, "Pilih paket untuk melanjutkan:",
                    (mx+18, my+58), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (180, 180, 180), 1, cv2.LINE_AA)

        # Divider
        cv2.line(frame, (mx+12, my+68), (mx+mw-12, my+68), (70, 70, 90), 1)

        # Plans
        for i, plan in enumerate(PRICING_PLANS):
            row_y = my + 88 + i * 72
            is_sel = (self.selected_plan == i)
            border_col = (0, 200, 120) if is_sel else (70, 70, 90)
            cv2.rectangle(frame, (mx+14, row_y), (mx+mw-14, row_y+54), (38, 38, 48), -1)
            cv2.rectangle(frame, (mx+14, row_y), (mx+mw-14, row_y+54), border_col, 1)

            # Plan label & desc
            cv2.putText(frame, f"  {plan['label']}  —  Rp {plan['price']:,}".replace(",", "."),
                        (mx+22, row_y+22), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                        (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"  {plan['desc']}",
                        (mx+22, row_y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                        (150, 150, 150), 1, cv2.LINE_AA)

            # Beli button
            bx1 = mx + mw - 82
            bx2 = mx + mw - 18
            by1 = row_y + 12
            by2 = row_y + 38
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 160, 80), -1)
            cv2.putText(frame, "Beli",
                        (bx1+14, by2-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255, 255, 255), 1, cv2.LINE_AA)
            self.beli_rects.append((bx1, by1, bx2, by2))

        # Close modal hint
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
        # click outside modal card → close
        cx1, cy1 = self.modal_x, self.modal_y
        cx2, cy2 = cx1 + self.modal_w, cy1 + self.modal_h
        if not (cx1 <= mx <= cx2 and cy1 <= my <= cy2):
            self.show_modal = False

    # ── toast ─────────────────────────────────────────────────────────────────

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
        """
        Peace / victory sign: jari telunjuk (8) & tengah (12) tegak,
        jari manis (16) & kelingking (20) menekuk ke telapak.
        Ibu jari (4) tidak diperhitungkan.
        """
        def tip_above_pip(tip_idx, pip_idx):
            return landmarks[tip_idx].y < landmarks[pip_idx].y  # y lebih kecil = lebih atas

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

class FaceFilterProcessor:
    def __init__(self, cfg):
        self.cfg = cfg
        self.mp_face = mp.solutions.face_mesh
        self.detector = self.mp_face.FaceMesh(
            static_image_mode=False, max_num_faces=2, refine_landmarks=True,
            min_detection_confidence=0.7, min_tracking_confidence=0.6)

    def apply(self, frame, filter_fn):
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
    """
    Full FPV-style heads-up display.
    Layout:
      TOP-LEFT     : mode, filter, face, gesture aktif
      TOP-RIGHT    : waktu, FPS, RAM, CPU, platform
      BOTTOM-LEFT  : koordinat tiap fingertip tangan
      CENTER-TOP   : crosshair + artificial horizon bar
      BOTTOM-CENTER: gesture legend
    """

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

    # finger label per tip index
    FINGER_LABELS = {4: "THB", 8: "IDX", 12: "MID", 16: "RNG", 20: "PNK"}

    _fps_buf: List[float] = []
    _last_ts: float = 0.0

    @classmethod
    def draw(cls, frame: np.ndarray, proc, is_bowtie: bool,
             face_count: int, all_tips: list,
             peace_active: bool, fist_count: int) -> None:

        h, w = frame.shape[:2]
        now  = time.time()

        # ── FPS rolling average ───────────────────────────────────────────────
        if cls._last_ts:
            cls._fps_buf.append(1.0 / max(now - cls._last_ts, 1e-6))
            if len(cls._fps_buf) > 30: cls._fps_buf.pop(0)
        cls._last_ts = now
        fps = sum(cls._fps_buf) / len(cls._fps_buf) if cls._fps_buf else 0.0

        # ── System stats ──────────────────────────────────────────────────────
        ram      = psutil.virtual_memory()
        cpu_pct  = psutil.cpu_percent(interval=None)
        ram_used = ram.used  / (1024**2)
        ram_tot  = ram.total / (1024**2)
        ram_pct  = ram.percent
        ts_str   = datetime.datetime.now().strftime("%H:%M:%S")
        date_str = datetime.datetime.now().strftime("%d/%m/%Y")
        os_str   = platform.system().upper()[:3]

        # ── Semi-transparent panel helpers ────────────────────────────────────
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

        # ══ TOP-LEFT — mode & filter ══════════════════════════════════════════
        panel(4, 4, 310, 115)
        cv2.rectangle(frame, (4,4), (310,115), cls.C_CYAN, 1)
        mode_str  = "3D-MESH" if proc.is_3d_mode else ("2D-BOWTIE" if is_bowtie else "2D-QUAD")
        face_str  = f"FACE {face_count}" if proc.face_mode else "FACE OFF"
        txt(f"MODE   {mode_str}",          14, 24,  cls.C_CYAN,   0.50, 1)
        txt(f"FILTER {proc.current_filter.upper()}", 14, 44, cls.C_WHITE, 0.50, 1)
        txt(f"HANDS  {len(all_tips)}  |  {face_str}", 14, 64, cls.C_TEAL,  0.45, 1)

        # active gestures
        gestures = []
        if peace_active:       gestures.append("✌ BLUR")
        if fist_count == 2:    gestures.append("✊✊ MODE")
        if fist_count == 1:    gestures.append("✊ FIST")
        g_str = "  ".join(gestures) if gestures else "—"
        txt(f"GESTURE {g_str}", 14, 84, cls.C_ORANGE, 0.45, 1)
        txt(f"NEXT   {proc.secondary_filter.upper()}", 14, 104, cls.C_DIM, 0.40, 1)

        # ══ TOP-RIGHT — system stats ══════════════════════════════════════════
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

        res_str = f"RES  {w}x{h}"
        txt(res_str, rx, 148, cls.C_DIM, 0.40, 1)

        # ══ CENTER-TOP — crosshair + artificial horizon ═══════════════════════
        cx, cy = w//2, h//2
        arm = 18; gap = 6
        col_ch = cls.C_GREEN
        # crosshair
        cv2.line(frame, (cx-arm-gap, cy), (cx-gap, cy), col_ch, 1)
        cv2.line(frame, (cx+gap, cy), (cx+arm+gap, cy), col_ch, 1)
        cv2.line(frame, (cx, cy-arm-gap), (cx, cy-gap), col_ch, 1)
        cv2.line(frame, (cx, cy+gap), (cx, cy+arm+gap), col_ch, 1)
        cv2.circle(frame, (cx, cy), 3, col_ch, -1)
        cv2.circle(frame, (cx, cy), arm+gap+4, col_ch, 1)

        # artificial horizon bar (static decoration)
        blen = 80
        cv2.line(frame, (cx-blen, cy-1), (cx-gap-4, cy-1), cls.C_YELLOW, 2)
        cv2.line(frame, (cx+gap+4, cy-1), (cx+blen, cy-1), cls.C_YELLOW, 2)
        txt("0°", cx+blen+4, cy+4, cls.C_YELLOW, 0.35, 1)

        # frame corner brackets
        brk = 20; bt = 2; bc = cls.C_GREEN
        for (px,py,sx,sy) in [(0,0,1,1),(w,0,-1,1),(0,h,1,-1),(w,h,-1,-1)]:
            cv2.line(frame,(px,py),(px+sx*brk,py),bc,bt)
            cv2.line(frame,(px,py),(px,py+sy*brk),bc,bt)

        # ══ BOTTOM-LEFT — hand fingertip coordinates ══════════════════════════
        if all_tips:
            hand_labels = ["L-HAND","R-HAND"]
            base_y = h - 10 - len(all_tips) * 75
            panel(4, base_y - 14, 220, h - 4)
            cv2.rectangle(frame, (4, base_y-14), (220, h-4), cls.C_CYAN, 1)
            for hi, tips in enumerate(all_tips):
                label = hand_labels[hi] if hi < 2 else f"HAND{hi}"
                txt(f"── {label} ──", 10, base_y + hi*75, cls.C_CYAN, 0.42, 1)
                tip_indices = [4, 8, 12, 16, 20]
                for fi, (tx, ty) in enumerate(tips):
                    fname = cls.FINGER_LABELS.get(tip_indices[fi], f"F{fi}")
                    col = cls.C_YELLOW if fi == 1 else cls.C_WHITE  # IDX highlight
                    txt(f"  {fname}  X:{tx:4d}  Y:{ty:4d}",
                        10, base_y + hi*75 + 14 + fi*12,
                        col, 0.37, 1)

        # ══ BOTTOM-CENTER — gesture legend ════════════════════════════════════
        legend = [
            ("PINCH",     "NEXT FILTER"),
            ("✌  PEACE",  "BLUR FRAME"),
            ("✊✊ 2-FIST", "TOGGLE MODE"),
            ("N/P",       "FILTER STEP"),
            ("F",         "FACE ON/OFF"),
            ("C",         "MODE TOGGLE"),
        ]
        lw = 230; lh = len(legend)*14 + 10
        lx = (w - lw) // 2; ly = h - lh - 6
        panel(lx, ly, lx+lw, ly+lh)
        cv2.rectangle(frame, (lx,ly), (lx+lw,ly+lh), cls.C_DIM, 1)
        for i,(gesture,action) in enumerate(legend):
            gy = ly + 12 + i*14
            txt(f"{gesture:<12} {action}", lx+6, gy, cls.C_DIM, 0.35, 1)

        # ══ SCAN LINE effect (subtle) ═════════════════════════════════════════
        for y_sl in range(0, h, 6):
            cv2.line(frame, (0, y_sl), (w, y_sl), (0,0,0), 1)
        # blend scanlines lightly
        ovl2 = frame.copy()
        cv2.addWeighted(ovl2, 0.92, frame, 0.08, 0, frame)


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineConfig:
    cam_index: int = 0
    frame_width: int = 960
    frame_height: int = 540
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

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        frame   = cv2.flip(frame, 1)
        frame   = cv2.resize(frame, (self.cfg.frame_width, self.cfg.frame_height))
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.detector.process(rgb)
        now     = time.time()

        all_tips    = []
        fist_count  = 0
        is_bowtie   = False
        peace_count = 0  # dua jari (peace/victory) → blur seluruh frame

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

        # ── Peace gesture → blur seluruh frame ────────────────────────────────
        if peace_count > 0:
            frame = cv2.GaussianBlur(frame, (31, 31), 0)
            cv2.putText(frame, "✌ BLUR MODE", (15, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 180), 2, cv2.LINE_AA)

        face_count = 0
        if self.face_mode:
            frame, face_count = self.face_proc.apply(frame, self.filters[self.current_filter])

        self._draw_hud(frame, is_bowtie, face_count, all_tips, peace_count > 0, fist_count)
        # Watermark — selalu terakhir, di atas semua layer
        self.watermark_ui.draw(frame)
        return frame

    def _draw_hud(self, frame, is_bowtie, face_count, all_tips=None, peace_active=False, fist_count=0):
        FPVHud.draw(frame, self, is_bowtie, face_count,
                    all_tips or [], peace_active, fist_count)

    def close(self):
        self.face_proc.close()
        self.detector.close()


# ══════════════════════════════════════════════════════════════════════════════
# MOUSE CALLBACK
# ══════════════════════════════════════════════════════════════════════════════

_watermark_ui_ref: Optional[WatermarkUI] = None

def _on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and _watermark_ui_ref:
        _watermark_ui_ref.handle_click(x, y)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    global _watermark_ui_ref
    cfg       = PipelineConfig()
    processor = PortalProcessor(cfg)
    _watermark_ui_ref = processor.watermark_ui

    cap = cv2.VideoCapture(cfg.cam_index)
    if not cap.isOpened():
        print("[ERROR] Kamera tidak terdeteksi!"); return

    win = "RetroLens Engine"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, _on_mouse)

    print("=== RetroLens Engine — Powered by Faisaldev ===")
    print("Q        : Quit | C : Toggle mode | N/P : Filter")
    print("F        : Toggle face filter | S : Screenshot")

    while True:
        ret, frame = cap.read()
        if not ret: break

        out = processor.process_frame(frame)
        cv2.imshow(win, out)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("c"):
            processor.is_3d_mode = not processor.is_3d_mode
        elif key == ord("n"):
            processor.cycle_filter(1)
        elif key == ord("p"):
            processor.cycle_filter(-1)
        elif key == ord("f"):
            processor.face_mode = not processor.face_mode
        elif key == ord("s"):
            fn = f"cap_{int(time.time())}.png"
            cv2.imwrite(fn, out); print(f"[SNAP] {fn}")
        elif key == 27:  # ESC tutup modal
            processor.watermark_ui.show_modal = False

    processor.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
