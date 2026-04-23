import pygame as pg
import pygame_gui


class AquariumUIManager:
    def __init__(self, win_size):
        self.win_size = win_size
        self.manager = pygame_gui.UIManager(win_size)
        
        self.sim_playing = True
        self.debug_mode = False
        
        self._build_ui()

    def _build_ui(self):
        button_width = 80
        button_height = 40
        padding = 10
        
        bottom_y = self.win_size[1] - button_height - padding
        
        self.play_pause_btn = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect((padding, bottom_y), (button_width, button_height)),
            text='Pause',
            manager=self.manager
        )
        
        self.stop_btn = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect((padding + button_width + padding, bottom_y), (button_width, button_height)),
            text='Stop',
            manager=self.manager
        )
        
        self.hamburger_btn = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect((padding, padding), (40, 40)),
            text='≡',
            manager=self.manager
        )
        
        panel_width = 250
        panel_height = self.win_size[1] - (padding * 3) - 40
        self.menu_panel = pygame_gui.elements.UIPanel(
            relative_rect=pg.Rect((padding, padding * 2 + 40), (panel_width, panel_height)),
            starting_height=1,
            manager=self.manager,
            visible=False
        )
        
        current_y = 10
        
        pygame_gui.elements.UILabel(
            relative_rect=pg.Rect((10, current_y), (panel_width - 20, 30)),
            text='Parameters',
            manager=self.manager,
            container=self.menu_panel
        )
        current_y += 35
        
        pygame_gui.elements.UIPanel(
            relative_rect=pg.Rect((10, current_y), (panel_width - 20, 2)),
            starting_height=2,
            manager=self.manager,
            container=self.menu_panel
        )
        current_y += 10
        
        self.debug_btn = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect((10, current_y), (panel_width - 20, 30)),
            text='Debug Mode: OFF',
            manager=self.manager,
            container=self.menu_panel
        )

    def process_events(self, event):
        consumed = self.manager.process_events(event)
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.play_pause_btn:
                self.sim_playing = not self.sim_playing
                self.play_pause_btn.set_text('Pause' if self.sim_playing else 'Play')
                consumed = True
                
            elif event.ui_element == self.stop_btn:
                self.sim_playing = False
                self.play_pause_btn.set_text('Play')
                consumed = True
                
            elif event.ui_element == self.hamburger_btn:
                if self.menu_panel.visible:
                    self.menu_panel.hide()
                else:
                    self.menu_panel.show()
                consumed = True
                    
            elif event.ui_element == self.debug_btn:
                self.debug_mode = not self.debug_mode
                self.debug_btn.set_text(f'Debug Mode: {"ON" if self.debug_mode else "OFF"}')
                consumed = True
                
        return consumed

    def update(self, delta_time):
        self.manager.update(delta_time)
        
    def draw(self, window_surface):
        self.manager.draw_ui(window_surface)
