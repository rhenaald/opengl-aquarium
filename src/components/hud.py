"""
HUD Overlay — Aquarium 3D
Aesthetic: Deep-sea bioluminescent. Dark navy base, glowing cyan accents,
           frosted-glass panels, pulse animation on live counters.

Dependencies (all bundled with pygame 2.x — no extra installs):
  - pygame.gfxdraw  : anti-aliased circles
  - pygame.font     : font rendering
"""

import math
import pygame as pg
import pygame.gfxdraw as gfxdraw
from collections import Counter


# ── Palette ───────────────────────────────────────────────────────────────────
SEA_DEEP    = (4,   10,  22,  210)
GLOW_CYAN   = (0,   210, 200, 255)
GLOW_WARM   = (255, 165,  60, 255)
GLOW_GREEN  = (60,  230, 140, 255)
TEXT_BRIGHT = (210, 240, 238, 255)
TEXT_MID    = (110, 160, 155, 255)
TEXT_DIM    = (50,   80,  78, 255)
DIVIDER     = (0,   180, 170,  45)
BADGE_FILL  = (0,   210, 200,  22)

FS_XS = 11
FS_S  = 13
FS_M  = 15


# ── Helpers ───────────────────────────────────────────────────────────────────

def _surf(w, h):
    s = pg.Surface((w, h), pg.SRCALPHA)
    s.fill((0, 0, 0, 0))
    return s

def _filled(surf, rect, color, r=0):
    pg.draw.rect(surf, color, rect, border_radius=r)

def _outline(surf, rect, color, w=1, r=0):
    pg.draw.rect(surf, color, rect, width=w, border_radius=r)

def _dot(surf, cx, cy, radius, color):
    gfxdraw.aacircle(surf, int(cx), int(cy), radius, color)
    gfxdraw.filled_circle(surf, int(cx), int(cy), radius, color)

def _hline(surf, x0, x1, y, color):
    gfxdraw.line(surf, int(x0), int(y), int(x1), int(y), color)

def _panel(surf, rect, radius=10):
    _filled(surf, rect, SEA_DEEP, r=radius)
    _outline(surf, rect, DIVIDER, w=1, r=radius)


# ── HUD ───────────────────────────────────────────────────────────────────────

class HUD:
    """
    Bioluminescent HUD for AquariumEngine.
    Call  hud.render(screen)  once per frame after 3D scene rendering.
    Aliran data tidak berubah — baca dari app.scene, app.camera, app.clock, app.sim.
    """

    def __init__(self, app):
        self.app = app
        pg.font.init()

        mono      = pg.font.match_font("consolas,couriernew,dejavusansmono,monospace")
        self.f_xs = pg.font.Font(mono, FS_XS)
        self.f_s  = pg.font.Font(mono, FS_S)
        self.f_m  = pg.font.Font(mono, FS_M)

        self.W, self.H = app.WIN_SIZE
        self.PAD   = 16
        self.INNER = 12
        self.GAP   = 5

        self.slider_min = 0
        self.slider_max = 16
        self.slider_dragging = False
        self.slider_value = self.app.sim.max_fish
        self.slider_rect = None

        self._tick     = 0.0
        self._obj_info = None

    # ── Data ─────────────────────────────────────────────────────────────────

    def _collect_objects(self):
        counts = Counter()
        for obj in self.app.scene.objects:
            counts[type(obj).__name__] += 1
        return list(counts.items())

    # ── Entry point ───────────────────────────────────────────────────────────

    def render(self, screen):
        self._obj_info = self._collect_objects()

        self._tick += 0.04

        hud = _surf(self.W, self.H)
        self._draw_topbar(hud)
        self._draw_fish_slider(hud)
        self._draw_live_panel(hud)
        self._draw_object_panel(hud)
        self._draw_controls_panel(hud)
        self._draw_mode_pill(hud)

        # Flip Y — kompensasi OpenGL (origin bawah-kiri) vs Pygame (origin atas-kiri)
        hud = pg.transform.flip(hud, False, True)
        screen.blit(hud, (0, 0))

    # ── Top bar ───────────────────────────────────────────────────────────────

    def _draw_topbar(self, dst):
        H   = 34
        bar = _surf(self.W, H)
        _filled(bar, (0, 0, self.W, H), (4, 10, 22, 205))

        # Glowing bottom edge
        for i, a in enumerate([55, 25, 8]):
            pg.draw.line(bar, (*GLOW_CYAN[:3], a),
                         (0, H - 1 - i), (self.W, H - 1 - i))

        # Left: title
        t = self.f_m.render("AQUARIUM  3D", True, GLOW_CYAN)
        bar.blit(t, (self.PAD, (H - t.get_height()) // 2))

        # Centre: mode
        cam  = self.app.camera
        col  = GLOW_WARM if cam.use_orbit else GLOW_GREEN
        ms   = self.f_m.render("ORBIT MODE" if cam.use_orbit else "FREE CAM", True, col)
        mx   = self.W // 2 - ms.get_width() // 2
        bar.blit(ms, (mx, (H - ms.get_height()) // 2))
        for ox in (-10, ms.get_width() + 10):
            _dot(bar, mx + ox, H // 2, 2, (*col[:3], 170))

        # Right: FPS
        fps = self.f_m.render(f"{int(self.app.clock.get_fps()):>3} FPS", True, TEXT_BRIGHT)
        bar.blit(fps, (self.W - self.PAD - fps.get_width(), (H - fps.get_height()) // 2))

        dst.blit(bar, (0, 0))

    # ── Live counters (top-left, under bar) ───────────────────────────────────

    def _draw_live_panel(self, dst):
        scene    = self.app.scene
        fish_n   = len(scene.fish)    if hasattr(scene, 'fish')    else 0
        bubble_n = len(scene.bubbles) if hasattr(scene, 'bubbles') else 0
        paused   = self.app.sim.paused if hasattr(self.app, 'sim') else False

        ROW_H   = FS_S + self.GAP + 4
        PANEL_W = 162
        PANEL_H = self.INNER * 2 + FS_XS + 10 + 2 * ROW_H

        panel = _surf(PANEL_W, PANEL_H)
        _panel(panel, (0, 0, PANEL_W, PANEL_H), radius=10)

        # Status row
        pulse = 0.5 + 0.5 * math.sin(self._tick * 2.6)
        if paused:
            s_col, s_txt = (255, 140, 60), "PAUSED"
            dot_a        = 200
        else:
            s_col, s_txt = (60, 220, 140), "LIVE"
            dot_a        = int(160 + 95 * pulse)

        _dot(panel, self.INNER + 4, self.INNER + FS_XS // 2 + 2, 3, (*s_col, dot_a))
        st = self.f_xs.render(s_txt, True, s_col)
        panel.blit(st, (self.INNER + 14, self.INNER))

        ry = self.INNER + FS_XS + 8
        _hline(panel, self.INNER, PANEL_W - self.INNER, ry - 3, (*GLOW_CYAN[:3], 30))

        for label, count, col in [
            ("FISH",    fish_n,   (60,  200, 140)),
            ("BUBBLES", bubble_n, (80,  180, 255)),
        ]:
            lb = self.f_xs.render(label, True, TEXT_MID)
            vl = self.f_s.render(str(count), True, (*col, 255))
            panel.blit(lb, (self.INNER, ry))
            panel.blit(vl, (PANEL_W - self.INNER - vl.get_width(), ry - 1))
            ry += ROW_H

        dst.blit(panel, (self.PAD, 34 + 8))

    # ── Scene objects (bottom-left) ───────────────────────────────────────────

    def _draw_object_panel(self, dst):
        ROW_H   = FS_S + self.GAP + 3
        PANEL_W = 228
        PANEL_H = self.INNER * 2 + FS_XS + 14 + len(self._obj_info) * ROW_H + 22

        panel = _surf(PANEL_W, PANEL_H)
        _panel(panel, (0, 0, PANEL_W, PANEL_H), radius=12)

        hdr = self.f_xs.render("SCENE OBJECTS", True, GLOW_CYAN)
        panel.blit(hdr, (self.INNER, self.INNER))

        dy = self.INNER + FS_XS + 7
        _hline(panel, self.INNER, PANEL_W - self.INNER, dy,     (*GLOW_CYAN[:3], 40))
        _hline(panel, self.INNER, PANEL_W - self.INNER, dy + 1, (*GLOW_CYAN[:3], 12))

        ry      = dy + 10
        total   = 0
        palette = [
            (0, 210, 200), (60, 230, 140), (255, 165, 60),
            (80, 160, 255), (200, 100, 255), (255, 100, 140),
        ]

        for i, (name, count) in enumerate(self._obj_info):
            total += count
            dc = palette[i % len(palette)]
            _dot(panel, self.INNER + 5, ry + FS_S // 2, 3, (*dc, 215))

            lb = self.f_s.render(name, True, TEXT_MID)
            ct = self.f_s.render(f"×{count}", True, TEXT_BRIGHT)
            panel.blit(lb, (self.INNER + 16, ry))
            panel.blit(ct, (PANEL_W - self.INNER - ct.get_width(), ry))
            ry += ROW_H

        # Total
        _hline(panel, self.INNER, PANEL_W - self.INNER, ry + 3, (*GLOW_CYAN[:3], 35))
        tl = self.f_xs.render("TOTAL", True, TEXT_DIM)
        tv = self.f_s.render(str(total), True, GLOW_CYAN)
        panel.blit(tl, (self.INNER + 16, ry + 7))
        panel.blit(tv, (PANEL_W - self.INNER - tv.get_width(), ry + 6))

        dst.blit(panel, (self.PAD, self.H - self.PAD - PANEL_H))

    # ── Controls (bottom-right) ───────────────────────────────────────────────

    def _draw_controls_panel(self, dst):
        cam = self.app.camera

        if cam.use_orbit:
            binds = [
                ("RMB",    "Orbit rotate"),
                ("SCROLL", "Zoom"),
                ("MMB",    "Pan"),
                ("TAB",    "Free Cam"),
                ("SPACE",  "Pause / Play"),
                ("B",      "Spawn bubble"),
                ("F",      "Spawn fish"),
                ("ESC",    "Quit"),
            ]
        else:
            binds = [
                ("WASD",   "Move"),
                ("Q / E",  "Down / Up"),
                ("MOUSE",  "Look"),
                ("SHIFT",  "Fast"),
                ("TAB",    "Orbit mode"),
                ("SPACE",  "Pause / Play"),
                ("B",      "Spawn bubble"),
                ("F",      "Spawn fish"),
                ("DRAG",   "Adjust fish count"),
                ("ESC",    "Quit"),
            ]

        ROW_H   = FS_XS + self.GAP + 4
        PANEL_W = 240
        PANEL_H = self.INNER * 2 + FS_XS + 14 + len(binds) * ROW_H

        panel = _surf(PANEL_W, PANEL_H)
        _panel(panel, (0, 0, PANEL_W, PANEL_H), radius=12)

        hdr = self.f_xs.render("CONTROLS", True, GLOW_CYAN)
        panel.blit(hdr, (self.INNER, self.INNER))

        dy = self.INNER + FS_XS + 7
        _hline(panel, self.INNER, PANEL_W - self.INNER, dy,     (*GLOW_CYAN[:3], 40))
        _hline(panel, self.INNER, PANEL_W - self.INNER, dy + 1, (*GLOW_CYAN[:3], 12))

        ry = dy + 10
        for key, action in binds:
            ks  = self.f_xs.render(key, True, GLOW_CYAN)
            kw  = ks.get_width() + 12
            kh  = FS_XS + 6
            _filled(panel, (self.INNER, ry - 1, kw, kh), BADGE_FILL, r=4)
            _outline(panel, (self.INNER, ry - 1, kw, kh), (*GLOW_CYAN[:3], 65), w=1, r=4)
            panel.blit(ks, (self.INNER + 6, ry + 2))

            ac = self.f_xs.render(action, True, TEXT_MID)
            panel.blit(ac, (self.INNER + kw + 8, ry + 2))
            ry += ROW_H

        dst.blit(panel, (self.W - self.PAD - PANEL_W, self.H - self.PAD - PANEL_H))

    # ── Fish target slider (center bottom on screen) ──────────────────────────

    def _draw_fish_slider(self, dst):
        target = self.app.sim.max_fish
        self.slider_value = target

        PANEL_W = 360
        PANEL_H = 86
        x = self.W // 2 - PANEL_W // 2
        y = self.H - self.PAD - PANEL_H

        panel = _surf(PANEL_W, PANEL_H)
        _panel(panel, (0, 0, PANEL_W, PANEL_H), radius=14)

        hdr = self.f_s.render("FISH TARGET", True, GLOW_CYAN)
        panel.blit(hdr, (self.INNER, self.INNER))

        # Slider track
        track_y = self.INNER + FS_M + 16
        track_h = 6
        track_x = self.INNER
        track_w = PANEL_W - self.INNER * 2
        _filled(panel, (track_x, track_y, track_w, track_h), (*TEXT_DIM[:3], 120), r=3)

        # Handle
        handle_x = track_x + int((target - self.slider_min) / max(1, self.slider_max - self.slider_min) * track_w)
        handle_y = track_y + track_h // 2
        _dot(panel, handle_x, handle_y, 9, GLOW_GREEN)
        _outline(panel, (handle_x - 10, handle_y - 10, 20, 20), (*GLOW_CYAN[:3], 180), w=2, r=10)

        # Labels
        value_label = self.f_m.render(f"{target} fish", True, TEXT_BRIGHT)
        panel.blit(value_label, (self.INNER, track_y + track_h + 12))

        min_label = self.f_xs.render(str(self.slider_min), True, TEXT_MID)
        max_label = self.f_xs.render(str(self.slider_max), True, TEXT_MID)
        panel.blit(min_label, (track_x, track_y + track_h + 12))
        panel.blit(max_label, (track_x + track_w - max_label.get_width(), track_y + track_h + 12))

        self.slider_rect = pg.Rect(x + track_x, y + track_y, track_w, track_h)
        self.slider_handle_rect = pg.Rect(x + handle_x - 12, y + handle_y - 12, 24, 24)

        dst.blit(panel, (x, y))

    def _pos_to_hud(self, pos):
        x, y = pos
        return x, y

    def _update_slider_value(self, mouse_x):
        if self.slider_rect is None:
            return

        rel_x = mouse_x - self.slider_rect.x
        rel_x = max(0, min(rel_x, self.slider_rect.width))
        frac = rel_x / max(1, self.slider_rect.width)
        value = round(self.slider_min + frac * (self.slider_max - self.slider_min))
        self.app.sim.max_fish = value
        self.slider_value = value

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            hx, hy = self._pos_to_hud(event.pos)
            if self.slider_rect and self.slider_rect.collidepoint(hx, hy):
                self.slider_dragging = True
                self._update_slider_value(hx)

        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.slider_dragging = False

        elif event.type == pg.MOUSEMOTION and self.slider_dragging:
            hx, hy = self._pos_to_hud(event.pos)
            self._update_slider_value(hx)

    # ── Mode pill (top-right, under bar) ──────────────────────────────────────

    def _draw_mode_pill(self, dst):
        cam   = self.app.camera
        col   = GLOW_WARM if cam.use_orbit else GLOW_GREEN
        label = self.f_s.render("● ORBIT" if cam.use_orbit else "● FREE CAM", True, col)

        PW = label.get_width() + 26
        PH = label.get_height() + 10
        px = self.W - self.PAD - PW
        py = 34 + 8

        pill = _surf(PW, PH)
        _filled(pill, (0, 0, PW, PH), (*col[:3], 20), r=PH // 2)
        _outline(pill, (0, 0, PW, PH), (*col[:3], 85), w=1, r=PH // 2)
        pill.blit(label, (13, 5))
        dst.blit(pill, (px, py))