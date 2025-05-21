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

        # transition / tint
        self.transition_target: tuple[str, str] | None = None
        self.tint_surf = Surface((WINDOW_WIDTH,WINDOW_HEIGHT))
        self.tint_mode = 'untint'
        self.tint_progress = 0
        self.tint_direction = -1
        self.tint_speed = 600

        self.import_assets()
        self.setup(self.tmx_maps['world'],'house')

        # overlays
        self.dialog_tree: DialogTree | None = None

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
        # clear the map
        for group in [self.all_sprites,self.collision_sprites,self.transition_sprites,self.character_sprites]:
            group.empty()

        # terrain and terrain top
        for layer in ['Terrain', 'Terrain Top']:
            for x, y, surf in tmx_map.get_layer_by_name(layer).tiles():
                BaseSprite((x*TILE_SIZE,y*TILE_SIZE),surf,(self.all_sprites,),WORLD_LAYERS['bg'])

        # water
        for obj in tmx_map.get_layer_by_name('Water'):
            for x in range(int(obj.x),int(obj.x + obj.width),TILE_SIZE):
                for y in range(int(obj.y),int(obj.y + obj.height),TILE_SIZE):
                    AnimatedSprite((x,y),self.overworld_frames['water'],(self.all_sprites,),WORLD_LAYERS['water'])

        # coast
        for obj in tmx_map.get_layer_by_name('Coast'):
            frames = self.overworld_frames['coast'][obj.properties['terrain']][obj.properties['side']]
            AnimatedSprite((obj.x,obj.y),frames,(self.all_sprites,),WORLD_LAYERS['bg'])

        # Objects
        for obj in tmx_map.get_layer_by_name('Objects'):
            if obj.name == 'top':
                BaseSprite((obj.x,obj.y),obj.image,(self.all_sprites,),WORLD_LAYERS['top'])
            else:
                CollidableSprite((obj.x,obj.y),obj.image,(self.all_sprites,self.collision_sprites))

        # transition objects
        for obj in tmx_map.get_layer_by_name('Transition'):
            TransitionSprite((obj.x,obj.y),(obj.width,obj.height),(obj.properties['target'],obj.properties['pos']),(self.transition_sprites,))

        # collision objects
        for obj in tmx_map.get_layer_by_name('Collisions'):
            BorderSprite((obj.x,obj.y),Surface((obj.width,obj.height)),(self.collision_sprites,))

        # monster patch
        for obj in tmx_map.get_layer_by_name('Monsters'):
            MonsterPatchSprite((obj.x,obj.y),obj.image,(self.all_sprites,),obj.properties['biome'])

        # Entities
        for obj in tmx_map.get_layer_by_name('Entities'):
            if obj.name == 'Player' and obj.properties['pos'] == player_start_pos:
                self.player = Player(
                    (obj.x,obj.y),
                    obj.properties['direction'],
                    self.overworld_frames['characters']['player'],
                    (self.all_sprites,),
                    self.collision_sprites)
            if obj.name == 'Character':
                Character(
                    (obj.x,obj.y),
                    obj.properties['direction'],
                    self.overworld_frames['characters'][obj.properties['graphic']],
                    (self.all_sprites,self.collision_sprites,self.character_sprites),
                    TRAINER_DATA[obj.properties['character_id']],
                    self.player,
                    self.create_dialog,
                    self.collision_sprites,
                    float(obj.properties['radius']))

    # dialog system
    def input(self):
        if not self.dialog_tree and not self.player.character_approaching:
            keys = pygame.key.get_just_pressed()
            character_list: list[Character] = self.character_sprites.sprites()
            if keys[pygame.K_SPACE]:
                for character in character_list:
                    if check_connection(character.radius,self.player,character):
                        self.player.block()
                        character.change_facing_direction(self.player.rect.center)
                        self.create_dialog(character)
                        character.can_rotate = False

    def create_dialog(self, character: Character):
        if not self.dialog_tree:
            self.dialog_tree = DialogTree(character,self.player,(self.all_sprites,),self.fonts['dialog'],self.end_dialog)

    def end_dialog(self, character: Character):
        self.dialog_tree = None
        self.player.unblock()

    # transition system
    def transition_check(self):
        sprites: list[TransitionSprite] = [sprite for sprite in self.transition_sprites if sprite.rect.colliderect(self.player.hitbox)]
        if sprites:
            self.player.block()
            self.transition_target = sprites[0].target
            self.tint_mode = 'tint'

    def tint_screen(self, dt: float):
        if self.tint_mode == 'untint':
            self.tint_progress -= (self.tint_speed * dt)

        if self.tint_mode == 'tint':
            self.tint_progress += (self.tint_speed * dt)
            if self.tint_progress >= 255:
                self.setup(self.tmx_maps[self.transition_target[0]],self.transition_target[1])
                self.tint_mode = 'untint'
                self.transition_target = None

        self.tint_progress = max(0, min(self.tint_progress,255))
        self.tint_surf.set_alpha(self.tint_progress)
        self.display_surface.blit(self.tint_surf,(0,0))

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
            self.input()
            self.transition_check()
            self.all_sprites.update(dt)
            self.all_sprites.draw(self.player)

            # overlays
            if self.dialog_tree: self.dialog_tree.update()

            self.tint_screen(dt)
            pygame.display.update()

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()