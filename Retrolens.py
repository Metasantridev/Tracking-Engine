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

        all_tips   = []
        fist_count = 0
        is_bowtie  = False

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

        face_count = 0
        if self.face_mode:
            frame, face_count = self.face_proc.apply(frame, self.filters[self.current_filter])

        self._draw_hud(frame, is_bowtie, face_count)
        # Watermark — selalu terakhir, di atas semua layer
        self.watermark_ui.draw(frame)
        return frame

    def _draw_hud(self, frame, is_bowtie, face_count):
        mode_str = "3D Mesh" if self.is_3d_mode else ("2D Bowtie" if is_bowtie else "2D Quad")
        face_str = f"ON ({face_count})" if self.face_mode else "OFF"
        cv2.putText(frame, f"MODE: {mode_str} [C / Dual Fist]", (15,25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,255,255), 2)
        cv2.putText(frame, f"FILTER: {self.current_filter.upper()} [N/P/Pinch]", (15,50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 2)
        cv2.putText(frame, f"FACE: {face_str} [F]", (15,75), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,220,255), 2)

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
