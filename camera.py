"""
Camera - Orbit (default) + FPS mode.

ORBIT MODE (default):
  RMB drag      - rotate
  MMB drag      - pan
  Scroll wheel  - zoom

FPS MODE (TAB):
  WASD + Q/E   - move
  Mouse move   - look
"""

import pygame as pg
from pyglm import glm
import math

FOV        = 60.0
NEAR       = 0.05
FAR        = 200.0
ORBIT_SENS = 0.30
PAN_SENS   = 0.006
FPS_SENS   = 0.15


class Camera:
    def __init__(self, app):
        self.app = app
        self.aspect_ratio = app.WIN_SIZE[0] / app.WIN_SIZE[1]
        self.WIN_CX = app.WIN_SIZE[0] // 2
        self.WIN_CY = app.WIN_SIZE[1] // 2

        # ── Orbit state ───────────────────────────────────────────────
        self.use_orbit    = True
        self.orbit_target = glm.vec3(0.0, 1.5, 0.0)
        self.orbit_radius = 14.0
        self.orbit_yaw    = 30.0
        self.orbit_pitch  = 20.0

        # ── FPS state (will be synced from orbit on first toggle) ─────
        self.fps_pos   = glm.vec3(0.0, 4.0, 14.0)
        self.fps_yaw   = 180.0
        self.fps_pitch = -10.0

        # ── Shared vectors ────────────────────────────────────────────
        self.position = glm.vec3(0)
        self.forward  = glm.vec3(0, 0, -1)
        self.up       = glm.vec3(0, 1, 0)
        self.right    = glm.vec3(1, 0, 0)
        self.world_up = glm.vec3(0, 1, 0)

        # ── Mouse drag state (orbit only) ─────────────────────────────
        self._rmb = False
        self._mmb = False

        # ── FPS warp flag ─────────────────────────────────────────────
        self._fps_warped = False

        self.m_proj = self._make_proj()
        self._update_orbit()
        self.m_view = self._make_view()

    # ─────────────────────────────────────────────────────────────────
    #  Event handler
    # ─────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 4: self._zoom(-1.0); return
            if event.button == 5: self._zoom(1.0);  return
            if self.use_orbit:
                if event.button == 3: self._rmb = True
                if event.button == 2: self._mmb = True

        elif event.type == pg.MOUSEBUTTONUP:
            if self.use_orbit:
                if event.button == 3: self._rmb = False
                if event.button == 2: self._mmb = False

        elif event.type == pg.MOUSEMOTION:
            dx, dy = event.rel
            if self.use_orbit:
                if self._rmb:
                    self.orbit_yaw   += dx * ORBIT_SENS
                    self.orbit_pitch -= dy * ORBIT_SENS
                    self.orbit_pitch  = max(-85.0, min(85.0, self.orbit_pitch))
                elif self._mmb:
                    scale = PAN_SENS * self.orbit_radius * 0.1
                    self.orbit_target -= self.right * (dx * scale)
                    self.orbit_target += self.up    * (dy * scale)
            else:
                # FPS: skip the warp event, process all others
                if self._fps_warped:
                    self._fps_warped = False
                    return
                self.fps_yaw   += dx * FPS_SENS
                self.fps_pitch -= dy * FPS_SENS
                self.fps_pitch  = max(-89.0, min(89.0, self.fps_pitch))
                # Warp back to center to avoid hitting window edge
                pg.mouse.set_pos(self.WIN_CX, self.WIN_CY)
                self._fps_warped = True

    # ─────────────────────────────────────────────────────────────────
    #  Per-frame update
    # ─────────────────────────────────────────────────────────────────
    def update(self):
        if self.use_orbit:
            self._update_orbit()
        else:
            self._fps_keyboard()
            self._update_fps_vectors()
        self.m_view = self._make_view()

    # ─────────────────────────────────────────────────────────────────
    #  Toggle orbit <-> FPS  — KEY FIX: sync position from orbit
    # ─────────────────────────────────────────────────────────────────
    def toggle_mode(self):
        self.use_orbit = not self.use_orbit

        if self.use_orbit:
            # Back to orbit — free mouse
            pg.mouse.set_visible(True)
            pg.event.set_grab(False)
            self._rmb = False
            self._mmb = False
            self._fps_warped = False
        else:
            # ── Copy current orbit camera position & look direction ────
            # This prevents the black screen jump when switching modes
            self.fps_pos = glm.vec3(self.position)   # where orbit cam is NOW

            # Derive yaw & pitch from current forward vector
            fwd = self.forward
            self.fps_pitch = math.degrees(math.asin(
                max(-1.0, min(1.0, float(fwd.y)))
            ))
            self.fps_yaw = math.degrees(math.atan2(
                float(fwd.z), float(fwd.x)
            ))

            # Hide cursor, grab, center
            pg.mouse.set_visible(False)
            pg.event.set_grab(True)
            pg.mouse.set_pos(self.WIN_CX, self.WIN_CY)
            self._fps_warped = True

    def reset(self):
        self.orbit_yaw    = 30.0
        self.orbit_pitch  = 20.0
        self.orbit_radius = 14.0
        self.orbit_target = glm.vec3(0.0, 1.5, 0.0)
        self.fps_pos      = glm.vec3(0.0, 4.0, 14.0)
        self.fps_yaw      = 180.0
        self.fps_pitch    = -10.0
        self._rmb = False
        self._mmb = False
        self._fps_warped = False

    # ─────────────────────────────────────────────────────────────────
    #  Orbit internals
    # ─────────────────────────────────────────────────────────────────
    def _update_orbit(self):
        yaw   = glm.radians(self.orbit_yaw)
        pitch = glm.radians(self.orbit_pitch)
        x = self.orbit_radius * glm.cos(pitch) * glm.cos(yaw)
        y = self.orbit_radius * glm.sin(pitch)
        z = self.orbit_radius * glm.cos(pitch) * glm.sin(yaw)
        self.position = self.orbit_target + glm.vec3(x, y, z)
        self.forward  = glm.normalize(self.orbit_target - self.position)
        self.right    = glm.normalize(glm.cross(self.forward, self.world_up))
        self.up       = glm.normalize(glm.cross(self.right, self.forward))

    def _zoom(self, delta):
        if self.use_orbit:
            self.orbit_radius = max(2.0, min(60.0, self.orbit_radius + delta))
        else:
            self.fps_pos += self.forward * (-delta * 0.8)

    # ─────────────────────────────────────────────────────────────────
    #  FPS internals
    # ─────────────────────────────────────────────────────────────────
    def _fps_keyboard(self):
        keys  = pg.key.get_pressed()
        speed = 0.04 * self.app.delta_time
        if keys[pg.K_LSHIFT] or keys[pg.K_RSHIFT]: speed *= 3.0
        if keys[pg.K_LCTRL]  or keys[pg.K_RCTRL]:  speed *= 0.3

        if keys[pg.K_w]: self.fps_pos += self.forward * speed
        if keys[pg.K_s]: self.fps_pos -= self.forward * speed
        if keys[pg.K_a]: self.fps_pos -= self.right   * speed
        if keys[pg.K_d]: self.fps_pos += self.right   * speed
        if keys[pg.K_q]: self.fps_pos -= self.up      * speed
        if keys[pg.K_e]: self.fps_pos += self.up      * speed

    def _update_fps_vectors(self):
        yaw   = math.radians(self.fps_yaw)
        pitch = math.radians(self.fps_pitch)
        self.position = self.fps_pos
        self.forward  = glm.normalize(glm.vec3(
            math.cos(yaw) * math.cos(pitch),
            math.sin(pitch),
            math.sin(yaw) * math.cos(pitch),
        ))
        self.right = glm.normalize(glm.cross(self.forward, self.world_up))
        self.up    = glm.normalize(glm.cross(self.right, self.forward))

    # ─────────────────────────────────────────────────────────────────
    #  Matrices
    # ─────────────────────────────────────────────────────────────────
    def _make_view(self):
        return glm.lookAt(self.position, self.position + self.forward, self.up)

    def _make_proj(self):
        return glm.perspective(glm.radians(FOV), self.aspect_ratio, NEAR, FAR)