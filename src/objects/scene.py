"""
AquariumScene - constructs the full aquarium layout and manages
runtime lists of fish and bubbles.
"""

import random
import math
from src.objects.model import SolidModel, GlassPanel, GlueSeam, SandFloor, Seaweed, Fish, Bubble, WaterSurface


# Tank dimensions (half-extents)
TANK_W = 5.0   # X half-width
TANK_H = 6.0   # full height
TANK_D = 5.0   # Z half-depth
WALL_T = 0.12  # glass thickness
WATER_SURFACE_DIFFERENCE = 2  # the distance between water surface and tank height


class AquariumScene:
    def __init__(self, app):
        self.app = app

        # Object lists
        self.static_opaque = []  # rocks, coral, sand, seaweed
        self.glass_panels = []  # semi-transparent walls
        self.fish = []
        self.bubbles = []

        # Water surface (animated)
        self.water_surface = WaterSurface(app, water_y=5.4)

        # Bubble spawn timer
        self._bubble_timer = 0.0

        self._build_tank()
        self._build_decorations()
        self._spawn_initial_fish()
        self._spawn_initial_bubbles()

    @property
    def objects(self):
        """Return a live list of all scene objects for HUD / debug introspection."""
        return [
            *self.static_opaque,
            *self.glass_panels,
            *self.fish,
            *self.bubbles,
            self.water_surface,
        ]

    # ──────────────────────────────────────────────────────────────────
    #  Build
    # ──────────────────────────────────────────────────────────────────

    def _build_tank(self):
        app = self.app
        W, H, D = TANK_W, TANK_H, TANK_D
        wall_height = H + WATER_SURFACE_DIFFERENCE
        wall_half_h = wall_height * 0.5
        wall_center_y = wall_half_h

        # --- Sand floor ---
        self.static_opaque.append(
            SandFloor(app, pos=(0, 0, 0), scale=(1, 1, 1), half_extent=(W, D))
        )

        # --- Glass walls ---
        glass_tint = (0.55, 0.78, 0.82)
        glass_alpha = 0.08

        def add_glass(pos, rot, scale):
            self.glass_panels.append(
                GlassPanel(app, pos=pos, rot=rot, scale=scale,
                           tint=glass_tint, alpha=glass_alpha, vao_name='glass_cube')
            )

        # Front (Z+)
        add_glass(pos=(0, wall_center_y, D),  rot=(0, 0, 0),
                  scale=(W, wall_half_h, WALL_T * 0.5))
        # Back (Z-)
        add_glass(pos=(0, wall_center_y, -D), rot=(0, 180, 0),
                  scale=(W, wall_half_h, WALL_T * 0.5))
        # Left (X-)
        add_glass(pos=(-W, wall_center_y, 0), rot=(0, 0, 0),
                  scale=(WALL_T * 0.5, wall_half_h, D))
        # Right (X+)
        add_glass(pos=(W, wall_center_y, 0),  rot=(0, 0, 0),
                  scale=(WALL_T * 0.5, wall_half_h, D))

        # --- Transparent glue seams at direct glass-to-glass joins ---
        seam_r = 0.035
        for sx in (-1, 1):
            for sz in (-1, 1):
                self.glass_panels.append(GlueSeam(
                    app,
                    pos=(sx * W, wall_center_y, sz * D),
                    scale=(seam_r, wall_half_h, seam_r),
                    tint=(0.70, 0.90, 0.95),
                    alpha=0.18,
                ))

        # --- Subtle glass edge beads for stronger edge visibility ---
        edge_r = 0.028
        edge_tint = (0.68, 0.88, 0.94)
        edge_alpha = 0.14
        for y in (0.0, wall_height):
            for z in (-D, D):
                self.glass_panels.append(GlueSeam(
                    app,
                    pos=(0, y, z),
                    scale=(W, edge_r, edge_r),
                    tint=edge_tint,
                    alpha=edge_alpha,
                ))
            for x in (-W, W):
                self.glass_panels.append(GlueSeam(
                    app,
                    pos=(x, y, 0),
                    scale=(edge_r, edge_r, D),
                    tint=edge_tint,
                    alpha=edge_alpha,
                ))

    def _build_decorations(self):
        app = self.app

        self.static_opaque.append(SolidModel(
            app, 'solid_cube',
            pos=(-1.7, 0.18, -1.8), rot=(0, 28, 4),
            scale=(1.40, 0.18, 0.46),
            color=(0.28, 0.20, 0.13)))
        # Port hull wall
        self.static_opaque.append(SolidModel(
            app, 'solid_cube',
            pos=(-2.55, 0.38, -2.05), rot=(0, 28, 0),
            scale=(1.35, 0.18, 0.06),
            color=(0.30, 0.22, 0.14)))
        # Starboard hull wall
        self.static_opaque.append(SolidModel(
            app, 'solid_cube',
            pos=(-0.90, 0.38, -1.52), rot=(0, 28, 0),
            scale=(1.35, 0.18, 0.06),
            color=(0.30, 0.22, 0.14)))
        # Broken mast 1 (standing, tilted)
        self.static_opaque.append(SolidModel(
            app, 'solid_cube',
            pos=(-1.55, 1.05, -1.68), rot=(0, 28, 18),
            scale=(0.055, 1.05, 0.055),
            color=(0.33, 0.24, 0.16)))
        # Broken mast 2 (fallen on deck)
        self.static_opaque.append(SolidModel(
            app, 'solid_cube',
            pos=(-2.15, 0.26, -2.05), rot=(0, 28, 72),
            scale=(0.05, 0.65, 0.05),
            color=(0.31, 0.23, 0.15)))
        # Cargo barrel (sphere)
        self.static_opaque.append(SolidModel(
            app, 'solid_sphere',
            pos=(-2.25, 0.22, -1.45), rot=(0, 0, 0),
            scale=(0.18, 0.22, 0.18),
            color=(0.30, 0.22, 0.13)))
        # Treasure chest body
        self.static_opaque.append(SolidModel(
            app, 'solid_cube',
            pos=(-1.15, 0.13, -2.15), rot=(0, 14, 0),
            scale=(0.18, 0.12, 0.14),
            color=(0.30, 0.21, 0.10)))
        # Treasure chest lid (slightly open)
        self.static_opaque.append(SolidModel(
            app, 'solid_cube',
            pos=(-1.15, 0.28, -2.15), rot=(0, 14, -18),
            scale=(0.18, 0.05, 0.14),
            color=(0.38, 0.27, 0.13)))
        # Coral on wreck — warm red/orange growing from hull
        self.static_opaque.append(SolidModel(
            app, 'coral',
            pos=(-1.50, 0.75, -1.92), rot=(0, 0, 0),
            scale=(0.13, 0.65, 0.13),
            color=(0.95, 0.32, 0.22)))
        self.static_opaque.append(SolidModel(
            app, 'coral',
            pos=(-2.05, 0.55, -1.72), rot=(0, 0, 0),
            scale=(0.10, 0.42, 0.10),
            color=(0.90, 0.55, 0.14)))
        self.static_opaque.append(SolidModel(
            app, 'coral',
            pos=(-1.25, 0.42, -2.05), rot=(0, 0, 0),
            scale=(0.08, 0.32, 0.08),
            color=(1.00, 0.75, 0.10)))
        # Wreck base rock
        self.static_opaque.append(SolidModel(
            app, 'rock',
            pos=(-2.40, 0.38, -2.30), rot=(0, 55, 0),
            scale=(0.55, 0.38, 0.45),
            color=(0.36, 0.32, 0.28)))

        # Main spire — very tall, commanding
        self.static_opaque.append(SolidModel(
            app, 'coral',
            pos=(1.8, 2.1, 1.8), rot=(0, 0, 0),
            scale=(0.28, 2.1, 0.28),
            color=(0.90, 0.20, 0.48)))
        # Branch spires at varied heights
        self.static_opaque.append(SolidModel(
            app, 'coral',
            pos=(1.35, 1.50, 2.25), rot=(0, 0, 0),
            scale=(0.18, 1.50, 0.18),
            color=(0.95, 0.42, 0.18)))
        self.static_opaque.append(SolidModel(
            app, 'coral',
            pos=(2.30, 1.10, 1.45), rot=(0, 0, 0),
            scale=(0.15, 1.10, 0.15),
            color=(1.00, 0.72, 0.08)))
        self.static_opaque.append(SolidModel(
            app, 'coral',
            pos=(2.05, 0.65, 2.35), rot=(0, 0, 0),
            scale=(0.10, 0.65, 0.10),
            color=(0.80, 0.16, 0.68)))
        self.static_opaque.append(SolidModel(
            app, 'coral',
            pos=(1.50, 0.42, 1.40), rot=(0, 0, 0),
            scale=(0.08, 0.42, 0.08),
            color=(0.95, 0.58, 0.22)))
        # Base rocks anchoring the spire cluster
        self.static_opaque.append(SolidModel(
            app, 'rock',
            pos=(1.80, 0.40, 1.80), rot=(0, 42, 0),
            scale=(0.58, 0.40, 0.52),
            color=(0.38, 0.34, 0.30)))
        self.static_opaque.append(SolidModel(
            app, 'rock',
            pos=(2.10, 0.22, 2.15), rot=(0, 115, 0),
            scale=(0.30, 0.22, 0.28),
            color=(0.34, 0.30, 0.26)))

        rock_configs = [
            # Left wall: big rock with a smaller one sitting on top
            dict(pos=(-3.50, 0.45, 0.60), scale=(0.68, 0.45, 0.55), rot=(0, 22, 0),  color=(0.38, 0.34, 0.30)),
            dict(pos=(-3.25, 0.92, 0.35), scale=(0.36, 0.36, 0.33), rot=(0, 68, 8),  color=(0.34, 0.30, 0.26)),  # on top
            dict(pos=(-3.62, 0.20, -0.20), scale=(0.28, 0.20, 0.26), rot=(0, 110, 0), color=(0.32, 0.29, 0.25)),
            # Right back wall
            dict(pos=(3.30, 0.52, -2.90), scale=(0.72, 0.52, 0.62), rot=(0, 148, 0), color=(0.40, 0.36, 0.32)),
            dict(pos=(3.55, 0.25, -2.45), scale=(0.32, 0.25, 0.30), rot=(0, 198, 0), color=(0.36, 0.32, 0.27)),
            # Front-right, mid depth — draws eye via rule of 3rds
            dict(pos=(3.10, 0.38, 3.40), scale=(0.50, 0.38, 0.46), rot=(0, 62, 0),   color=(0.42, 0.38, 0.34)),
        ]
        for cfg in rock_configs:
            self.static_opaque.append(SolidModel(
                app, 'rock',
                pos=cfg['pos'], rot=cfg['rot'],
                scale=cfg['scale'], color=cfg['color']))

        # ════════════════════════════════════════════════════════════════════════
        # ACCENT CORALS — scattered, varied heights 0.4 – 1.5
        # ════════════════════════════════════════════════════════════════════════

        coral_accents = [
            # Right back cluster
            dict(pos=(3.10, 1.50, -3.10), scale=(0.17, 1.50, 0.17), color=(0.90, 0.24, 0.50)),
            dict(pos=(3.40, 0.90, -2.75), scale=(0.12, 0.90, 0.12), color=(0.80, 0.18, 0.70)),
            dict(pos=(2.75, 0.58, -3.40), scale=(0.09, 0.58, 0.09), color=(1.00, 0.55, 0.10)),
            # Left-front
            dict(pos=(-3.00, 1.20, 2.85), scale=(0.16, 1.20, 0.16), color=(0.95, 0.35, 0.25)),
            dict(pos=(-2.65, 0.72, 3.20), scale=(0.11, 0.72, 0.11), color=(0.95, 0.60, 0.20)),
            # Back-center pushed to right 1/3
            dict(pos=(1.60, 1.35, -4.05), scale=(0.20, 1.35, 0.20), color=(1.00, 0.40, 0.15)),
            dict(pos=(1.90, 0.78, -3.72), scale=(0.13, 0.78, 0.13), color=(0.85, 0.22, 0.55)),
        ]
        for cfg in coral_accents:
            self.static_opaque.append(SolidModel(
                app, 'coral',
                pos=cfg['pos'], rot=(0, 0, 0),
                scale=cfg['scale'], color=cfg['color']))

        seaweed_positions = [
            # Around wreck
            (-2.55, 0.0, -2.40), (-2.30, 0.0, -2.60), (-1.20, 0.0, -2.55),
            (-1.05, 0.0, -2.30), (-2.65, 0.0, -1.45),
            # Around coral spire
            (1.20, 0.0, 2.55), (2.55, 0.0, 1.30), (1.55, 0.0, 3.05),
            # Left wall
            (-4.05, 0.0,  1.55), (-3.82, 0.0,  1.20), (-4.25, 0.0,  1.85),
            # Back right
            (3.52, 0.0, -3.52), (3.20, 0.0, -3.82),
            # Front scattered
            (0.55, 0.0, 4.25), (-0.45, 0.0, 4.05),
        ]
        for x, y, z in seaweed_positions:
            h = random.uniform(1.0, 3.2)
            phase = random.uniform(0, math.tau)
            self.static_opaque.append(Seaweed(
                app, pos=(x, h * 0.5, z),
                scale=(0.08, h * 0.5, 0.08),
                phase=phase))

        # ── Gravel accent ─────────────────────────────────────────────────────
        for _ in range(14):
            gx = random.uniform(-4.3, 4.3)
            gz = random.uniform(-4.3, 4.3)
            gs = random.uniform(0.06, 0.14)
            gray = random.uniform(0.30, 0.55)
            self.static_opaque.append(SolidModel(
                app, 'solid_cube',
                pos=(gx, gs * 0.5, gz),
                rot=(random.uniform(0, 360), random.uniform(0, 360), 0),
                scale=(gs, gs * 0.6, gs),
                color=(gray, gray * 0.95, gray * 0.90)))


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

    # Fungsi yang mengatur jumlah ikan sesuai dengan nilai target dari HUD slider / state simulasi
    def _enforce_fish_target(self):
        target = max(0, self.app.sim.max_fish)
        while len(self.fish) < target:
            self.fish.append(Fish(self.app))
        if len(self.fish) > target:
            self.fish = self.fish[:target]

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

        # Enforce fish target count from HUD slider / simulation state
        self._enforce_fish_target()

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

    def on_glass_click(self, world_pos):
        for fish in self.fish:
            fish.trigger_flee(world_pos)
