from pygame import Surface
from random import *
from typing import Optional, Literal, Callable

from settings import *
from monster import *
from support import *
from custom_timer import *


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

    def __init__(self, pos: tuple[float, float], surf: Surface, groups: tuple[pygame.sprite.Group], biome: str, monster_level: int, patch_monsters: str):
        self.biome = biome
        super().__init__(pos, surf, groups, WORLD_LAYERS['main' if self.biome != 'sand' else 'bg'])
        self.y_sort -= 40
        self.level = monster_level
        self.monsters = patch_monsters.split(',')


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

    def __init__(
            self,
            pos: tuple[float, float],
            frames: dict[str, list[Surface]],
            groups: tuple[pygame.sprite.Group],
            monster: Monster,
            index: int,
            pos_index: int,
            entitiy: str,
            apply_attack: Callable[['MonsterSprite',Literal['burn','heal','battlecry','spark','scratch','splash','fire','explosion','annihilate','ice'],float],None],
            create_monster: Callable[[Monster,int,int,Literal['player','opponent']],None]
        ):
        # data
        self.index = index
        self.pos_index = pos_index
        self.entity = entitiy
        self.monster = monster
        self.frame_index, self.frames = 0, frames
        self.state: Literal['idle', 'attack'] = 'idle'
        self.animation_speed = ANIMATION_SPEED + uniform(-1,1)
        self.z_index = BATTLE_LAYERS['monster']
        self.highlight = False
        self.adjusted_frame_index = 0
        self.target_sprite: Optional['MonsterSprite'] = None
        self.current_attack: Optional[Literal['burn','heal','battlecry','spark','scratch','splash','fire','explosion','annihilate','ice']] = None
        self.next_monster_data: Optional[tuple[Monster,int,int,Literal['player','opponent']]] = None
        self.apply_attack = apply_attack
        self.create_monster = create_monster

        # sprite setup
        super().__init__(*groups)
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(center = pos)

        # timers
        self.timers = {
            'remove_highlight': Timer(300,func = lambda: self.set_highlight(False)),
            'kill': Timer(600,func=self.destroy)
        }

    def animate(self, dt: float):
        self.frame_index += (ANIMATION_SPEED * dt)

        self.adjusted_frame_index = int(self.frame_index) % len(self.frames[self.state])
        self.image = self.frames[self.state][self.adjusted_frame_index]

        if self.state == 'attack' and self.adjusted_frame_index == len(self.frames[self.state]) - 1:
            # apply attack
            self.apply_attack(self.target_sprite,self.current_attack,self.monster.get_base_damage(self.current_attack))
            self.state = 'idle'

        if self.highlight:
            white_surf = pygame.mask.from_surface(self.image).to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf

    def set_highlight(self, value: bool):
        self.highlight = value
        if value:
            self.timers['remove_highlight'].activate()

    def activate_attack(self, target_sprite: 'MonsterSprite', attack: Literal['burn','heal','battlecry','spark','scratch','splash','fire','explosion','annihilate','ice']):
        self.state = 'attack'
        self.frame_index = 0
        self.target_sprite = target_sprite
        self.current_attack = attack
        self.monster.reduce_energy(attack)

    def delayed_kill(self, new_monster: Optional[tuple[Monster,int,int,Literal['player','opponent']]] = None):
        if not self.timers['kill'].active:
            self.next_monster_data = new_monster
            self.timers['kill'].activate()

    def destroy(self):
        self.kill()
        if self.next_monster_data:
            self.create_monster(*self.next_monster_data)

    def update(self, dt: float, *args, **kwargs):
        super().update(*args, **kwargs)
        for timer in self.timers.values():
            timer.update()
        self.animate(dt)
        self.monster.update(dt)


class MonsterOutlineSprite(pygame.sprite.Sprite):

    def __init__(self, monster_sprite: MonsterSprite, groups: tuple[pygame.sprite.Group], outline_frames: dict[str, list[Surface]]):
        super().__init__(*groups)
        self.z_index = BATTLE_LAYERS['outline']
        self.monster_sprite = monster_sprite
        self.frames = outline_frames

        self.image = self.frames[self.monster_sprite.state][self.monster_sprite.adjusted_frame_index]
        self.rect = self.image.get_frect(center = self.monster_sprite.rect.center)

    def update(self, _, *args, **kwargs):
        super().update(*args, **kwargs)
        self.image = self.frames[self.monster_sprite.state][self.monster_sprite.adjusted_frame_index]
        if not self.monster_sprite.groups():
            self.kill()


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

    def update(self, _, *args, **kwargs):
        super().update(*args, **kwargs)
        if not self.monster_sprite.groups():
            self.kill()


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

        if not self.monster_sprite.groups():
            self.kill()


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
            value = int(value)
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

        if not self.monster_sprite.groups():
            self.kill()


class AttackSprite(AnimatedSprite):

    def __init__(self, pos: tuple[float, float], frames: list[Surface], groups: tuple[pygame.sprite.Group]):
        super().__init__(pos, frames, groups, BATTLE_LAYERS['overlay'])
        self.rect.center = pos

    def animate(self, dt: float):
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()


class TimedSprite(BaseSprite):

    def __init__(self, pos: tuple[float, float], surf: pygame.Surface, groups: tuple[pygame.sprite.Group], duration: int, update_all_monster: Callable[[Literal['pause', 'resume']], None]):
        super().__init__(pos, surf, groups, BATTLE_LAYERS['overlay'])
        self.rect.center = pos
        self.update_all_monster = update_all_monster
        self.death_timer = Timer(duration,autostart=True,func=self.destroy)

    def destroy(self):
        self.kill()
        self.update_all_monster('resume')

    def update(self, _, *args, **kwargs):
        super().update(*args, **kwargs)
        self.death_timer.update()