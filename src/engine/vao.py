from src.engine.shader_program import ShaderProgram
from src.engine.vbo import VBO


class VAO:
    def __init__(self, ctx):
        self.ctx = ctx
        self.vbo = VBO(ctx)
        self.program = ShaderProgram(ctx)
        self.vaos = {
            'color_cube': self.get_vao(self.program.programs['default_color'], self.vbo.vbos['color_cube']),
            'color_plane': self.get_vao(self.program.programs['default_color'], self.vbo.vbos['color_plane']),
        }

    def get_vao(self, program, vbo):
        return self.ctx.vertex_array(program, [(vbo.vbo, vbo.format, *vbo.attribs)])

    def destroy(self):
        for vao in self.vaos.values():
            vao.release()
        self.vbo.destroy()
        self.program.destroy()
