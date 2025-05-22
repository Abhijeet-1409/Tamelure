from typing import Any

from settings import *
from monster import *
from sprites import *
from groups import *


class Battle():

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

        # groups
        self.battle_sprites = BattleSprites()
        self.player_sprites = pygame.sprite.Group()
        self.opponent_sprites = pygame.sprite.Group()

        self.setup()

    def setup(self):
        for entity, monsters in self.monster_data.items():
            for index, monster in { k: v for k, v in monsters.items() if k <= 2}.items():
                self.create_monster(monster,index,index,entity)

    def create_monster(self, monster: Monster, index: int, pos_index: int, entity: str):
        frames: dict[str, list[pygame.Surface]] = self.monster_frames['monsters'][monster.name]
        if entity == 'player':
            pos = sorted(list(BATTLE_POSITIONS['left'].values()),key= lambda tup: tup[1])[pos_index]
            groups = (self.battle_sprites, self.player_sprites)
            frames = { state: [ pygame.transform.flip(frame,True,False) for frame in frame_list ] for state, frame_list in frames.items()}
        else:
            pos = sorted(list(BATTLE_POSITIONS['right'].values()),key= lambda tup: tup[1])[pos_index]
            groups = (self.battle_sprites, self.opponent_sprites)

        monster_sprite = MonsterSprite(pos,frames,groups,monster,index,pos_index,entity)

        name_pos = monster_sprite.rect.midleft + vector(16,-70) if entity == 'player' else monster_sprite.rect.midright + vector(-40,-70)
        name_sprite = MonsterNameSprite(name_pos,monster_sprite,(self.battle_sprites,),self.fonts['regular'])

        anchor = name_sprite.rect.bottomleft if entity == 'player' else name_sprite.rect.bottomright
        MonsterLevelSprite(entity,anchor,monster_sprite,(self.battle_sprites,),self.fonts['small'])

        MonsterStatsSprite(monster_sprite.rect.midbottom + vector(0,20),monster_sprite,(150,48),(self.battle_sprites,),self.fonts['small'])

    def update(self, dt:float):
        self.display_surface.blit(self.bg_surf,(0,0))
        self.battle_sprites.update(dt)
        self.battle_sprites.draw()