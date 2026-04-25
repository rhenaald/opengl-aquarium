"""
AquariumScene - constructs the full aquarium layout and manages
runtime lists of fish and bubbles.
"""

import random
import math
from model import SolidModel, GlassPanel, SandFloor, Seaweed, Fish, Bubble


# Tank dimensions (half-extents)
TANK_W = 5.0   # X half-width
TANK_H = 6.0   # full height
TANK_D = 5.0   # Z half-depth
WALL_T = 0.12  # glass thickness


class AquariumScene:
    def __init__(self, app):
        self.app = app

        # Object lists
        self.static_opaque      = []  # rocks, coral, sand, seaweed
        self.glass_panels       = []  # semi-transparent walls
        self.fish               = []
        self.bubbles            = []

        # Bubble spawn timer
        self._bubble_timer = 0.0

        self._build_tank()
        self._build_decorations()
        self._spawn_initial_fish()
        self._spawn_initial_bubbles()

    # ──────────────────────────────────────────────────────────────────
    #  Build
    # ──────────────────────────────────────────────────────────────────

    def _build_tank(self):
        app = self.app
        W, H, D = TANK_W, TANK_H, TANK_D

        # --- Sand floor ---
        self.static_opaque.append(
            SandFloor(app, pos=(0, 0, 0), scale=(W, 1, D))
        )

        # --- Tank frame corners (dark metal look) ---
        frame_color = (0.12, 0.12, 0.14)
        pillar_r    = 0.12
        for sx in (-1, 1):
            for sz in (-1, 1):
                self.static_opaque.append(SolidModel(
                    app, 'solid_cube',
                    pos=(sx * W, H * 0.5, sz * D),
                    scale=(pillar_r, H * 0.5, pillar_r),
                    color=frame_color
                ))
        # Top & bottom rim bars
        for sy in (0.06, H - 0.06):
            # X bars
            for sz in (-1, 1):
                self.static_opaque.append(SolidModel(
                    app, 'solid_cube',
                    pos=(0, sy, sz * D),
                    scale=(W, pillar_r, pillar_r),
                    color=frame_color
                ))
            # Z bars
            for sx in (-1, 1):
                self.static_opaque.append(SolidModel(
                    app, 'solid_cube',
                    pos=(sx * W, sy, 0),
                    scale=(pillar_r, pillar_r, D),
                    color=frame_color
                ))

        # --- Glass walls ---
        glass_tint  = (0.55, 0.78, 0.82)
        glass_alpha = 0.08

        def add_glass(pos, rot, scale):
            self.glass_panels.append(
                GlassPanel(app, pos=pos, rot=rot, scale=scale,
                           tint=glass_tint, alpha=glass_alpha)
            )

        # Front (Z+)
        add_glass(pos=(0, H*0.5, D),  rot=(0, 0, 0),   scale=(W, H*0.5, 1))
        # Back (Z-)
        add_glass(pos=(0, H*0.5, -D), rot=(0, 180, 0),  scale=(W, H*0.5, 1))
        # Left (X-)
        add_glass(pos=(-W, H*0.5, 0), rot=(0, -90, 0),  scale=(D, H*0.5, 1))
        # Right (X+)
        add_glass(pos=(W, H*0.5, 0),  rot=(0,  90, 0),  scale=(D, H*0.5, 1))

    def _build_decorations(self):
        app = self.app

        # --- Rocks ---
        rock_configs = [
            dict(pos=(-3.2, 0.35, -2.8), scale=(0.55, 0.40, 0.45), rot=(0,  25, 0), color=(0.38, 0.34, 0.30)),
            dict(pos=(-3.0, 0.18, -2.5), scale=(0.30, 0.22, 0.28), rot=(0,  70, 0), color=(0.32, 0.29, 0.26)),
            dict(pos=( 3.5, 0.30, -3.2), scale=(0.50, 0.35, 0.40), rot=(0, 130, 0), color=(0.40, 0.36, 0.32)),
            dict(pos=( 3.2, 0.45, -2.8), scale=(0.65, 0.50, 0.55), rot=(0, 200, 0), color=(0.35, 0.31, 0.28)),
            dict(pos=( 0.5, 0.22,  3.8), scale=(0.42, 0.30, 0.38), rot=(0,  45, 0), color=(0.42, 0.38, 0.34)),
            dict(pos=(-1.0, 0.18,  3.6), scale=(0.28, 0.20, 0.24), rot=(0,  90, 0), color=(0.36, 0.32, 0.28)),
        ]
        for cfg in rock_configs:
            self.static_opaque.append(SolidModel(
                app, 'rock',
                pos=cfg['pos'], rot=cfg['rot'],
                scale=cfg['scale'], color=cfg['color']
            ))

        # --- Coral columns ---
        coral_configs = [
            dict(pos=(-2.5, 1.0, -3.5), scale=(0.18, 1.0, 0.18), color=(0.95, 0.35, 0.25)),
            dict(pos=(-2.3, 0.7, -3.3), scale=(0.12, 0.7, 0.12), color=(0.95, 0.60, 0.20)),
            dict(pos=(-2.7, 0.6, -3.2), scale=(0.10, 0.55, 0.10), color=(1.00, 0.80, 0.10)),
            dict(pos=( 3.2, 1.2, -2.5), scale=(0.20, 1.2, 0.20), color=(0.90, 0.25, 0.50)),
            dict(pos=( 3.0, 0.8, -2.2), scale=(0.14, 0.8, 0.14), color=(0.80, 0.20, 0.70)),
            dict(pos=( 0.0, 0.9,  4.0), scale=(0.16, 0.9, 0.16), color=(1.00, 0.55, 0.10)),
        ]
        for cfg in coral_configs:
            self.static_opaque.append(SolidModel(
                app, 'coral',
                pos=cfg['pos'], rot=(0, 0, 0),
                scale=cfg['scale'], color=cfg['color']
            ))

        # --- Seaweed clusters ---
        seaweed_positions = [
            (-1.5, 0.0, -4.2), (-1.2, 0.0, -4.0), (-1.8, 0.0, -3.8),
            ( 2.0, 0.0, -4.0), ( 2.3, 0.0, -3.8),
            (-4.0, 0.0,  1.5), (-3.8, 0.0,  1.2), (-4.2, 0.0,  1.8),
            ( 4.0, 0.0,  2.0), ( 3.8, 0.0,  2.3),
            ( 0.5, 0.0,  4.2), ( 0.2, 0.0,  4.0),
        ]
        for i, (x, y, z) in enumerate(seaweed_positions):
            h = random.uniform(1.2, 2.8)
            phase = random.uniform(0, math.tau)
            self.static_opaque.append(Seaweed(
                app, pos=(x, h * 0.5, z),
                scale=(0.08, h * 0.5, 0.08),
                phase=phase
            ))

        # --- Gravel accent (small scattered cubes on sand) ---
        for _ in range(18):
            gx = random.uniform(-4.3, 4.3)
            gz = random.uniform(-4.3, 4.3)
            gs = random.uniform(0.06, 0.14)
            gray = random.uniform(0.30, 0.55)
            self.static_opaque.append(SolidModel(
                app, 'solid_cube',
                pos=(gx, gs * 0.5, gz),
                rot=(random.uniform(0, 360), random.uniform(0, 360), 0),
                scale=(gs, gs * 0.6, gs),
                color=(gray, gray * 0.95, gray * 0.90)
            ))

    def _spawn_initial_fish(self):
        for i in range(5):
            self.fish.append(Fish(self.app, color_idx=i % 5))

    def _spawn_initial_bubbles(self):
        for _ in range(20):
            b = Bubble(self.app)
            b.pos.y = random.uniform(0.2, 5.5)  # distribute vertically
            self.bubbles.append(b)

    # ──────────────────────────────────────────────────────────────────
    #  Runtime: spawn manually
    # ──────────────────────────────────────────────────────────────────

    def spawn_bubble_manual(self):
        if len(self.bubbles) < self.app.sim.max_bubbles + 20:
            self.bubbles.append(Bubble(self.app))

    def spawn_fish_manual(self):
        if len(self.fish) < self.app.sim.max_fish + 10:
            self.fish.append(Fish(self.app))

    # ──────────────────────────────────────────────────────────────────
    #  Update
    # ──────────────────────────────────────────────────────────────────

    def update(self, dt, t):
        # Auto-spawn bubbles
        self._bubble_timer += dt
        spawn_interval = max(80, 800 // max(1, self.app.sim.max_bubbles))
        if self._bubble_timer > spawn_interval and len(self.bubbles) < self.app.sim.max_bubbles:
            self.bubbles.append(Bubble(self.app))
            self._bubble_timer = 0.0

        # Update fish
        for f in self.fish:
            f.update(dt, t)

        # Update & cull bubbles
        for b in self.bubbles:
            b.update(dt, t)
        self.bubbles = [b for b in self.bubbles if b.alive]

        # Update static animated (seaweed)
        for obj in self.static_opaque:
            obj.update(dt, t)