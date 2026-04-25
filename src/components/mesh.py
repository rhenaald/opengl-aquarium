from src.engine.vao import VAO

class Mesh:
    def __init__(self, app):
        self.app = app
        self.vao = VAO(app.ctx)

    def destroy(self):
        self.vao.destroy()