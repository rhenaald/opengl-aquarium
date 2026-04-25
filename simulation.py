"""
SimulationState - manages all interactive parameters for the aquarium simulation.
Pause/play, wave speed, bubble count, light intensity, water color presets.
"""


class SimulationState:
    # Water color presets (ambient fog color for underwater feel)
    WATER_PRESETS = [
        (0.04, 0.18, 0.32),   # Deep ocean blue
        (0.05, 0.25, 0.22),   # Tropical teal
        (0.10, 0.20, 0.38),   # Mediterranean blue
    ]
    PRESET_NAMES = ["Deep Ocean", "Tropical Teal", "Mediterranean"]

    def __init__(self):
        self.paused = False

        # Wave parameters
        self.wave_speed = 1.0       # multiplier
        self.wave_amplitude = 0.08  # height of wave distortion

        # Bubble parameters
        self.max_bubbles = 40
        self.bubble_rise_speed = 0.8

        # Light
        self.light_intensity = 1.0

        # Water color
        self.water_preset_idx = 0
        self.water_color = self.WATER_PRESETS[0]

        # Fish
        self.max_fish = 8

        # Caustic animation speed
        self.caustic_speed = 0.5

    def toggle_pause(self):
        self.paused = not self.paused

    def increase_wave_speed(self):
        self.wave_speed = min(5.0, round(self.wave_speed + 0.1, 2))

    def decrease_wave_speed(self):
        self.wave_speed = max(0.0, round(self.wave_speed - 0.1, 2))

    def increase_bubbles(self):
        self.max_bubbles = min(120, self.max_bubbles + 5)

    def decrease_bubbles(self):
        self.max_bubbles = max(0, self.max_bubbles - 5)

    def increase_light(self):
        self.light_intensity = min(3.0, round(self.light_intensity + 0.1, 2))

    def decrease_light(self):
        self.light_intensity = max(0.1, round(self.light_intensity - 0.1, 2))

    def next_water_preset(self):
        self.water_preset_idx = (self.water_preset_idx + 1) % len(self.WATER_PRESETS)
        self.water_color = self.WATER_PRESETS[self.water_preset_idx]
        return self.PRESET_NAMES[self.water_preset_idx]

    def set_water_preset(self, idx):
        self.water_preset_idx = idx % len(self.WATER_PRESETS)
        self.water_color = self.WATER_PRESETS[self.water_preset_idx]
        return self.PRESET_NAMES[self.water_preset_idx]