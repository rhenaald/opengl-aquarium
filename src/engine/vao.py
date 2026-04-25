from src.engine.shader_program import ShaderProgram
from src.engine.vbo import VBO


class VAO:
    def __init__(self, ctx):
        self.ctx = ctx
        self.vbo = VBO(ctx)
        self.program = ShaderProgram(ctx)

        p = self.program.programs
        v = self.vbo.vbos

        def make(prog_name, vbo_name):
            prog = p[prog_name]
            vbo  = v[vbo_name]
            return ctx.vertex_array(prog, [(vbo.vbo, vbo.format, *vbo.attribs)])

        self.vaos = {
            'tank_wall':    make('glass',       'glass_panel'),
            'sand_floor':   make('sand',         'plane'),
            'rock':         make('phong_color',  'cube'),
            'coral':        make('phong_color',  'cylinder'),
            'seaweed':      make('seaweed',      'cylinder'),
            'fish':         make('fish',         'fish_body'),   # ← realistic mesh
            'bubble':       make('bubble',       'sphere_tiny'),
            'solid_cube':   make('phong_color',  'cube'),
            'solid_sphere': make('phong_color',  'sphere'),
        }

    def destroy(self):
        for vao in self.vaos.values():
            vao.release()
        self.vbo.destroy()
        self.program.destroy()