from pyglm import glm


class BaseModelColor:
    def __init__(self, app, vao_name, pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), color=(1.0, 1.0, 1.0)):
        self.app = app
        self.camera = app.camera
        self.light = app.light
        self.vao_name = vao_name
        self.vao = app.mesh.vao.vaos[vao_name]
        self.program = self.vao.program

        self.pos = glm.vec3(pos)
        self.rot = glm.vec3([glm.radians(a) for a in rot])
        self.scale = glm.vec3(scale)
        self.color = glm.vec3(color)
        self.m_model = self.get_model_matrix()

        self.on_init()

    def on_init(self):
        self.program['m_proj'].write(self.camera.m_proj)
        self.program['light.position'].write(self.light.position)
        self.program['light.Ia'].write(self.light.Ia)
        self.program['light.Id'].write(self.light.Id)
        self.program['light.Is'].write(self.light.Is)

    def get_model_matrix(self):
        m_model = glm.mat4()
        m_model = glm.translate(m_model, self.pos)
        m_model = glm.rotate(m_model, self.rot.z, glm.vec3(0, 0, 1))
        m_model = glm.rotate(m_model, self.rot.y, glm.vec3(0, 1, 0))
        m_model = glm.rotate(m_model, self.rot.x, glm.vec3(1, 0, 0))
        m_model = glm.scale(m_model, self.scale)
        return m_model

    def update(self):
        self.program['m_view'].write(self.camera.m_view)
        self.program['m_model'].write(self.m_model)
        self.program['cam_pos'].write(self.camera.position)
        self.program['u_color'].write(self.color)

    def render(self):
        self.update()
        self.vao.render()


class ColorCube(BaseModelColor):
    def __init__(self, app, vao_name='color_cube', pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), color=(1.0, 1.0, 1.0)):
        super().__init__(app, vao_name, pos, rot, scale, color)


class ColorPlane(BaseModelColor):
    def __init__(self, app, vao_name='color_plane', pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), color=(1.0, 1.0, 1.0)):
        super().__init__(app, vao_name, pos, rot, scale, color)
