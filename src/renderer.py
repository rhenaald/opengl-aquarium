class SceneRenderer:
    def __init__(self, app):
        self.app = app
        self.scene = app.scene

    def render(self):
        for obj in self.scene.objects:
            obj.render()
        self.scene.update()

    def destroy(self):
        return None
