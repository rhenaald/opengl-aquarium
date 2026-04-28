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
            vbo = v[vbo_name]
            return ctx.vertex_array(prog, [(vbo.vbo, vbo.format, *vbo.attribs)])

        self.vaos = {
            'skybox':       make('skybox',      'skybox'),
            'water_volume': make('water_volume', 'cube_pos'),
            'tank_wall':    make('glass',       'glass_panel'),
            'glass_cube':   make('glass',       'cube'),
            'sand_floor':   make('sand',         'sand_grid'),
            'rock':         make('phong_color',  'cube'),
            'coral':        make('phong_color',  'cylinder'),
            'seaweed':      make('seaweed',      'cylinder'),
            # ← realistic mesh
            'fish':         make('fish',         'fish_body'),
            'bubble':       make('bubble',       'sphere_tiny'),
            'solid_cube':   make('phong_color',  'cube'),
            'solid_sphere': make('phong_color',  'sphere'),
            'water_surface':  make('water_surface', 'water_grid'),
        }

    def destroy(self):
        for vao in self.vaos.values():
            vao.release()
        self.vbo.destroy()
        self.program.destroy()
