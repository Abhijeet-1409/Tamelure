from settings import *
from sprites import *
from entities import *
from groups import *
from support import *
from dialog import *
from monster import *
from monster_index import *


class Game():

    # general
    def __init__(self):
        pygame.init()
        self.running = True
        self.clock = pygame.time.Clock()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
        pygame.display.set_caption("Tamelure")

        # player monsters
        self.player_monsters = {
            0: Monster('Charmadillo', 30),
			1: Monster('Friolera', 29),
			2: Monster('Larvea', 3),
			3: Monster('Atrox', 24),
			4: Monster('Sparchu', 24),
			5: Monster('Gulfin', 24),
			6: Monster('Jacana', 2),
			7: Monster('Pouch', 3)
        }

        # dummy monster
        self.dummy_monster = {
            0: Monster('Atrox', 24),
			1: Monster('Sparchu', 24),
			2: Monster('Gulfin', 24),
			3: Monster('Jacana', 2),
			4: Monster('Pouch', 3)
        }

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.character_sprites = pygame.sprite.Group()
        self.transition_sprites = pygame.sprite.Group()

        self.import_assets()
        self.setup(self.tmx_maps['world'],'house')

    def import_assets(self):
        self.tmx_maps = tmx_importer('data','maps')

        self.overworld_frames = {
            'water': import_folder('graphics','tilesets','water'),
            'coast': coast_importer(24,12,'graphics','tilesets','coast'),
            'characters': all_characters_import('graphics','characters'),
        }

        self.monster_frames = {
            'icons': import_folder_dict('graphics','icons'),
            'monsters': all_monsters_importer('graphics','monsters'),
            'ui': import_folder_dict('graphics','ui')
        }

        self.fonts = {
            'dialog': pygame.font.Font(join(BASE_DIR,'graphics','fonts','PixeloidSans.ttf'),30),
            'regular': pygame.font.Font(join(BASE_DIR,'graphics','fonts','PixeloidSans.ttf'),18),
            'small': pygame.font.Font(join(BASE_DIR,'graphics','fonts','PixeloidSans.ttf'),14),
            'bold': pygame.font.Font(join(BASE_DIR,'graphics','fonts','dogicapixelbold.otf'),20),
        }

    def setup(self, tmx_map: TiledMap, player_start_pos: str):
        # terrain and terrain top
        for layer in ['Terrain', 'Terrain Top']:
            for x, y, surf in tmx_map.get_layer_by_name(layer).tiles():
                BaseSprite((x*TILE_SIZE,y*TILE_SIZE),surf,(self.all_sprites,),WORLD_LAYERS['bg'])

        player_surf = pygame.Surface((100,200))
        player_surf.fill('red')
        player_frames = {}
        for direction in ['up','down','left','right']:
            player_frames[direction] = [player_surf]
            player_frames[f'{direction}_idle'] = [player_surf]
        self.player = Player((0,0),'down',player_frames,(self.all_sprites,),self.collision_sprites)

    def run(self):
        while self.running:
            # delta time
            dt = self.clock.tick(60) / 1000

            self.display_surface.fill('black')

            # event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # game logic
            self.all_sprites.update(dt)
            self.all_sprites.draw(self.player)

            pygame.display.update()

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()