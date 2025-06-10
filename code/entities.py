from random import choice
from typing import Callable

from settings import *
from sprites import *
from game_data import *
from custom_timer import *


class Entity(pygame.sprite.Sprite):

    def __init__(self, pos: tuple[float,float], facing_direction: str,frames: dict[str,list[Surface]], groups: tuple[pygame.sprite.Group]):
        super().__init__(*groups)
        self.z_index = WORLD_LAYERS['main']

        # graphics
        self.facing_direction = facing_direction
        self.frame_index, self.frames = 0, frames

        # movement
        self.direction = vector(0,0)
        self.speed = 250
        self.blocked = False

        # sprite setup
        self.image = self.frames[self.facing_direction][self.frame_index]
        self.rect = self.image.get_frect(center = pos)
        self.hitbox = self.rect.inflate(-self.rect.width / 2, -60)

        self.y_sort = self.rect.centery

    def animate(self, dt: float):
        self.frame_index += (ANIMATION_SPEED * dt)
        self.image = self.frames[self.get_state()][int(self.frame_index) % len(self.frames[self.get_state()])]

    def get_state(self):
        moving = bool(self.direction)
        if moving:
            if self.direction.x != 0:
                self.facing_direction = 'right' if self.direction.x > 0 else 'left'
            if self.direction.y != 0:
                self.facing_direction = 'down' if self.direction.y > 0 else 'up'
        return f'{self.facing_direction}{'' if moving else '_idle'}'

    def block(self):
        self.blocked = True
        self.direction = vector(0,0)

    def unblock(self):
        self.blocked = False

    def change_facing_direction(self, target_pos: tuple[float,float]):
        relation = vector(target_pos) - vector(self.rect.center)
        if abs(relation.y) < 30:
            self.facing_direction = 'right' if relation.x > 0 else 'left'
        if abs(relation.x) < 30:
            self.facing_direction = 'down' if relation.y > 0 else 'up'

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self.y_sort = self.rect.centery


class Player(Entity):

    def __init__(
            self,
            pos: tuple[float, float],
            facing_direction: str,
            frames: dict[str,list[Surface]],
            groups: tuple[pygame.sprite.Group],
            collision_sprites: pygame.sprite.Group
        ):
        super().__init__(pos, facing_direction, frames, groups)
        self.collision_sprites = collision_sprites
        self.noticed = False
        self.character_approaching = False

    def input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])
        self.direction = self.direction.normalize() if self.direction else self.direction

    def move(self, dt: float):
        self.rect.centerx += (self.direction.x * self.speed * dt)
        self.hitbox.centerx = self.rect.centerx
        self.collision('horizontal')
        self.rect.centery += (self.direction.y * self.speed * dt)
        self.hitbox.centery = self.rect.centery
        self.collision('vertical')

    def collision(self, axis: str):
        for sprite in self.collision_sprites:
            if sprite.hitbox.colliderect(self.hitbox):
                if axis == 'horizontal':
                    if self.direction.x > 0 : self.hitbox.right = sprite.hitbox.left
                    if self.direction.x < 0 : self.hitbox.left = sprite.hitbox.right
                    self.rect.centerx = self.hitbox.centerx
                if axis == 'vertical':
                    if self.direction.y > 0 : self.hitbox.bottom = sprite.hitbox.top
                    if self.direction.y < 0 : self.hitbox.top = sprite.hitbox.bottom
                    self.rect.centery = self.hitbox.centery

    def update(self, dt: float, *args, **kwargs):
        super().update(*args, **kwargs)
        if not self.blocked:
            self.input()
            self.move(dt)
        self.animate(dt)


class Character(Entity):

    def __init__(
            self,
            pos: tuple[float, float],
            facing_direction: str,
            frames: dict[str,list[Surface]],
            groups: tuple[pygame.sprite.Group],
            character_data: dict,
            player: Player,
            create_dialog: Callable[['Character'],None],
            collision_sprites: pygame.sprite.Group,
            radius: float,
            nurse: bool,
            notice_sound: pygame.Sound
        ):
        super().__init__(pos, facing_direction, frames, groups)
        self.character_data = character_data
        self.player = player
        self.create_dialog = create_dialog
        self.collsion_rects: list[pygame.FRect] = [sprite.rect for sprite in collision_sprites if sprite is not self]
        self.nurse = nurse
        self.monsters: None | dict[int, Monster] = { index: Monster(name,level) for index, (name, level) in self.character_data['monsters'].items()} if 'monsters'in self.character_data else None

        # movement
        self.has_moved = False
        self.can_rotate = True
        self.has_noticed = False
        self.radius = radius
        self.view_directions = character_data['directions']

        self.timers: dict[str, Timer] = {
            'look_around': Timer(1500,True,True,self.random_view_direction),
            'notice': Timer(500,func=self.start_move)
        }
        self.notice_sound = notice_sound

    def random_view_direction(self):
        if self.can_rotate:
            self.facing_direction = choice(self.view_directions)

    def get_dialogs(self):
        is_defeated = self.character_data['defeated']
        return self.character_data['dialog'][ 'defeated' if is_defeated else 'default']

    def raycast(self):
        from support import check_connection
        if check_connection(self.radius,self,self.player) and self.has_los() and not self.has_moved and not self.has_noticed:
            self.player.block()
            self.player.change_facing_direction(self.rect.center)
            self.timers['notice'].activate()
            self.can_rotate = False
            self.has_noticed = True
            self.player.noticed = True
            self.player.character_approaching =  True
            self.notice_sound.play()

    def has_los(self):
        if vector(self.rect.center).distance_to(self.player.rect.center) < self.radius:
            collisions = [ bool(rects.clipline(self.rect.center,self.player.rect.center )) for rects in self.collsion_rects ]
            return not any(collisions)

    def start_move(self):
        relation = (vector(self.player.rect.center) - vector(self.rect.center)).normalize()
        self.direction = vector( round(relation.x), round(relation.y))

    def move(self, dt: float):
        if not self.has_moved and self.direction:
            if not self.hitbox.inflate(10,10).colliderect(self.player.hitbox):
                self.rect.center += (self.direction * self.speed * dt)
                self.hitbox.center = self.rect.center
            else:
                self.has_moved = True
                self.direction = vector(0,0)
                self.create_dialog(self)
                self.player.noticed = False
                self.player.character_approaching = False

    def update(self, dt: float, *args, **kwargs):
        super().update(*args, **kwargs)
        for timer in self.timers.values():
            timer.update()
        super().animate(dt)
        if self.character_data['look_around']:
            self.raycast()
            self.move(dt)
