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


# ── Slider descriptor ────────────────────────────────────────────────────────

class SliderDef:
    """Defines a slider: label, min, max, attribute on SimulationState, format string."""
    def __init__(self, label, attr, vmin, vmax, step=0.01, fmt="{:.2f}"):
        self.label = label
        self.attr  = attr
        self.vmin  = vmin
        self.vmax  = vmax
        self.step  = step
        self.fmt   = fmt


# ── HUD ───────────────────────────────────────────────────────────────────────

class HUD:
    """
    Bioluminescent HUD for AquariumEngine.
    Call  hud.render(screen)  once per frame after 3D scene rendering.
    Aliran data tidak berubah — baca dari app.scene, app.camera, app.clock, app.sim.
    """

    # Slider definitions grouped by section
    FISH_SLIDERS = [
        SliderDef("FISH TARGET", "max_fish", 0, 16, step=1, fmt="{:.0f}"),
    ]
    WATER_SLIDERS = [
        SliderDef("WAVE AMPLITUDE", "wave_amplitude", 0.0, 0.15, step=0.005, fmt="{:.3f}"),
        SliderDef("WAVE FREQUENCY", "wave_frequency", 0.0, 4.0,  step=0.05,  fmt="{:.2f}"),
        SliderDef("WAVE SPEED",     "wave_speed",     0.0, 2.5,  step=0.05,  fmt="{:.2f}"),
    ]

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

        # Hamburger menu state
        self.menu_open = False
        self.hamburger_rect = None  # screen-space rect for click detection

        # Slider interaction state
        self._active_slider_idx = None  # which slider is being dragged (flat index)
        self._all_sliders = self.FISH_SLIDERS + self.WATER_SLIDERS
        self._slider_rects = {}  # idx → pg.Rect (screen-space track rects)

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
        self._draw_live_panel(hud)
        self._draw_object_panel(hud)
        self._draw_controls_panel(hud)
        self._draw_mode_pill(hud)
        self._draw_hamburger_menu(hud)

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

    # ── Hamburger menu (bottom-center) ────────────────────────────────────────

    def _draw_hamburger_menu(self, dst):
        """Draw the hamburger button and, if open, the settings panel above it."""
        BTN_W = 48
        BTN_H = 40
        btn_x = self.W // 2 - BTN_W // 2
        btn_y = self.H - self.PAD - BTN_H

        # ── Button ──
        btn = _surf(BTN_W, BTN_H)
        btn_col = GLOW_CYAN if not self.menu_open else GLOW_GREEN
        _filled(btn, (0, 0, BTN_W, BTN_H), (*SEA_DEEP[:3], 230), r=12)
        _outline(btn, (0, 0, BTN_W, BTN_H), (*btn_col[:3], 140), w=1, r=12)

        # Hamburger icon (3 lines) or X when open
        cx = BTN_W // 2
        cy = BTN_H // 2
        if self.menu_open:
            # X icon
            pg.draw.line(btn, btn_col, (cx - 7, cy - 7), (cx + 7, cy + 7), 2)
            pg.draw.line(btn, btn_col, (cx + 7, cy - 7), (cx - 7, cy + 7), 2)
        else:
            # Three horizontal lines
            for dy in (-8, 0, 8):
                pg.draw.line(btn, btn_col, (cx - 10, cy + dy), (cx + 10, cy + dy), 2)

        dst.blit(btn, (btn_x, btn_y))

        # Store button rect for click detection (screen-space, pre-flip)
        self.hamburger_rect = pg.Rect(btn_x, btn_y, BTN_W, BTN_H)

        # ── Settings panel (if open) ──
        if self.menu_open:
            self._draw_settings_panel(dst, btn_x, btn_y, BTN_W)

    def _draw_settings_panel(self, dst, btn_x, btn_y, btn_w):
        """Draw the settings panel floating above the hamburger button."""
        PANEL_W = 340
        SLIDER_H = 46   # height per slider row
        SECTION_GAP = 14
        SEPARATOR_H = 14

        # Calculate panel height
        fish_rows   = len(self.FISH_SLIDERS)
        water_rows  = len(self.WATER_SLIDERS)
        content_h   = (self.INNER +                       # top pad
                       FS_XS + 8 +                        # FISH header
                       fish_rows * SLIDER_H +             # fish sliders
                       SEPARATOR_H + SECTION_GAP +        # separator
                       FS_XS + 8 +                        # WATER header
                       water_rows * SLIDER_H +            # water sliders
                       self.INNER)                         # bottom pad

        PANEL_H = content_h
        panel_x = self.W // 2 - PANEL_W // 2
        panel_y = btn_y - PANEL_H - 8

        panel = _surf(PANEL_W, PANEL_H)
        _filled(panel, (0, 0, PANEL_W, PANEL_H), (*SEA_DEEP[:3], 235), r=14)
        _outline(panel, (0, 0, PANEL_W, PANEL_H), (*GLOW_CYAN[:3], 60), w=1, r=14)

        # Subtle glow line at bottom
        for i, a in enumerate([40, 18, 6]):
            pg.draw.line(panel, (*GLOW_CYAN[:3], a),
                         (14, PANEL_H - 1 - i), (PANEL_W - 14, PANEL_H - 1 - i))

        ry = self.INNER
        slider_flat_idx = 0

        # ── Section: FISH ──
        hdr = self.f_xs.render("FISH", True, GLOW_CYAN)
        panel.blit(hdr, (self.INNER, ry))
        ry += FS_XS + 4
        _hline(panel, self.INNER, PANEL_W - self.INNER, ry, (*GLOW_CYAN[:3], 35))
        ry += 4

        for sdef in self.FISH_SLIDERS:
            self._draw_slider(panel, sdef, slider_flat_idx,
                              self.INNER, ry, PANEL_W - self.INNER * 2,
                              panel_x, panel_y)
            slider_flat_idx += 1
            ry += SLIDER_H

        # Spacer antar section (tanpa separator line)
        ry += SEPARATOR_H

        # ── Section: WATER SURFACE ──
        hdr2 = self.f_xs.render("WATER SURFACE", True, GLOW_CYAN)
        panel.blit(hdr2, (self.INNER, ry))
        ry += FS_XS + 4
        _hline(panel, self.INNER, PANEL_W - self.INNER, ry, (*GLOW_CYAN[:3], 35))
        ry += 4

        for sdef in self.WATER_SLIDERS:
            self._draw_slider(panel, sdef, slider_flat_idx,
                              self.INNER, ry, PANEL_W - self.INNER * 2,
                              panel_x, panel_y)
            slider_flat_idx += 1
            ry += SLIDER_H

        dst.blit(panel, (panel_x, panel_y))

    def _draw_slider(self, panel, sdef, flat_idx, x, y, width, panel_x, panel_y):
        """Draw a single slider on the panel surface."""
        sim = self.app.sim
        value = getattr(sim, sdef.attr)

        # Label + value
        label_surf = self.f_xs.render(sdef.label, True, TEXT_MID)
        value_str  = sdef.fmt.format(value)
        value_surf = self.f_s.render(value_str, True, TEXT_BRIGHT)
        panel.blit(label_surf, (x, y))
        panel.blit(value_surf, (x + width - value_surf.get_width(), y))

        # Track
        track_y = y + FS_XS + 8
        track_h = 6
        track_x = x
        track_w = width

        # Track background
        _filled(panel, (track_x, track_y, track_w, track_h), (*TEXT_DIM[:3], 100), r=3)

        # Filled portion
        frac = (value - sdef.vmin) / max(0.001, sdef.vmax - sdef.vmin)
        frac = max(0.0, min(1.0, frac))
        fill_w = int(frac * track_w)
        if fill_w > 0:
            _filled(panel, (track_x, track_y, fill_w, track_h), (*GLOW_CYAN[:3], 80), r=3)

        # Handle
        handle_x = track_x + int(frac * track_w)
        handle_y = track_y + track_h // 2

        # Glow ring
        _dot(panel, handle_x, handle_y, 8, (*GLOW_GREEN[:3], 60))
        _dot(panel, handle_x, handle_y, 6, GLOW_GREEN)
        _outline(panel, (handle_x - 7, handle_y - 7, 14, 14), (*GLOW_CYAN[:3], 150), w=1, r=7)

        # Store screen-space track rect for click detection
        self._slider_rects[flat_idx] = pg.Rect(
            panel_x + track_x, panel_y + track_y, track_w, track_h + 16
        )

    # ── Event handling ────────────────────────────────────────────────────────

    def _pos_to_hud(self, pos):
        """Convert mouse position, accounting for Y-flip."""
        x, y = pos
        return x, y

    def _screen_to_hud_y(self, screen_y):
        """Convert screen Y to HUD Y (pre-flip coordinate)."""
        return self.H - screen_y

    def _update_slider_from_mouse(self, flat_idx, mouse_x):
        """Update the simulation state from a slider drag."""
        rect = self._slider_rects.get(flat_idx)
        if rect is None:
            return

        sdef = self._all_sliders[flat_idx]
        rel_x = mouse_x - rect.x
        rel_x = max(0, min(rel_x, rect.width))
        frac = rel_x / max(1, rect.width)
        raw_value = sdef.vmin + frac * (sdef.vmax - sdef.vmin)

        # Snap to step
        if sdef.step >= 1:
            raw_value = round(raw_value)
        else:
            raw_value = round(raw_value / sdef.step) * sdef.step

        raw_value = max(sdef.vmin, min(sdef.vmax, raw_value))
        setattr(self.app.sim, sdef.attr, raw_value)

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            hud_y = self._screen_to_hud_y(my)

            # Check hamburger button
            # Be tolerant to Y-space mismatch: depending on render path, events may
            # already be in HUD space or still in screen-top-left space.
            if self.hamburger_rect and (
                self.hamburger_rect.collidepoint(mx, hud_y) or
                self.hamburger_rect.collidepoint(mx, my)
            ):
                self.menu_open = not self.menu_open
                return

            # Check sliders (only if menu is open)
            if self.menu_open:
                for idx, rect in self._slider_rects.items():
                    # Expand hit area vertically
                    expanded = pg.Rect(rect.x, rect.y - 8, rect.width, rect.height + 16)
                    if expanded.collidepoint(mx, hud_y) or expanded.collidepoint(mx, my):
                        self._active_slider_idx = idx
                        self._update_slider_from_mouse(idx, mx)
                        return

        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self._active_slider_idx = None

        elif event.type == pg.MOUSEMOTION and self._active_slider_idx is not None:
            mx, my = event.pos
            self._update_slider_from_mouse(self._active_slider_idx, mx)

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


# ── Scene interaction & updates ─────────────────────────────────────────────
    def is_over(self, pos):
        hud_rect = pg.Rect(0, 0, 220, pg.display.get_surface().get_height())
        return hud_rect.collidepoint(pos)