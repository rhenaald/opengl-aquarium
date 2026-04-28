from pyglm import glm


class WaterVolume:
    def __init__(self, app):
        self.app = app
        self.camera = app.camera
        self.sim = app.sim
        self.vao = app.mesh.vao.vaos['water_volume']
        self.program = self.vao.program

        self.box_min = glm.vec3(-5.0, 0.0, -5.0)
        self.box_max = glm.vec3(5.0, 6.0, 5.0)
        self.m_model = glm.scale(
            glm.translate(glm.mat4(), glm.vec3(0.0, 3.0, 0.0)),
            glm.vec3(5.0, 3.0, 5.0),
        )

        self.program['m_proj'].write(self.camera.m_proj)
        self.program['m_model'].write(self.m_model)
        self.program['u_box_min'].write(self.box_min)
        self.program['u_box_max'].write(self.box_max)
        self.program['u_scene_depth'].value = 0

    def render(self):
        surface = self.app.scene.water_surface
        self.program['m_view'].write(self.camera.m_view)
        self.program['cam_pos'].write(self.camera.position)
        self.program['u_water_color'].write(glm.vec3(self.sim.water_color))
        self.program['u_absorption'].value = 0.18
        self.program['u_surface_base_y'].value = surface.pos.y
        self.program['u_wave_amplitude'].value = self.sim.wave_amplitude
        self.program['u_wave_frequency'].value = self.sim.wave_frequency
        self.program['u_wave_speed'].value = self.sim.wave_speed
        self.program['u_time'].value = self.app.time
        self.program['u_viewport_size'].write(glm.vec2(self.app.WIN_SIZE))
        inv_view_proj = glm.inverse(self.camera.m_proj * self.camera.m_view)
        self.program['u_inv_view_proj'].write(inv_view_proj)
        self.app.renderer.scene_depth.use(location=0)
        self.vao.render()
