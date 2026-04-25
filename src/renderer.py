"""
AquariumRenderer - renders the scene in correct order:
  1. Opaque objects (sand, rocks, coral, seaweed, fish)
  2. Transparent / additive objects sorted back-to-front (bubbles)
  3. Glass panels (depth-write off, blended)
"""


class AquariumRenderer:
    def __init__(self, app):
        self.app   = app
        self.ctx   = app.ctx
        self.scene = app.scene

    def render(self):
        scene = self.scene
        ctx   = self.ctx
        cam   = self.app.camera

        # ── 1. Opaque pass ─────────────────────────────────────────────
        ctx.enable_only(self.ctx.DEPTH_TEST | self.ctx.CULL_FACE)
        for obj in scene.static_opaque:
            obj.render()
        for f in scene.fish:
            f.render()

        # ── 2. Bubbles — transparent, no back-face culling ─────────────
        ctx.enable_only(self.ctx.DEPTH_TEST | self.ctx.BLEND)
        ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA

        # Sort bubbles back-to-front
        cam_pos = cam.position
        def bubble_dist(b):
            d = b.pos - cam_pos
            return -(d.x*d.x + d.y*d.y + d.z*d.z)

        sorted_bubbles = sorted(scene.bubbles, key=bubble_dist)
        for b in sorted_bubbles:
            b.render()

        # ── 3. Glass panels — transparent, no culling, depth-write off ─
        ctx.enable_only(self.ctx.DEPTH_TEST | self.ctx.BLEND)
        ctx.depth_func = '<='   # LEQUAL

        def glass_dist(g):
            d = g.pos - cam_pos
            return -(d.x*d.x + d.y*d.y + d.z*d.z)

        sorted_glass = sorted(scene.glass_panels, key=glass_dist)
        for g in sorted_glass:
            g.render()

        # Restore default state
        ctx.enable_only(self.ctx.DEPTH_TEST | self.ctx.CULL_FACE)
        ctx.depth_func = '<'    # LESS

    def destroy(self):
        pass