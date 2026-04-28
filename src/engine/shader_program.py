"""
ShaderProgram - loads and manages all GLSL shader programs.

Programs:
  - phong_color   : standard Phong shading with solid color + wave distortion uniform
  - skybox       : cubemap background
  - water_volume : Beer-Lambert water absorption overlay
  - bubble        : transparent sphere with Fresnel rim
  - glass         : semi-transparent with tint
  - sand          : Phong + sandy color variation via noise-like gradient
  - fish          : animated fish with simple color stripe
"""

import os


class ShaderProgram:
    def __init__(self, ctx):
        self.ctx = ctx
        shader_dir = os.path.join(os.path.dirname(
            __file__), '..', '..', 'shaders')
        self.programs = {
            'skybox':      self._load(shader_dir, 'skybox'),
            'water_volume': self._load(shader_dir, 'water_volume'),
            'phong_color': self._load(shader_dir, 'phong_color'),
            'bubble':      self._load(shader_dir, 'bubble'),
            'glass':       self._load(shader_dir, 'glass'),
            'sand':        self._load(shader_dir, 'sand'),
            'fish':        self._load(shader_dir, 'fish'),
            'seaweed':     self._load(shader_dir, 'seaweed'),
            'water_surface':  self._load(shader_dir, 'water_surface'),
        }

    def _load(self, shader_dir, name):
        with open(f'{shader_dir}/{name}.vert', 'r', encoding='utf-8') as f:
            vert = f.read()
        with open(f'{shader_dir}/{name}.frag', 'r', encoding='utf-8') as f:
            frag = f.read()
        return self.ctx.program(vertex_shader=vert, fragment_shader=frag)

    def destroy(self):
        for prog in self.programs.values():
            prog.release()
