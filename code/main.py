from typing import Literal
from random import choice

from settings import *
from sprites import *
from entities import *
from groups import *
from support import *
from dialog import *
from monster import *
from monster_index import *
from battle import *
from custom_timer import *
from evolution import *


class Game():

    # general
    def __init__(self):
        pygame.init()
        self.running = True
        self.clock = pygame.time.Clock()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
        pygame.display.set_caption("Tamelure")
        self.encounter_timer = Timer(2000,func=self.monster_encounter)

        # player monsters
        self.player_monsters = {
            0: Monster("Plumette", 6),
            1: Monster("Sparchu", 6),
            2: Monster("Finsta", 7)
        }

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.character_sprites = pygame.sprite.Group()
        self.transition_sprites = pygame.sprite.Group()
        self.monster_patch_sprites = pygame.sprite.Group()

        # transition / tint
        self.transition_target: tuple[str, str] | Battle | str |None = None
        self.tint_surf = Surface((WINDOW_WIDTH,WINDOW_HEIGHT))
        self.tint_mode: Literal['untint','tint'] = 'untint'
        self.tint_progress = 0
        self.tint_direction = -1
        self.tint_speed = 600

        self.import_assets()
        self.setup(self.tmx_maps['world'],'house')
        self.audios['overworld'].play(-1)

        # overlays
        self.dialog_tree: DialogTree | None = None
        self.monster_index = MonsterIndex(self.player_monsters,self.fonts,self.monster_frames)
        self.index_open = False
        self.battle: Battle | None = None
        self.evolution: Evolution | None = None

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
            'ui': import_folder_dict('graphics','ui'),
            'attacks': attack_importer('graphics','attacks')
        }

        self.monster_frames['outlines'] = outline_creator(self.monster_frames['monsters'],4)

        self.fonts = {
            'dialog': pygame.font.Font(join(BASE_DIR,'graphics','fonts','PixeloidSans.ttf'),30),
            'regular': pygame.font.Font(join(BASE_DIR,'graphics','fonts','PixeloidSans.ttf'),18),
            'small': pygame.font.Font(join(BASE_DIR,'graphics','fonts','PixeloidSans.ttf'),14),
            'bold': pygame.font.Font(join(BASE_DIR,'graphics','fonts','dogicapixelbold.otf'),20),
        }

        self.bg_frames = import_folder_dict('graphics','backgrounds')
        self.star_animation_frames = import_folder('graphics','other','star animation')

        self.audios = audio_importer('audio')

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
            MonsterPatchSprite((obj.x,obj.y),obj.image,(self.all_sprites,self.monster_patch_sprites),obj.properties['biome'],obj.properties['level'],obj.properties['monsters'])

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
                    float(obj.properties['radius']),
                    obj.properties['character_id']=='Nurse',
                    self.audios['notice'])

    # dialog system
    def input(self):
        if not self.dialog_tree and not self.player.character_approaching and not self.battle and not self.evolution:
            keys = pygame.key.get_just_pressed()
            character_list: list[Character] = self.character_sprites.sprites()
            if keys[pygame.K_SPACE] and not self.index_open:
                for character in character_list:
                    if check_connection(character.radius,self.player,character):
                        self.player.block()
                        character.change_facing_direction(self.player.rect.center)
                        self.create_dialog(character)
                        character.can_rotate = False

            if keys[pygame.K_RETURN]:
                    self.index_open = not self.index_open
                    self.player.block() if self.index_open else self.player.unblock()

    def create_dialog(self, character: Character):
        if not self.dialog_tree:
            self.dialog_tree = DialogTree(character,self.player,(self.all_sprites,),self.fonts['dialog'],self.end_dialog)

    def end_dialog(self, character: Character):
        self.dialog_tree = None
        if character.nurse:
            for monster in self.player_monsters.values():
                monster.health = monster.get_stat('max_health')
                monster.health = monster.get_stat('max_energy')
            self.player.unblock()
        elif not character.character_data['defeated']:
            self.audios['overworld'].stop()
            self.audios['battle'].play(-1)
            self.transition_target = Battle(
                self.player_monsters,
                character.monsters,
                self.monster_frames,
                self.bg_frames[character.character_data['biome']],
                self.fonts,
                self.end_battle,
                character,
                self.audios)
            self.tint_mode = 'tint'
        else:
            self.player.unblock()
            self.check_evolution()

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
                if type(self.transition_target) == Battle:
                    self.battle = self.transition_target
                elif type(self.transition_target) == str and self.transition_target == 'level':
                    self.battle = None
                else:
                    self.setup(self.tmx_maps[self.transition_target[0]],self.transition_target[1])
                self.tint_mode = 'untint'
                self.transition_target = None

        self.tint_progress = max(0, min(self.tint_progress,255))
        self.tint_surf.set_alpha(self.tint_progress)
        self.display_surface.blit(self.tint_surf,(0,0))

    def  end_battle(self, character: Character | None):
        self.audios['battle'].stop()
        self.transition_target = 'level'
        self.tint_mode = 'tint'
        if character:
            character.character_data['defeated'] = True
            self.create_dialog(character)
        elif not self.evolution:
            self.player.unblock()
            self.check_evolution()

    def check_evolution(self):
        for index, monster in self.player_monsters.items():
            if monster.evolution:
                if monster.level == monster.evolution[1]:
                    self.audios['evolution'].play()
                    self.player.block()
                    self.evolution = Evolution(
                        self.monster_frames['monsters'],
                        monster.name,
                        monster.evolution[0],
                        self.fonts['bold'],
                        self.end_evolution,
                        self.star_animation_frames
                    )
                    self.player_monsters[index] = Monster(monster.evolution[0],monster.evolution[1])
        if not self.evolution:
            self.audios['overworld'].play(-1)

    def end_evolution(self):
        self.evolution = None
        self.player.unblock()
        self.audios['evolution'].stop()
        self.audios['overworld'].play(-1)

    # monster encounters
    def check_monster(self):
        healthy_player_monster: list[Monster] = [ monster for monster in self.player_monsters.values() if monster.health > 10 ]
        monster_patches: list[MonsterPatchSprite] = self.monster_patch_sprites.sprites()
        if [patch for patch in monster_patches if patch.rect.colliderect(self.player.hitbox)] and not self.battle and self.player.direction and len(healthy_player_monster) >= 3:
            if not self.encounter_timer.active:
                self.encounter_timer.activate()

    def monster_encounter(self):
        self.reorder_player_monster()
        monster_patches: list[MonsterPatchSprite] = [ patch for patch in self.monster_patch_sprites.sprites() if patch.rect.colliderect(self.player.hitbox)]
        if monster_patches and self.player.direction:
            self.encounter_timer.duration = randint(800, 2500)
            self.player.block()
            self.audios['overworld'].stop()
            self.audios['battle'].play(-1)
            self.transition_target = Battle(
                self.player_monsters,
                { index: Monster(name,monster_patches[0].level) for index, name in enumerate(monster_patches[0].monsters) },
                self.monster_frames,
                self.bg_frames[monster_patches[0].biome],
                self.fonts,
                self.end_battle,
                None,
                self.audios)
            self.tint_mode = 'tint'
        self.encounter_timer.deactivate()

    def reorder_player_monster(self):
        index_monster_list = [ (index,monster) for index, monster in self.player_monsters.items()]
        is_reorder_required = False
        for index,monster in index_monster_list[:3]:
            if monster.health < 20:
                is_reorder_required = True
        if is_reorder_required:
            unhealthy_monster = [ (index,monster) for index, monster in index_monster_list if monster.health < 20 and index < 3]
            healthy_monster = [ (index,monster) for index, monster in index_monster_list if monster.health > 20 and index >= 3]
            healthy_monster = sorted(healthy_monster, reverse = True, key = lambda index_monster : index_monster[1].health )
            min_monster_list_len = min(len(unhealthy_monster),len(healthy_monster))
            for pos in range(min_monster_list_len):
                key, key_monster = unhealthy_monster[pos]
                index, index_monster = healthy_monster[pos]
                self.player_monsters[key] = index_monster
                self.player_monsters[index] = key_monster

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
            self.encounter_timer.update()
            self.input()
            self.transition_check()
            self.all_sprites.update(dt)
            self.all_sprites.draw(self.player)
            self.check_monster()

            # overlays
            if self.dialog_tree: self.dialog_tree.update()
            if self.index_open: self.monster_index.update(dt)
            if self.battle: self.battle.update(dt)
            if self.evolution: self.evolution.update(dt)

            self.tint_screen(dt)
            pygame.display.update()

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()