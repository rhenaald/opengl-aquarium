import pygame as pg


class InputManager:
    def __init__(self):
        self.keys_pressed: set[int] = set()
        self.keys_down: set[int] = set()
        self.keys_up: set[int] = set()
        self.mouse_delta: tuple[int, int] = (0, 0)
        self.quit_requested: bool = False
        self.mouse_visible_toggle_requested: bool = False
        self.camera_mode_toggle_requested: bool = False
        self.orbit_zoom_in: bool = False
        self.orbit_zoom_out: bool = False
        
        self._prev_mouse_pos: tuple[int, int] = (0, 0)
    
    def update(self):
        self.keys_down.clear()
        self.keys_up.clear()
        self.mouse_delta = (0, 0)
        self.mouse_visible_toggle_requested = False
        self.camera_mode_toggle_requested = False
        self.orbit_zoom_in = False
        self.orbit_zoom_out = False
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit_requested = True
            
            elif event.type == pg.KEYDOWN:
                self.keys_pressed.add(event.key)
                self.keys_down.add(event.key)
                
                if event.key == pg.K_ESCAPE:
                    self.quit_requested = True
                elif event.key == pg.K_TAB:
                    self.camera_mode_toggle_requested = True
                elif event.key == pg.K_BACKQUOTE:
                    self.mouse_visible_toggle_requested = True
            
            elif event.type == pg.KEYUP:
                self.keys_pressed.discard(event.key)
                self.keys_up.add(event.key)
            
            elif event.type == pg.MOUSEMOTION:
                dx = event.rel[0]
                dy = event.rel[1]
                self.mouse_delta = (dx, dy)
            
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 4:  # scroll up
                    self.orbit_zoom_in = True
                elif event.button == 5:  # scroll down
                    self.orbit_zoom_out = True
    
    def is_pressed(self, key):
        return key in self.keys_pressed
    
    def is_down(self, key):
        return key in self.keys_down
    
    def is_up(self, key):
        return key in self.keys_up
    
    def get_mouse_delta(self):
        return self.mouse_delta
