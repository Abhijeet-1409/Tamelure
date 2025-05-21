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


