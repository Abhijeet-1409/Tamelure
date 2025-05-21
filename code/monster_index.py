import pygame.freetype
from settings import *
from monster  import *
from support import *


class MonsterIndex():

    def __init__(self, monsters: dict[str, Monster], fonts: dict[str, pygame.Font], monster_frames):
        self.display_surface = pygame.display.get_surface()
        self.fonts = fonts
        self.monsters = monsters
        self.frame_index = 0

        # frames
        self.icon_frames = monster_frames['icons']
        self.monster_frames = monster_frames['monsters']
        self.ui_frames = monster_frames['ui']

        # tint_surf
        self.tint_surf = pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT))
        self.tint_surf.set_alpha(200)

        # dimensions
        self.main_rect = pygame.FRect(0,0,WINDOW_WIDTH*0.6,WINDOW_HEIGHT*0.8).move_to(center=(WINDOW_WIDTH/2,WINDOW_HEIGHT/2))

        # list
        self.visible_items = 6
        self.list_width = self.main_rect.width * 0.3
        self.item_height = self.main_rect.height / self.visible_items
        self.index = 0
        self.selected_index: int | None = None

        # max values
        self.max_stats = {}
        for data in MONSTER_DATA.values():
            for stat, value in data['stats'].items():
                if stat != 'element':
                    if stat not in self.max_stats:
                        self.max_stats[stat] = value
                    else:
                        self.max_stats[stat] = max(self.max_stats[stat],value)
        self.max_stats['health'] = self.max_stats.pop('max_health')
        self.max_stats['energy'] = self.max_stats.pop('max_energy')

    def input(self):
        pass

    def display_list(self):
        pass

    def display_main(self, dt: float):
        pass

    def update(self, dt: float):
        self.input()
        self.display_surface.blit(self.tint_surf,(0,0))
        self.display_list()
        self.display_main(dt)
