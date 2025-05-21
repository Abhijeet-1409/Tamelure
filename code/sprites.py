from settings import *
from pygame import Surface


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


