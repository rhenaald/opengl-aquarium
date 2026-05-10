from pyglm import glm


class PointLight:
    def __init__(self, position=(6, 8, 6), color=(1, 1, 1), intensity=1.0):
        self.position = glm.vec3(position)
        self.color = glm.vec3(color)
        self.intensity = intensity
        self.Ia = 0.20 * self.color * intensity
        self.Id = 0.85 * self.color * intensity
        self.Is = 0.40 * self.color * intensity
