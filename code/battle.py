from typing import Any, Literal, Optional

from settings import *
from monster import *
from sprites import *
from groups import *


class Battle():

    # main
    def __init__(
            self,
            player_monsters: dict[int, Monster],
            opponent_monsters: dict[int, Monster],
            monster_frames: dict[str, Any],
            bg_surf: pygame.Surface,
            fonts: dict[str, pygame.Font]
        ):
        self.display_surface = pygame.display.get_surface()
        self.monster_frames = monster_frames
        self.bg_surf = bg_surf
        self.fonts = fonts
        self.monster_data = {'player': player_monsters, 'opponent': opponent_monsters}
        self.available_monsters: dict[int,Monster] = {}

        # groups
        self.battle_sprites = BattleSprites()
        self.player_sprites = pygame.sprite.Group()
        self.opponent_sprites = pygame.sprite.Group()

        # control
        self.current_monster_sprite: MonsterSprite | None = None
        self.selection_mode: Optional[Literal['general','monster','attacks','switch','target']] = None
        self.selection_side: Literal['player','opponent'] = 'player'
        self.indexes = {
            'general': 0,
            'monster': 0,
            'attacks': 0,
            'switch': 0,
            'target': 0,
        }

        self.setup()

    def setup(self):
        for entity, monsters in self.monster_data.items():
            for index, monster in { k: v for k, v in monsters.items() if k <= 2}.items():
                self.create_monster(monster,index,index,entity)

    def create_monster(self, monster: Monster, index: int, pos_index: int, entity: str):
        frames: dict[str, list[pygame.Surface]] = self.monster_frames['monsters'][monster.name]
        outline_frames: dict[str, list[pygame.Surface]] = self.monster_frames['outlines'][monster.name]
        if entity == 'player':
            pos = sorted(list(BATTLE_POSITIONS['left'].values()),key= lambda tup: tup[1])[pos_index]
            groups = (self.battle_sprites, self.player_sprites)
            frames = { state: [ pygame.transform.flip(frame,True,False) for frame in frame_list ] for state, frame_list in frames.items()}
            outline_frames = { state: [ pygame.transform.flip(frame,True,False) for frame in frame_list ] for state, frame_list in outline_frames.items()}
        else:
            pos = sorted(list(BATTLE_POSITIONS['right'].values()),key= lambda tup: tup[1])[pos_index]
            groups = (self.battle_sprites, self.opponent_sprites)

        monster_sprite = MonsterSprite(pos,frames,groups,monster,index,pos_index,entity)
        MonsterOutlineSprite(monster_sprite,(self.battle_sprites,),outline_frames)

        name_pos = monster_sprite.rect.midleft + vector(16,-70) if entity == 'player' else monster_sprite.rect.midright + vector(-40,-70)
        name_sprite = MonsterNameSprite(name_pos,monster_sprite,(self.battle_sprites,),self.fonts['regular'])

        anchor = name_sprite.rect.bottomleft if entity == 'player' else name_sprite.rect.bottomright
        MonsterLevelSprite(entity,anchor,monster_sprite,(self.battle_sprites,),self.fonts['small'])

        MonsterStatsSprite(monster_sprite.rect.midbottom + vector(0,20),monster_sprite,(150,48),(self.battle_sprites,),self.fonts['small'])

    def input(self):
        if self.selection_mode and self.current_monster_sprite:
            limiter = 0
            keys = pygame.key.get_just_pressed()

            match self.selection_mode:
                case 'general': limiter = len(BATTLE_CHOICES['full'])
                case 'attacks': limiter = len(self.current_monster_sprite.monster.get_abilities(all=False))
                case 'switch': limiter = len(self.available_monsters)

            if keys[pygame.K_DOWN]:
                self.indexes[self.selection_mode] = (self.indexes[self.selection_mode] + 1) % limiter
            if keys[pygame.K_UP]:
                self.indexes[self.selection_mode] = (self.indexes[self.selection_mode] - 1) % limiter
            if keys[pygame.K_SPACE]:
                if self.selection_mode == 'general':
                    if self.indexes['general'] == 0:
                        self.selection_mode = 'attacks'

                    if self.indexes['general'] == 1:
                        self.update_all_monster('resume')
                        self.current_monster_sprite, self.selection_mode = None, None
                        self.indexes['general'] = 0

                    if self.indexes['general'] == 2:
                        self.selection_mode = 'switch'

                    if self.indexes['general'] == 3:
                        print('catch')
            if keys[pygame.K_BACKSPACE]:
                if self.selection_mode in ('attacks', 'switch', 'target'):
                    self.selection_mode = 'general'

    # battle setup
    def check_active(self):
        player_monster_sprites: list[MonsterSprite] = self.player_sprites.sprites()
        for monster_sprite in player_monster_sprites:
            if monster_sprite.monster.initiative >= 100:
                self.update_all_monster('pause')
                monster_sprite.monster.initiative = 0
                monster_sprite.set_highlight(True)
                self.current_monster_sprite = monster_sprite
                if self.player_sprites in monster_sprite.groups():
                    self.selection_mode = 'general'

    def update_all_monster(self, option: Literal['pause','resume']):
        player_monster_sprites: list[MonsterSprite] = self.player_sprites.sprites()
        for monster_sprite in player_monster_sprites:
            monster_sprite.monster.paused = True if option == 'pause' else False

    # ui
    def draw_ui(self):
        if self.current_monster_sprite:
            if self.selection_mode == 'general':
                self.draw_general()
            if self.selection_mode == 'attacks':
                self.draw_attacks()
            if self.selection_mode == 'switch':
                self.draw_switch()

    def draw_general(self):
        for index, (option, data_dict) in enumerate(BATTLE_CHOICES['full'].items()) :
            if index == self.indexes['general']:
                surf: pygame.Surface = self.monster_frames['ui'][f"{data_dict['icon']}_highlight"]
            else:
                surf: pygame.Surface = pygame.transform.grayscale(self.monster_frames['ui'][f"{data_dict['icon']}"])
            rect = surf.get_frect(center = self.current_monster_sprite.rect.midright + data_dict['pos'])
            self.display_surface.blit(surf,rect)

    def draw_attacks(self):
        # data
        ablities = self.current_monster_sprite.monster.get_abilities(all=False)
        width, height = 150, 200
        visible_attacks = 4
        item_height = height / visible_attacks
        v_offset = 0 if self.indexes['attacks'] < visible_attacks else -(self.indexes['attacks'] - visible_attacks + 1) * item_height

        # bg
        bg_rect = pygame.FRect((0,0),(width,height)).move_to(midleft = self.current_monster_sprite.rect.midright + vector(20,0))
        pygame.draw.rect(self.display_surface,COLORS['white'],bg_rect,0,5)

        for index, ability in enumerate(ablities):
            selected = index == self.indexes['attacks']

            # text
            if selected:
                element = ATTACK_DATA[ability]['element']
                text_color = COLORS[element] if element != 'normal' else COLORS['black']
            else:
                text_color = COLORS['black'] if selected else COLORS['light']
            text_surf = self.fonts['regular'].render(ability,False,text_color)

            # rect
            text_rect = text_surf.get_frect(center = (bg_rect.midtop + vector(0,(item_height/2) + (index*item_height) + v_offset)))
            text_bg_rect = pygame.FRect((0,0),(width, item_height)).move_to(center = text_rect.center)

            # draw
            if bg_rect.collidepoint(text_rect.center):
                if selected:
                    if text_bg_rect.collidepoint(bg_rect.topleft):
                        pygame.draw.rect(self.display_surface,COLORS['dark white'],text_bg_rect,0,0,5,5,0)
                    elif text_bg_rect.collidepoint(bg_rect.midbottom + vector(0,-1)):
                        pygame.draw.rect(self.display_surface,COLORS['dark white'],text_bg_rect,0,0,0,0,5,5)
                    else:
                        pygame.draw.rect(self.display_surface,COLORS['dark white'],text_bg_rect)
                self.display_surface.blit(text_surf,text_rect)

    def draw_switch(self):
        width, height = 300, 320
        visible_monster = 4
        item_height = height / visible_monster
        v_offset = 0 if self.indexes['switch'] < visible_monster else -(self.indexes['switch'] - visible_monster + 1) * item_height

        # bg
        bg_rect = pygame.FRect((0,0),(width,height)).move_to(midleft = self.current_monster_sprite.rect.midright + vector(20,0))
        pygame.draw.rect(self.display_surface,COLORS['white'],bg_rect,0,5)

        active_monsters: list[tuple[int,Monster]] = [(monster_sprite.index,monster_sprite.monster) for monster_sprite in self.player_sprites.sprites()]
        self.available_monsters = { index: monster for index, monster in self.monster_data['player'].items() if (index,monster) not in active_monsters and monster.health > 0}

        for index, monster in enumerate(self.available_monsters.values()):
            selected = index == self.indexes['switch']
            item_bg_rect = pygame.FRect((0,0),(width,item_height)).move_to(midleft = (bg_rect.left, bg_rect.top + (item_height/2) + (index*item_height) + v_offset))

            text_color = COLORS['red'] if selected else COLORS['black']

            # icon
            icon_surf: pygame.Surface = self.monster_frames['icons'][monster.name]
            icon_rect = icon_surf.get_frect(midleft = (bg_rect.topleft + vector(10, (item_height/2) + (index*item_height) + v_offset)))

            # text
            text_surf = self.fonts['regular'].render(f"{monster.name} ({monster.level})",False,text_color)
            text_rect = text_surf.get_frect(topleft = (bg_rect.left + 90,icon_rect.top))

            # draw
            if bg_rect.collidepoint(item_bg_rect.center):
                if selected:
                    if item_bg_rect.collidepoint(bg_rect.topleft):
                        pygame.draw.rect(self.display_surface,COLORS['dark white'],item_bg_rect,0,0,5,5,0)
                    elif item_bg_rect.collidepoint(bg_rect.midbottom + vector(0,-1)):
                        pygame.draw.rect(self.display_surface,COLORS['dark white'],item_bg_rect,0,0,0,0,5,5)
                    else:
                        pygame.draw.rect(self.display_surface,COLORS['dark white'],item_bg_rect)

                self.display_surface.blit(icon_surf,icon_rect)
                self.display_surface.blit(text_surf,text_rect)

                # stats
                for index, (stat,length) in enumerate([('health',100),('energy',80)]):
                    color = [COLORS['red'],COLORS['blue']][index]
                    value = monster.health if stat == 'health' else monster.energy
                    bar_rect = pygame.FRect(text_rect.bottomleft + vector(0,+ index * 6),(length,4))
                    draw_bar(self.display_surface,bar_rect,value,monster.get_stat(f"max_{stat}"),color,COLORS['black'])

    def update(self, dt:float):
        # updates
        self.input()
        self.battle_sprites.update(dt)
        self.check_active()

        # drawing
        self.display_surface.blit(self.bg_surf,(0,0))
        self.battle_sprites.draw(self.current_monster_sprite)
        self.draw_ui()