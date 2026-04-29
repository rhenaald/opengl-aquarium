import pygame as pg


class InputHandler:
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        cam = self.app.camera
        sim = self.app.sim
        scene = self.app.scene

        cam.handle_event(event)

        # Slider
        if hasattr(self.app, 'hud'):
            self.app.hud.handle_event(event)

        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            # Cek dulu HUD tidak sedang diklik (agar slider tidak trigger flee)
            if not (hasattr(self.app, 'hud') and self.app.hud.is_over(event.pos)):
                world_pos = self._screen_to_world(event.pos)
                scene.on_glass_click(world_pos)
                print(f"[INPUT] Glass tapped at screen={event.pos} world={world_pos}")

        if event.type == pg.KEYDOWN:
            key = event.key

            if key == pg.K_ESCAPE:
                self.app.quit()

            elif key == pg.K_TAB:
                cam.toggle_mode()

            elif key == pg.K_r:
                cam.reset()

            elif key == pg.K_SPACE:
                sim.toggle_pause()
                state = "PAUSED" if sim.paused else "RUNNING"
                print(f"[SIM] {state}")

            elif key == pg.K_b:
                scene.spawn_bubble_manual()
                print("[SIM] Bubble spawned manually")

            elif key == pg.K_f:
                scene.spawn_fish_manual()
                print(f"[SIM] Fish spawned (total: {len(scene.fish)})")

            elif key == pg.K_UP:
                sim.increase_wave_speed()
                print(f"[SIM] Wave speed: {sim.wave_speed:.2f}")

            elif key == pg.K_DOWN:
                sim.decrease_wave_speed()
                print(f"[SIM] Wave speed: {sim.wave_speed:.2f}")

            elif key == pg.K_RIGHT:
                sim.increase_bubbles()
                print(f"[SIM] Max bubbles: {sim.max_bubbles}")

            elif key == pg.K_LEFT:
                sim.decrease_bubbles()
                print(f"[SIM] Max bubbles: {sim.max_bubbles}")

            elif key == pg.K_z:
                sim.decrease_light()
                self.app.light.set_intensity(sim.light_intensity)
                print(f"[SIM] Light: {sim.light_intensity:.2f}")

            elif key == pg.K_x:
                sim.increase_light()
                self.app.light.set_intensity(sim.light_intensity)
                print(f"[SIM] Light: {sim.light_intensity:.2f}")

            elif key == pg.K_1:
                name = sim.set_water_preset(0)
                print(f"[SIM] Water: {name}")

            elif key == pg.K_2:
                name = sim.set_water_preset(1)
                print(f"[SIM] Water: {name}")

            elif key == pg.K_3:
                name = sim.set_water_preset(2)
                print(f"[SIM] Water: {name}")

    def _screen_to_world(self, screen_pos):
        sw, sh = pg.display.get_surface().get_size()
        sx, sy = screen_pos

        nx = sx / sw
        ny = sy / sh

        # TANK_W dan TANK_H mengacu pada ukuran scene.py (5.0 dan 6.0)
        TANK_W = 5.0
        TANK_H = 6.0

        wx = (nx * 2.0 - 1.0) * TANK_W
        wy = (1.0 - ny) * TANK_H

        return (wx, wy)