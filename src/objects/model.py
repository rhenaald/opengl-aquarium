"""
model.py - All renderable model classes for the aquarium.

Hierarchy:
  BaseModel          - common init, matrix helpers, uniform upload
  ├── SolidModel     - opaque Phong shading (rocks, coral base, etc.)
  ├── GlassPanel     - semi-transparent tank wall
  ├── GlueSeam       - translucent silicone-like corner joint
  ├── SandFloor      - sand with caustic
  ├── Seaweed        - animated swaying cylinder
  ├── Fish           - animated swimming ellipsoid
  └── Bubble         - transparent rising sphere
"""

import random
import math
import pygame as pg
from pyglm import glm


# ─────────────────────────────────────────────────────────────────────────────
#  Base
# ─────────────────────────────────────────────────────────────────────────────

class BaseModel:
    def __init__(self, app, vao_name, pos=(0,0,0), rot=(0,0,0), scale=(1,1,1)):
        self.app     = app
        self.camera  = app.camera
        self.light   = app.light
        self.sim     = app.sim
        self.vao     = app.mesh.vao.vaos[vao_name]
        self.program = self.vao.program

        self.pos   = glm.vec3(pos)
        self.rot   = glm.vec3([glm.radians(a) for a in rot])
        self.scale = glm.vec3(scale)
        self.m_model = self._make_model_matrix()

        self._init_light_uniforms()

    def _make_model_matrix(self):
        m = glm.mat4()
        m = glm.translate(m, self.pos)
        m = glm.rotate(m, self.rot.z, glm.vec3(0,0,1))
        m = glm.rotate(m, self.rot.y, glm.vec3(0,1,0))
        m = glm.rotate(m, self.rot.x, glm.vec3(1,0,0))
        m = glm.scale(m, self.scale)
        return m

    def _init_light_uniforms(self):
        p = self.program
        _set(p, 'm_proj',          self.camera.m_proj)
        _set(p, 'light.position',  self.light.position)
        _set(p, 'light.Ia',        self.light.Ia)
        _set(p, 'light.Id',        self.light.Id)
        _set(p, 'light.Is',        self.light.Is)

    def _upload_common(self):
        p = self.program
        _set(p, 'm_view',       self.camera.m_view)
        _set(p, 'm_model',      self.m_model)
        _set(p, 'cam_pos',      self.camera.position)
        _set(p, 'u_time',       self.app.time)
        # Lighting may change dynamically
        _set(p, 'light.Ia',     self.light.Ia)
        _set(p, 'light.Id',     self.light.Id)
        _set(p, 'light.Is',     self.light.Is)
        # Water color / fog
        wc = self.sim.water_color
        _set(p, 'u_water_color', glm.vec3(wc))
        _set(p, 'u_fog_density', 1.0)
        _set(p, 'u_sun_pos', glm.vec3(0.0, 9.0, -2.5))
        _set(p, 'u_sun_dir', glm.normalize(glm.vec3(0.0, -1.0, 0.22)))
        _set(p, 'u_sun_cutoff', math.cos(math.radians(34.0)))
        _set(p, 'u_water_surface_y', 6.0)
        _set(p, 'u_caustic_strength', 0.35 * self.sim.light_intensity)
        _set(p, 'u_caustic_speed', self.sim.caustic_speed)

    def update(self, dt, t): pass

    def render(self):
        self._upload_common()
        self.vao.render()


# ─────────────────────────────────────────────────────────────────────────────
#  Solid opaque model (rocks, coral, generic cube)
# ─────────────────────────────────────────────────────────────────────────────

class SolidModel(BaseModel):
    def __init__(self, app, vao_name='solid_cube',
                 pos=(0,0,0), rot=(0,0,0), scale=(1,1,1), color=(1,1,1)):
        super().__init__(app, vao_name, pos, rot, scale)
        self.color = glm.vec3(color)

    def render(self):
        self._upload_common()
        _set(self.program, 'u_color',    self.color)
        _set(self.program, 'u_wave_amp', 0.0)
        self.vao.render()


# ─────────────────────────────────────────────────────────────────────────────
#  Glass panel (tank wall)
# ─────────────────────────────────────────────────────────────────────────────

class GlassPanel(BaseModel):
    def __init__(self, app, pos=(0,0,0), rot=(0,0,0), scale=(1,1,1),
                 tint=(0.55, 0.75, 0.80), alpha=0.10, vao_name='tank_wall'):
        super().__init__(app, vao_name, pos, rot, scale)
        self.tint  = glm.vec3(tint)
        self.alpha = alpha

    def render(self):
        self._upload_common()
        _set(self.program, 'u_tint',  self.tint)
        _set(self.program, 'u_alpha', self.alpha)
        _set(self.program, 'u_ior', 1.5)
        _set(self.program, 'u_thickness', 0.08)
        _set(self.program, 'u_absorption_color', glm.vec3(0.10, 0.045, 0.025))
        _set(self.program, 'u_refraction_strength', 0.018)
        _set(self.program, 'u_reflection_strength', 0.35)
        self.vao.render()


class GlueSeam(BaseModel):
    def __init__(self, app, pos=(0,0,0), scale=(1,1,1),
                 tint=(0.70, 0.90, 0.95), alpha=0.18):
        super().__init__(app, 'glass_cube', pos, (0,0,0), scale)
        self.tint = glm.vec3(tint)
        self.alpha = alpha

    def render(self):
        self._upload_common()
        _set(self.program, 'u_tint', self.tint)
        _set(self.program, 'u_alpha', self.alpha)
        _set(self.program, 'u_ior', 1.5)
        _set(self.program, 'u_thickness', 0.12)
        _set(self.program, 'u_absorption_color', glm.vec3(0.06, 0.035, 0.02))
        _set(self.program, 'u_refraction_strength', 0.010)
        _set(self.program, 'u_reflection_strength', 0.20)
        self.vao.render()


# ─────────────────────────────────────────────────────────────────────────────
#  Sand floor
# ─────────────────────────────────────────────────────────────────────────────

class SandFloor(BaseModel):
    def __init__(self, app, pos=(0,0,0), scale=(1,1,1), half_extent=(5.0, 5.0)):
        super().__init__(app, 'sand_floor', pos, (0,0,0), scale)
        self.half_extent = glm.vec2(half_extent)

    def render(self):
        self._upload_common()
        sand = self.app.renderer.sand_material
        self.program['u_albedo_map'].value = 0
        self.program['u_normal_map'].value = 1
        self.program['u_roughness_map'].value = 2
        self.program['u_height_map'].value = 3
        _set(self.program, 'u_sand_tile', glm.vec2(6.0, 6.0))
        _set(self.program, 'u_normal_strength', 0.8)
        _set(self.program, 'u_micro_normal_strength', 0.3)
        _set(self.program, 'u_floor_half_extent', self.half_extent)
        sand['albedo'].use(location=0)
        sand['normal'].use(location=1)
        sand['roughness'].use(location=2)
        sand['height'].use(location=3)
        self.vao.render()


# ─────────────────────────────────────────────────────────────────────────────
#  Seaweed
# ─────────────────────────────────────────────────────────────────────────────

class Seaweed(BaseModel):
    def __init__(self, app, pos=(0,0,0), scale=(1,1,1), phase=0.0):
        super().__init__(app, 'seaweed', pos, (0,0,0), scale)
        self.phase = phase

    def render(self):
        self._upload_common()
        _set(self.program, 'u_sway_phase', self.phase)
        _set(self.program, 'u_wave_speed', self.sim.wave_speed)
        self.vao.render()


# ─────────────────────────────────────────────────────────────────────────────
#  Water Surface
# ─────────────────────────────────────────────────────────────────────────────

class WaterSurface(BaseModel):
    """Animated water surface plane with simplex noise displacement."""
    def __init__(self, app, water_y=5.4, tank_half_w=5.0, tank_half_d=5.0):
        super().__init__(app, 'water_surface',
                         pos=(0, water_y, 0),
                         rot=(0, 0, 0),
                         scale=(tank_half_w, 1.0, tank_half_d))

    def render(self):
        self._upload_common()
        _set(self.program, 'u_wave_amplitude', self.sim.wave_amplitude)
        _set(self.program, 'u_wave_frequency', self.sim.wave_frequency)
        _set(self.program, 'u_wave_speed',     self.sim.wave_speed)
        self.vao.render()


# ─────────────────────────────────────────────────────────────────────────────
#  Fish
# ─────────────────────────────────────────────────────────────────────────────

FISH_COLORS = [
    # (body,              belly/stripe,       fin accent)
    ((1.0, 0.38, 0.05), (1.0, 0.90, 0.10), (0.95, 0.20, 0.05)),  # clownfish
    ((0.10, 0.45, 0.90),(0.60, 0.90, 1.0), (0.05, 0.20, 0.70)),  # blue tang
    ((0.85, 0.15, 0.20),(1.0, 0.75, 0.20), (0.60, 0.05, 0.05)),  # red/gold
    ((0.15, 0.65, 0.35),(0.70, 1.0, 0.55), (0.05, 0.40, 0.20)),  # green
    ((0.65, 0.15, 0.80),(1.0, 0.65, 0.95), (0.45, 0.05, 0.60)),  # purple
    ((1.0, 0.75, 0.10), (1.0, 0.95, 0.60), (0.85, 0.45, 0.05)),  # golden
]

class Fish(BaseModel):
    TANK_HALF = 4.0

    def __init__(self, app, pos=None, color_idx=None):
        if pos is None:
            pos = (random.uniform(-3.2, 3.2),
                   random.uniform(0.8, 4.5),
                   random.uniform(-3.2, 3.2))
        # Scale: fish body mesh is unit-sized, scale to look good
        size = random.uniform(0.38, 0.60)
        super().__init__(app, 'fish', pos, (0,0,0), (size, size, size))

        cidx = color_idx if color_idx is not None else random.randint(0, len(FISH_COLORS)-1)
        self.color1, self.color2, self.color3 = FISH_COLORS[cidx]

        self.speed      = random.uniform(0.8, 1.8)
        self.swim_phase = random.uniform(0, math.tau)

        # Initial random direction
        angle = random.uniform(0, math.tau)
        self.direction = glm.normalize(glm.vec3(
            math.cos(angle), random.uniform(-0.05, 0.05), math.sin(angle)))

        self.turn_timer   = random.uniform(2.0, 5.0)
        self._yaw         = math.atan2(self.direction.z, self.direction.x)
        self._target_yaw  = self._yaw   # smooth turning
        self._bob_offset  = random.uniform(0, math.tau)
        self.is_fleeing   = False
        self.is_fleeing   = False
        self.flee_timer   = 0.0
        self.FLEE_DURATION = 1.5    # detik — durasi kabur
        self.FLEE_SPEED    = 5.0    # Kecepatan lari 3D (Bukan 150.0)
        self.FLEE_RADIUS   = 3.0    # Jarak sensitif 3D (Bukan 1000.0)


    def update(self, dt, t):
        dt_s = dt * 0.001  # ms → seconds

        # LOGIKA INTERAKTIF (BARU)
        if self.is_fleeing:
            self.flee_timer -= dt_s
            # Jika timer kabur habis, kembalikan ke kondisi santai
            if self.flee_timer <= 0.0:
                self.is_fleeing = False
                self.speed = getattr(self, 'normal_speed', random.uniform(0.8, 1.8))
        else:
            self.swim_phase += dt_s * self.speed * 2.0

            # Logika mencari arah acak saat santai (tetap dipertahankan)
            self.turn_timer -= dt_s
            if self.turn_timer <= 0:
                angle = random.uniform(0, math.tau)
                vy    = random.uniform(-0.08, 0.08)
                self.direction = glm.normalize(glm.vec3(
                    math.cos(angle), vy, math.sin(angle)))
                self._target_yaw = math.atan2(self.direction.z, self.direction.x)
                self.turn_timer  = random.uniform(2.0, 5.0)

        # Smooth yaw interpolation (no instant snapping)
        yaw_diff = self._target_yaw - self._yaw
        while yaw_diff >  math.pi: yaw_diff -= math.tau
        while yaw_diff < -math.pi: yaw_diff += math.tau
        self._yaw += yaw_diff * min(dt_s * 2.5, 1.0)
        
        # [CATATAN: Biarkan kode pergerakan (self.pos += move), 
        #           pantulan dinding, dan matriks di bawah sini persis seperti aslinya]
        move = self.direction * self.speed * dt_s
        self.pos += move
        
    
        # Choose new direction periodically
        self.turn_timer -= dt_s
        if self.turn_timer <= 0:
            angle = random.uniform(0, math.tau)
            vy    = random.uniform(-0.08, 0.08)
            self.direction = glm.normalize(glm.vec3(
                math.cos(angle), vy, math.sin(angle)))
            self._target_yaw = math.atan2(self.direction.z, self.direction.x)
            self.turn_timer  = random.uniform(2.0, 5.0)

        # Smooth yaw interpolation (no instant snapping)
        yaw_diff = self._target_yaw - self._yaw
        # Wrap difference to [-pi, pi]
        while yaw_diff >  math.pi: yaw_diff -= math.tau
        while yaw_diff < -math.pi: yaw_diff += math.tau
        self._yaw += yaw_diff * min(dt_s * 2.5, 1.0)

        # Move
        move = self.direction * self.speed * dt_s
        self.pos += move

        # Gentle vertical bob
        self.pos.y += math.sin(t * 1.2 + self._bob_offset) * 0.0008

        # Bounce off walls
        H = self.TANK_HALF
        bounced = False
        for axis in range(3):
            lo, hi = (-H, H) if axis != 1 else (0.6, 5.0)
            if self.pos[axis] < lo:
                self.pos[axis] = lo
                self.direction[axis] = abs(self.direction[axis])
                bounced = True
            elif self.pos[axis] > hi:
                self.pos[axis] = hi
                self.direction[axis] = -abs(self.direction[axis])
                bounced = True
        if bounced:
            self._target_yaw = math.atan2(self.direction.z, self.direction.x)

        # Model matrix: fish head points +X in local space, yaw around Y
        m = glm.mat4()
        m = glm.translate(m, self.pos)
        m = glm.rotate(m, self._yaw, glm.vec3(0, 1, 0))
        m = glm.scale(m, self.scale)
        self.m_model = m

    def render(self):
        self._upload_common()
        _set(self.program, 'u_color',      glm.vec3(self.color1))
        _set(self.program, 'u_color2',     glm.vec3(self.color2))
        _set(self.program, 'u_color3',     glm.vec3(self.color3))
        _set(self.program, 'u_swim_phase', self.swim_phase)
        self.vao.render()

    def trigger_flee(self, click_pos):
        cx, cy = click_pos
        dx = self.pos.x - cx
        dy = self.pos.y - cy

        dist = (dx * dx + dy * dy) ** 0.5
        
        # FIX 1: Abaikan klik jika jaraknya LEBIH BESAR dari radius efektif
        if dist > self.FLEE_RADIUS:
            return
        
        # FIX 2: Simpan kecepatan normal ikan sebelum di-boost
        if not hasattr(self, 'normal_speed'):
            self.normal_speed = self.speed
            
        self.is_fleeing = True
        self.flee_timer = self.FLEE_DURATION
        self.speed = self.FLEE_SPEED # Kecepatan jadi sangat cepat
        
        # FIX 3: Ganti arah berenang (direction) ikan agar kabur dari klik
        if dist > 0.01:
            new_dir = glm.vec3(dx, dy + random.uniform(-0.5, 0.5), self.direction.z)
            self.direction = glm.normalize(new_dir)
            self._target_yaw = math.atan2(self.direction.z, self.direction.x)

    
# ─────────────────────────────────────────────────────────────────────────────
#  Bubble
# ─────────────────────────────────────────────────────────────────────────────

class Bubble(BaseModel):
    def __init__(self, app, pos=None):
        if pos is None:
            pos = (random.uniform(-4.0, 4.0), 0.15, random.uniform(-4.0, 4.0))
        r = random.uniform(0.04, 0.14)
        super().__init__(app, 'bubble', pos, (0,0,0), (r, r, r))
        self.radius    = r
        self.rise_speed = random.uniform(0.5, 1.4)
        self.drift_x   = random.uniform(-0.08, 0.08)
        self.drift_z   = random.uniform(-0.08, 0.08)
        self.wobble    = random.uniform(0.01, 0.04)
        self.alive     = True

    def update(self, dt, t):
        spd = self.rise_speed * self.app.sim.bubble_rise_speed
        self.pos.y += spd * dt * 0.001
        self.pos.x += self.drift_x * dt * 0.001
        self.pos.z += self.drift_z * dt * 0.001

        # Pop at water surface (lowered to stay below wave level)
        if self.pos.y > 5.2:
            self.alive = False

        m = glm.mat4()
        m = glm.translate(m, self.pos)
        m = glm.scale(m, self.scale)
        self.m_model = m

    def render(self):
        self._upload_common()
        _set(self.program, 'u_wobble', self.wobble)
        self.vao.render()


# ─────────────────────────────────────────────────────────────────────────────
#  Helper
# ─────────────────────────────────────────────────────────────────────────────

def _set(prog, name, value):
    """Safe uniform set — silently skip if uniform not active in program."""
    try:
        if name in prog:
            prog[name].write(value) if hasattr(value, '__bytes__') or hasattr(value, 'to_bytes') else None
            # glm types have .to_bytes, primitives need direct assignment
            uni = prog[name]
            if hasattr(value, 'to_bytes'):
                uni.write(value)
            else:
                uni.value = value
    except Exception:
        pass
