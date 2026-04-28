from pyglm import glm


class AquariumLight:
    def __init__(self):
        self.position = glm.vec3(0.0, 9.0, 0.0)
        self.base_color = glm.vec3(0.85, 0.95, 1.0)
        self.intensity = 1.0
        self._recompute()

    def _recompute(self):
        c = self.base_color * self.intensity
        self.Ia = 0.18 * c
        self.Id = 0.80 * c
        self.Is = 0.50 * c

    def set_intensity(self, val):
        self.intensity = max(0.1, min(3.0, val))
        self._recompute()
