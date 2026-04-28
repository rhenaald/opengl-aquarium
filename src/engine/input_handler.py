import pygame as pg


class InputHandler:
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        cam = self.app.camera
        sim = self.app.sim
        scene = self.app.scene

        cam.handle_event(event)

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
