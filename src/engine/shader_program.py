class ShaderProgram:
    def __init__(self, ctx):
        self.ctx = ctx
        self.programs = {
            'default_color': self.get_program('default_color'),
        }

    def get_program(self, shader_program_name):
        with open(f'shaders/{shader_program_name}.vert', 'r', encoding='utf-8') as file:
            vertex_shader = file.read()
        with open(f'shaders/{shader_program_name}.frag', 'r', encoding='utf-8') as file:
            fragment_shader = file.read()
        return self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

    def destroy(self):
        for program in self.programs.values():
            program.release()
