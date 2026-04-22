from src.objects.model import ColorCube, ColorPlane


class Scene:
    def __init__(self, app):
        self.app = app
        self.objects = []
        self.load()

    def add_object(self, obj):
        self.objects.append(obj)

    def load(self):
        add = self.add_object
        app = self.app

        add(ColorCube(app, pos=(0, 1, 0)))
        add(ColorPlane(app, scale=(10, 10, 10)))

    def update(self):
        for o in self.objects:
            o.update()
        
