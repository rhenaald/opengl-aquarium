import moderngl as mgl
import pygame as pg
import array
import os
import array

class UIOverlay:
    def __init__(self, ctx, win_size):
        self.ctx = ctx
        self.win_size = win_size
        
        self.ui_surface = pg.Surface(win_size, flags=pg.SRCALPHA)
        
        self.texture = self.ctx.texture(win_size, 4)
        self.texture.filter = (mgl.NEAREST, mgl.NEAREST)
        self.texture.swizzle = 'BGRA'
        
        with open('shaders/ui.vert', 'r') as f:
            vertex_shader = f.read()
            
        with open('shaders/ui.frag', 'r') as f:
            fragment_shader = f.read()

        self.prog = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )
        
        vertices = array.array('f', [
            -1.0, -1.0, 0.0, 1.0,
             1.0, -1.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 0.0,
             1.0,  1.0, 1.0, 0.0,
        ])
        
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, '2f 2f', 'in_vert', 'in_texcoord')])

    def draw(self):
        texture_data = self.ui_surface.get_view('1')
        
        self.texture.write(texture_data)
        
        self.ctx.enable(mgl.BLEND)
        self.texture.use()
        self.vao.render(mgl.TRIANGLE_STRIP)
        self.ctx.disable(mgl.BLEND)

    def clear(self):
        self.ui_surface.fill((0, 0, 0, 0))
