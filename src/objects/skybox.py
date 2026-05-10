import os

import pygame as pg
from pyglm import glm


class Skybox:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.camera = app.camera
        self.vao = app.mesh.vao.vaos['skybox']
        self.program = self.vao.program
        self.texture = self._load_cubemap()
        self.program['u_skybox'].value = 0
        self.program['m_proj'].write(self.camera.m_proj)

    def _load_cubemap(self):
        base_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'assets',
            'materials',
            'skybox',
            'sky_10_cubemap_2k',
            'sky_10_cubemap_2k',
        )
        face_names = ['px.png', 'nx.png', 'py.png', 'ny.png', 'pz.png', 'nz.png']
        surfaces = []
        for name in face_names:
            path = os.path.normpath(os.path.join(base_dir, name))
            surfaces.append(pg.image.load(path).convert())

        size = surfaces[0].get_size()
        texture = self.ctx.texture_cube(size=size, components=3)
        for face, surface in enumerate(surfaces):
            if surface.get_size() != size:
                raise ValueError('Skybox cubemap faces must have the same size')
            texture.write(face, pg.image.tostring(surface, 'RGB', False), alignment=1)

        texture.build_mipmaps()
        return texture

    def render(self):
        view = glm.mat4(glm.mat3(self.camera.m_view))
        self.program['m_view'].write(view)
        self.texture.use(location=0)
        self.vao.render()

    def destroy(self):
        self.texture.release()
