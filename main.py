"""
Aquarium 3D - Interactive OpenGL Simulation
Entry point and main engine loop.
"""

from src.renderer import AquariumRenderer
from src.objects.scene import AquariumScene
# from src.engine.input_manager import InputManager
from src.components.mesh import Mesh
from src.components.point_light import PointLight
from src.components.camera import Camera
from simulation import SimulationState
from input_handler import InputHandler
from lighting import AquariumLight
import sys
import pygame as pg
import moderngl as mgl


class AquariumEngine:
    WIN_SIZE = (1280, 720)

    def __init__(self):
        pg.init()
        pg.display.set_caption("Aquarium 3D - Interactive Simulation")

        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(
            pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.gl_set_attribute(pg.GL_DOUBLEBUFFER, 1)
        self.screen = pg.display.set_mode(
            self.WIN_SIZE, flags=pg.OPENGL | pg.DOUBLEBUF)

        pg.display.gl_set_attribute(pg.GL_SWAP_CONTROL, 1)
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)

        self.ctx = mgl.create_context(require=330)
        self.ctx.enable(flags=mgl.DEPTH_TEST | mgl.CULL_FACE | mgl.BLEND)
        self.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        self.ctx.gc_mode = 'auto'

        # Timing
        self.clock = pg.time.Clock()
        self.time = 0.0
        self.delta_time = 0.0

        # Simulation state (pause/play, parameters)
        self.sim = SimulationState()

        # Lighting
        self.light = AquariumLight()

        # Camera
        # self.input = InputManager()
        self.light = PointLight(position=(6.0, 8.0, 6.0),
                                color=(1.0, 1.0, 1.0), intensity=1.2)
        self.camera = Camera(self)

        # Geometry & shaders
        self.mesh = Mesh(self)

        # Scene objects
        self.scene = AquariumScene(self)

        # Input handler
        self.input = InputHandler(self)

        # Renderer
        self.renderer = AquariumRenderer(self)

        self.running = True

        # HUD font
        pg.font.init()
        self.font = pg.font.SysFont("monospace", 16)
        self.hud_surface = pg.Surface(self.WIN_SIZE, pg.SRCALPHA)

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

    # def render_hud(self):
    #     """Overlay HUD info using pygame surface blitted over GL."""
    #     # We'll draw HUD text as overlay
    #     info_lines = [
    #         f"FPS: {self.clock.get_fps():.0f}",
    #         f"Sim: {'PAUSED' if self.sim.paused else 'RUNNING'}",
    #         f"Bubbles: {len(self.scene.bubbles)}",
    #         f"Fish: {len(self.scene.fish)}",
    #         f"Wave Speed: {self.sim.wave_speed:.2f}",
    #         f"Light: {self.sim.light_intensity:.2f}",
    #         f"Cam: {'FPS' if not self.camera.use_orbit else 'Orbit'}",
    #         f"[SPACE] Pause  [B] Bubble  [F] Fish",
    #     ]

    #     # Draw text using pygame overlay technique
    #     overlay = pg.Surface((260, len(info_lines) * 20 + 10), pg.SRCALPHA)
    #     overlay.fill((0, 0, 0, 120))
    #     for i, line in enumerate(info_lines):
    #         color = (180, 255, 220) if i < 7 else (140, 200, 255)
    #         text = self.font.render(line, True, color)
    #         overlay.blit(text, (8, 5 + i * 20))

    #     # Temporarily switch to 2D rendering for HUD
    #     # Use a separate pygame window surface trick:
    #     pg.display.get_surface().blit(overlay, (10, 10))

    #     self.scene = Scene(self)
    #     self.scene_renderer = Renderer(self)

    #     self.running = True

    # def check_events(self):
    #     self.input.update()

    #     if self.input.quit_requested:
    #         self.running = False
    #         return

    #     if self.input.camera_mode_toggle_requested:
    #         self.camera.use_orbit = not self.camera.use_orbit
    #         self.camera.set_default()

    #     if self.input.mouse_visible_toggle_requested:
    #         visible = not pg.mouse.get_visible()
    #         pg.mouse.set_visible(visible)
    #         pg.event.set_grab(not visible)

    #     if self.camera.use_orbit:
    #         if self.input.orbit_zoom_in:
    #             self.camera.orbit_radius = max(
    #                 2.0, self.camera.orbit_radius - 0.5)
    #         elif self.input.orbit_zoom_out:
    #             self.camera.orbit_radius = min(
    #                 40.0, self.camera.orbit_radius + 0.5)

    def render(self):
        self.ctx.clear(color=(0.02, 0.06, 0.12, 1.0))
        self.renderer.render()
        # self.render_hud()
        pg.display.flip()

    def update(self):
        self.time = pg.time.get_ticks() * 0.001
        if not self.sim.paused:
            self.scene.update(self.delta_time, self.time)
        self.camera.update()

    def get_time(self):
        self.time = pg.time.get_ticks() * 0.001

    def destroy(self):
        self.mesh.destroy()
        # self.scene_renderer.destroy()

    def quit(self):
        self.mesh.destroy()
        self.renderer.destroy()
        pg.quit()
        sys.exit()

    def run(self):
        while self.running:
            self.get_time()
            self.check_events()
            self.update()
            self.render()
            self.delta_time = self.clock.tick(60)

        self.destroy()
        pg.quit()
        sys.exit()


if __name__ == '__main__':
    app = AquariumEngine()
    app.run()
