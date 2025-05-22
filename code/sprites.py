from pygame import Surface
from random import *

from settings import *
from monster import *
from support import *


# overworld sprites
class BaseSprite(pygame.sprite.Sprite):

    def __init__(self, pos: tuple[float, float], surf: Surface, groups: tuple[pygame.sprite.Group], z_index = WORLD_LAYERS['main']):
        super().__init__(*groups)
        self.image = surf
        self.z_index = z_index
        self.rect = self.image.get_frect(topleft=pos)
        self.y_sort = self.rect.centery
        self.hitbox = self.rect.copy()


class AnimatedSprite(BaseSprite):

    def __init__(self, pos: tuple[float, float], frames: list[Surface], groups: tuple[pygame.sprite.Group], z_index = WORLD_LAYERS['main']):
        self.frame_index, self.frames = 0, frames
        super().__init__(pos, frames[self.frame_index], groups, z_index)

    def animate(self, dt: float):
        self.frame_index += (ANIMATION_SPEED * dt)
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

    def update(self, dt: float, *args, **kwargs):
        super().update(*args, **kwargs)
        self.animate(dt)


class MonsterPatchSprite(BaseSprite):

    def __init__(self, pos: tuple[float, float], surf: Surface, groups: tuple[pygame.sprite.Group], biome: str):
        self.biome = biome
        super().__init__(pos, surf, groups, WORLD_LAYERS['main' if self.biome != 'sand' else 'bg'])
        self.y_sort -= 40


class BorderSprite(BaseSprite):

    def __init__(self, pos: tuple[float, float], surf: Surface, groups: tuple[pygame.sprite.Group]):
        super().__init__(pos, surf, groups)


class CollidableSprite(BaseSprite):

    def __init__(self, pos: tuple[float, float], surf: Surface, groups: tuple[pygame.sprite.Group]):
        super().__init__(pos, surf, groups)
        self.hitbox = self.rect.inflate(0,-(self.rect.height * 0.6))


class TransitionSprite(BaseSprite):

    def __init__(self, pos: tuple[float, float], size: tuple[float, float], target: tuple[str, str], groups: tuple[pygame.sprite.Group], z_index=WORLD_LAYERS['main']):
        surf = Surface(size)
        super().__init__(pos, surf, groups, z_index)
        self.target = target


# battle sprites
class MonsterSprite(pygame.sprite.Sprite):

    def __init__(self, pos: tuple[float, float], frames: dict[str, list[Surface]], groups: tuple[pygame.sprite.Group], monster: Monster, index: int, pos_index: int, entitiy: str):
        # data
        self.index = index
        self.pos_index = pos_index
        self.entity = entitiy
        self.monster = monster
        self.frame_index, self.frames, self.state = 0, frames, 'idle'
        self.animation_speed = ANIMATION_SPEED + uniform(-1,1)
        self.z_index = BATTLE_LAYERS['monster']

        # sprite setup
        super().__init__(*groups)
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(center = pos)

    def animate(self, dt: float):
        self.frame_index += (ANIMATION_SPEED * dt)
        self.image = self.frames[self.state][int(self.frame_index) % len(self.frames[self.state])]

    def update(self, dt: float, *args, **kwargs):
        super().update(*args, **kwargs)
        self.animate(dt)


class MonsterNameSprite(pygame.sprite.Sprite):

    def __init__(self, pos: tuple[float, float], monster_sprite: MonsterSprite, groups: tuple[pygame.sprite.Group], font: pygame.Font):
        super().__init__(*groups)
        self.monster_sprite = monster_sprite
        self.z_index = BATTLE_LAYERS['name']

        padding = 10
        text_surf = font.render(self.monster_sprite.monster.name,False,COLORS['black'])

        self.image = pygame.Surface((text_surf.width + 2 * padding,text_surf.height + 2 *padding))
        self.image.fill(COLORS['white'])
        self.rect = self.image.get_frect(midtop = pos)
        self.image.blit(text_surf,(padding,padding))


class MonsterLevelSprite(pygame.sprite.Sprite):

    def __init__(self, entity: str, anchor: tuple[float, float], monster_sprite: MonsterSprite, groups: tuple[pygame.sprite.Group], font: pygame.Font):
        super().__init__(*groups)
        self.monster_sprite = monster_sprite
        self.font = font
        self.z_index = BATTLE_LAYERS['name']

        self.image = pygame.Surface((60,26))
        self.rect = self.image.get_frect(topleft = anchor) if entity == 'player' else self.image.get_frect(topright = anchor)
        self.xp_rect = pygame.FRect(0,self.rect.height-2,self.rect.width,2)

    def update(self, dt: float, *args, **kwargs):
        super().update(*args, **kwargs)
        self.image.fill(COLORS['white'])

        text_surf = self.font.render(f"Lvl {self.monster_sprite.monster.level}",False,COLORS['black'])
        text_rect = text_surf.get_frect(center = (self.rect.width/2,self.rect.height/2))

        self.image.blit(text_surf,text_rect)

        draw_bar(self.image,self.xp_rect,self.monster_sprite.monster.xp,self.monster_sprite.monster.level_up,COLORS['black'],COLORS['white'])


class MonsterStatsSprite(pygame.sprite.Sprite):

    def __init__(self, pos: tuple[float, float], monster_sprite: MonsterSprite, size: tuple[float, float], groups: tuple[pygame.sprite.Group], font: pygame.Font):
        super().__init__(*groups)
        self.monster_sprite = monster_sprite
        self.image = pygame.Surface(size)
        self.rect = self.image.get_frect(midbottom = pos)
        self.font = font
        self.z_index = BATTLE_LAYERS['overlay']

    def update(self, _,*args, **kwargs):
        super().update(*args, **kwargs)
        self.image.fill(COLORS['white'])

        for index, (value, max_value) in enumerate(self.monster_sprite.monster.get_info()):
            color = (COLORS['red'],COLORS['blue'],COLORS['gray'])[index]
            if index <= 1:
                text_surf = self.font.render(f"{value}/{max_value}",False,COLORS['black'])
                text_rect = text_surf.get_frect(topleft = (self.rect.width * 0.05,index * (self.rect.height / 2)))
                bar_rect = pygame.FRect(text_rect.bottomleft + vector(0,-2),(self.rect.width * 0.9,4))
                self.image.blit(text_surf,text_rect)
                draw_bar(self.image,bar_rect,value,max_value,color,COLORS['black'],2)
            else:
                init_rect = pygame.FRect((0,self.rect.height-2),(self.rect.width,2))
                draw_bar(self.image,init_rect,value,max_value,color,COLORS['white'],0)