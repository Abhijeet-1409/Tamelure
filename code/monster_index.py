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
        keys = pygame.key.get_just_pressed()
        if keys[pygame.K_UP]:
            self.index -= 1
        if keys[pygame.K_DOWN]:
            self.index += 1

        self.index = self.index % len(self.monsters)

        if keys[pygame.K_SPACE]:
            if self.selected_index != None :
                selected_monster = self.monsters[self.selected_index]
                current_monster = self.monsters[self.index]
                self.monsters[self.index] = selected_monster
                self.monsters[self.selected_index] = current_monster
                self.selected_index = None
            else:
                self.selected_index = self.index

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
        # data
        monster = self.monsters[self.index]

        # main bg
        rect = pygame.FRect(self.main_rect.left + self.list_width,self.main_rect.top,self.main_rect.width - self.list_width,self.main_rect.height)
        pygame.draw.rect(self.display_surface,COLORS['dark'],rect,0,12,0,12,0)

        # monster display
        top_rect = pygame.FRect(rect.topleft,(rect.width,rect.height * 0.4))
        pygame.draw.rect(self.display_surface,COLORS[monster.element],top_rect,0,12,0,12,0,0)

        # monster animation
        self.frame_index += (ANIMATION_SPEED * dt)
        frame_list_length = len(self.monster_frames[monster.name]['idle'])
        monster_surf: pygame.Surface = self.monster_frames[monster.name]['idle'][int(self.frame_index) % frame_list_length]
        monster_rect = monster_surf.get_frect(center = top_rect.center)
        self.display_surface.blit(monster_surf,monster_rect)

        # name
        name_surf = self.fonts['bold'].render(monster.name,False,COLORS['white'])
        name_rect = name_surf.get_frect(topleft = top_rect.topleft + vector(10,10))
        self.display_surface.blit(name_surf,name_rect)

        # level
        level_surf = self.fonts['regular'].render(f'Lvl: {monster.level}',False,COLORS['white'])
        level_rect = level_surf.get_frect(bottomleft = top_rect.bottomleft + vector(10,-16))
        self.display_surface.blit(level_surf,level_rect)

        # xp bar
        bar_rect = pygame.FRect(level_rect.bottomleft,(100,4))
        draw_bar(self.display_surface,bar_rect,monster.xp,monster.level_up,COLORS['white'],COLORS['dark'])

        # element
        element_surf = self.fonts['regular'].render(monster.element,False,COLORS['white'])
        element_rect = element_surf.get_frect(bottomright = top_rect.bottomright + vector(-10,-10))
        self.display_surface.blit(element_surf,element_rect)

        # health and energy
        bar_data = {
            'width': rect.width * 0.45,
            'height': 30,
            'top': top_rect.bottom + rect.width * 0.03,
            'left_side': rect.left + rect.width / 4,
            'right_side': rect.left + rect.width * 3/4,
        }

        healthbar_rect = pygame.FRect((0,0), (bar_data['width'],bar_data['height'])).move_to(midtop = (bar_data['left_side'],bar_data['top']))
        draw_bar(self.display_surface,healthbar_rect,monster.health,monster.get_stat('max_health'),COLORS['red'],COLORS['black'],2)
        hp_text = self.fonts['regular'].render(f"HP: {int(monster.health)}/{int(monster.get_stat('max_health'))}",False,COLORS['white'])
        hp_rect = hp_text.get_frect(midleft = healthbar_rect.midleft + vector(10,0))
        self.display_surface.blit(hp_text,hp_rect)

        energybar_rect = pygame.FRect((0,0), (bar_data['width'],bar_data['height'])).move_to(midtop = (bar_data['right_side'],bar_data['top']))
        draw_bar(self.display_surface,energybar_rect,monster.health,monster.get_stat('max_health'),COLORS['blue'],COLORS['black'],2)
        energy_text = self.fonts['regular'].render(f"ENERGY: {int(monster.energy)}/{int(monster.get_stat('max_energy'))}",False,COLORS['white'])
        energy_rect = energy_text.get_frect(midleft = energybar_rect.midleft + vector(10,0))
        self.display_surface.blit(energy_text,energy_rect)

        # info
        sides = {'left': healthbar_rect.left, 'right': energybar_rect.left}
        info_height = rect.bottom - healthbar_rect.bottom

        # stats
        stats_rect = pygame.FRect(sides['left'],healthbar_rect.bottom,healthbar_rect.width,info_height).inflate(0,-60).move(0,15)
        stats_text_surf = self.fonts['regular'].render('Stats',False,COLORS['white'])
        stats_text_rect = stats_text_surf.get_frect(bottomleft = stats_rect.topleft)
        self.display_surface.blit(stats_text_surf,stats_text_rect)

        monster_stats = monster.get_stats()
        stat_height = stats_rect.height / len(monster_stats)

        for index, (stat, value) in enumerate(monster_stats.items()):
            single_stat_rect = pygame.FRect(sides['left'],stats_rect.top + index * stat_height,stats_rect.width,stat_height)

            # icon
            icon_surf: pygame.Surface = self.ui_frames[stat]
            icon_rect = icon_surf.get_frect(midleft = single_stat_rect.midleft + vector(5,0))
            self.display_surface.blit(icon_surf,icon_rect)

            # text
            text_surf = self.fonts['regular'].render(stat,False,COLORS['white'])
            text_rect = text_surf.get_frect(topleft = icon_rect.topleft + vector(30,-10))
            self.display_surface.blit(text_surf,text_rect)

            # bar
            bar_rect = pygame.FRect(text_rect.left,text_rect.bottom + 2,(single_stat_rect.width - (text_rect.left - single_stat_rect.left)),4)
            draw_bar(self.display_surface,bar_rect,value,self.max_stats[stat] * monster.level,COLORS['white'],COLORS['black'])

        # abilities
        abilities_rect = stats_rect.copy().move_to(left = sides['right'])
        abilities_text_surf = self.fonts['regular'].render('Abilities',False,COLORS['white'])
        abilities_text_rect = abilities_text_surf.get_frect(bottomleft = abilities_rect.topleft)
        self.display_surface.blit(abilities_text_surf,abilities_text_rect)

        for index, ability in enumerate(monster.get_abilites()):
            ability_element = ATTACK_DATA[ability]['element']
            ability_text_surf = self.fonts['regular'].render(ability,False,COLORS['black'])
            x = abilities_rect.left + (index % 2) * (abilities_rect.width / 2)
            y = 20 + abilities_rect.top + ((index // 2) * (ability_text_surf.get_height() + 20))
            ability_text_rect = ability_text_surf.get_frect(topleft = (x,y))
            pygame.draw.rect(self.display_surface,COLORS[ability_element],ability_text_rect.inflate(10,10),0,4)
            self.display_surface.blit(ability_text_surf,ability_text_rect)

    def update(self, dt: float):
        self.input()
        self.display_surface.blit(self.tint_surf,(0,0))
        self.display_list()
        self.display_main(dt)
