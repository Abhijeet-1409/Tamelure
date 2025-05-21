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
        bg_rect = pygame.FRect(self.main_rect.topleft,(self.list_width,self.main_rect.height))
        pygame.draw.rect(self.display_surface,COLORS['gray'],bg_rect,0,0,12,0,12,0)

        line_offset = vector(0,-2)
        v_offset = 0 if self.index < self.visible_items else -(self.index - self.visible_items  + 1) * self.item_height
        for index, monster in self.monsters.items():
            #colors
            bg_color = COLORS['gray'] if self.index != index else COLORS['light']
            text_color = COLORS['white'] if self.selected_index != index else COLORS['gold']


            top = self.main_rect.top + index * self.item_height + v_offset
            item_rect = pygame.FRect(self.main_rect.left,top,self.list_width,self.item_height)

            text_surf = self.fonts['regular'].render(monster.name,False,text_color)
            text_rect = text_surf.get_frect(midleft = item_rect.midleft + vector(90,10))

            icon_surf: pygame.Surface = self.icon_frames[monster.name]
            icon_rect = icon_surf.get_frect(center = item_rect.midleft + vector(45,0))


            if item_rect.colliderect(self.main_rect):
                if item_rect.collidepoint(self.main_rect.topleft):
                    pygame.draw.rect(self.display_surface,bg_color,item_rect,0,0,12)
                elif item_rect.collidepoint(self.main_rect.bottomleft + vector(1,-1)):
                    pygame.draw.rect(self.display_surface,bg_color,item_rect,0,0,0,0,12,0)
                else:
                    pygame.draw.rect(self.display_surface,bg_color,item_rect)

                self.display_surface.blit(text_surf,text_rect)
                self.display_surface.blit(icon_surf,icon_rect)

        # lines
        for i in range(1,min(self.visible_items,len(self.monsters))):
            left = self.main_rect.left
            right = self.main_rect.left + self.list_width
            y = self.main_rect.top + self.item_height * i
            pygame.draw.line(self.display_surface,COLORS['light-gray'],(left,y),(right,y))

        # shadow
        shadow_surf = pygame.Surface((4,self.main_rect.height))
        shadow_surf.set_alpha(100)
        self.display_surface.blit(shadow_surf,(self.main_rect.left + self.list_width - 4,self.main_rect.top))

    def display_main(self, dt: float):
        pass

    def update(self, dt: float):
        self.input()
        self.display_surface.blit(self.tint_surf,(0,0))
        self.display_list()
        self.display_main(dt)
