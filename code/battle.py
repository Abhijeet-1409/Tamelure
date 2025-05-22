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
        pass

    def create_monster(self, monster: Monster, index: int, pos_index: int, entity: str):
        pass

    def update(self, dt:float):
        self.display_surface.blit(self.bg_surf,(0,0))
        self.battle_sprites.update(dt)
        self.battle_sprites.draw()