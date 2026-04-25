"""
Aquarium 3D - Interactive OpenGL Simulation
Entry point and main engine loop.
"""

import sys
import pygame as pg
import moderngl as mgl

from src.components.camera import Camera
from lighting import AquariumLight
from src.components.mesh import Mesh
from src.objects.scene import AquariumScene
from src.renderer import AquariumRenderer
from input_handler import InputHandler
from simulation import SimulationState

class AquariumEngine:
    WIN_SIZE = (1280, 720)

    def __init__(self):
        pg.init()
        pg.display.set_caption("Aquarium 3D - Interactive Simulation")

        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.gl_set_attribute(pg.GL_DOUBLEBUFFER, 1)
        self.screen = pg.display.set_mode(self.WIN_SIZE, flags=pg.OPENGL | pg.DOUBLEBUF)

        pg.display.gl_set_attribute(pg.GL_SWAP_CONTROL, 1)
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)

        self.ctx = mgl.create_context(require=330)
        self.ctx.enable(flags=mgl.DEPTH_TEST | mgl.CULL_FACE | mgl.BLEND)
        self.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        self.ctx.gc_mode = 'auto'

        self.clock      = pg.time.Clock()
        self.time       = 0.0
        self.delta_time = 16.0   # safe default (ms)

        self.sim      = SimulationState()
        self.light    = AquariumLight()
        self.camera   = Camera(self)
        self.mesh     = Mesh(self)
        self.scene    = AquariumScene(self)
        self.input    = InputHandler(self)
        self.renderer = AquariumRenderer(self)

        print(self._controls_text())

    def _controls_text(self):
        return (
            "\n=== AQUARIUM 3D CONTROLS ===\n"
            "  RMB drag        - Orbit rotate\n"
            "  Scroll Wheel    - Zoom\n"
            "  MMB drag        - Pan\n"
            "  TAB             - Toggle FPS / Orbit\n"
            "  WASD + Q/E      - FPS movement\n"
            "  R               - Reset camera\n"
            "  SPACE           - Pause / Play\n"
            "  B               - Spawn bubble\n"
            "  F               - Spawn fish\n"
            "  UP/DOWN         - Wave speed +/-\n"
            "  LEFT/RIGHT      - Bubble count +/-\n"
            "  Z/X             - Light intensity +/-\n"
            "  1/2/3           - Water color preset\n"
            "  ESC             - Quit\n"
            "============================\n"
        )

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            self.input.handle_event(event)

    def update(self):
        self.time = pg.time.get_ticks() * 0.001
        if not self.sim.paused:
            self.scene.update(self.delta_time, self.time)
        self.camera.update()

    def render(self):
        # ── 3D scene ─────────────────────────────────────────────────
        self.ctx.clear(color=(0.02, 0.06, 0.12, 1.0))
        self.renderer.render()

        pg.display.flip()

    def quit(self):
        self.mesh.destroy()
        self.renderer.destroy()
        pg.quit()
        sys.exit()

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.render()
            self.delta_time = self.clock.tick(60)


if __name__ == '__main__':
    app = AquariumEngine()
    app.run()