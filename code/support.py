from settings import *
from entities import Entity
from os.path import join
from os import walk
from pytmx import TiledMap
from pytmx.util_pygame import load_pygame

# imports
def import_image(*path, alpha = True, format = 'png'):
	full_path = join(BASE_DIR,*path) + f'.{format}'
	surf = pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert()
	return surf

def import_folder(*path):
	frames = []
	for folder_path, sub_folders, image_names in walk(join(BASE_DIR,*path)):
		for image_name in sorted(image_names, key = lambda name: int(name.split('.')[0])):
			full_path = join(folder_path, image_name)
			surf = pygame.image.load(full_path).convert_alpha()
			frames.append(surf)
	return frames

def import_folder_dict(*path):
	frames: dict[str, pygame.Surface] = {}
	for folder_path, sub_folders, image_names in walk(join(BASE_DIR,*path)):
		for image_name in image_names:
			full_path = join(folder_path, image_name)
			surf = pygame.image.load(full_path).convert_alpha()
			frames[image_name.split('.')[0]] = surf
	return frames

def import_sub_folders(*path):
	frames = {}
	for _, sub_folders, __ in walk(join(BASE_DIR,*path)):
		if sub_folders:
			for sub_folder in sub_folders:
				frames[sub_folder] = import_folder(*path, sub_folder)
	return frames

def import_tilemap(cols, rows, *path):
	frames = {}
	surf = import_image(*path)
	cell_width, cell_height = surf.get_width() / cols, surf.get_height() / rows
	for col in range(cols):
		for row in range(rows):
			cutout_rect = pygame.Rect(col * cell_width, row * cell_height,cell_width,cell_height)
			cutout_surf = pygame.Surface((cell_width, cell_height))
			cutout_surf.fill('green')
			cutout_surf.set_colorkey('green')
			cutout_surf.blit(surf, (0,0), cutout_rect)
			frames[(col, row)] = cutout_surf
	return frames

def character_importer(cols, rows, *path):
	frame_dict = import_tilemap(cols,rows,*path)
	new_dict: dict[str,list[pygame.Surface]] = {}
	for row, direction in enumerate(['down','left','right','up']):
		new_dict[direction] = [frame_dict[(col,row)] for col in range(cols)]
		new_dict[f'{direction}_idle'] = [frame_dict[(0,row)]]
	return new_dict

def all_characters_import(*path):
	new_dict: dict[str,dict[str,list[pygame.Surface]]] = {}
	for _, _, image_files in walk(join(BASE_DIR,*path)):
		for image in image_files:
			name = image.split('.')[0]
			new_dict[name] = character_importer(4,4,*path,name)
	return new_dict

def coast_importer(cols, rows, *path):
	frame_dict = import_tilemap(cols,rows,*path)
	new_dict: dict[str,dict[str,list[pygame.Surface]]] = {}
	terrains = ['grass', 'grass_i', 'sand_i', 'sand', 'rock', 'rock_i', 'ice', 'ice_i']
	sides = {
		'topleft': (0,0), 'top': (1,0), 'topright': (2,0),
		'left': (0,1), 'right': (2,1), 'bottomleft': (0,2),
		'bottom': (1,2), 'bottomright': (2,2)}
	for index, terrain in enumerate(terrains):
		new_dict[terrain] = {}
		for key, pos in sides.items():
			new_dict[terrain][key] = [frame_dict[(pos[0] + index * 3, pos[1] + row)] for row in range(0, rows, 3)]
	return new_dict

def tmx_importer(*path):
	tmx_dict: dict[str, TiledMap] = {}
	for folder_path, sub_folder, file_names in walk(join(BASE_DIR,*path)):
		for file in file_names:
			map_name = file.split('.')[0]
			full_path = join(folder_path,file)
			tmx_dict[map_name] = load_pygame(full_path)
	return tmx_dict

def monster_importer(cols: int, rows: int, *path):
	monster_dict: dict[str, list[pygame.Surface]] = {}
	frame_dict = import_tilemap(cols,rows,*path)
	for row, state in enumerate(['idle','attack']):
		monster_dict[state] = []
		for col in range(cols):
			monster_dict[state].append(frame_dict[(col,row)])
	return monster_dict

def all_monsters_importer(*path):
	all_monster_dict: dict[str, dict[str, list[pygame.Surface]]] = {}
	for folder_path, _ , file_names in walk(join(BASE_DIR,*path)):
		for file in file_names:
			name = file.split('.')[0]
			all_monster_dict[name] = monster_importer(4,2,*path,name)
	return all_monster_dict


# game function
def draw_bar(surface: pygame.Surface, rect: pygame.FRect, value: int, max_value: int, color: pygame.typing.ColorLike, bg_color: pygame.typing.ColorLike, radius: int = 1):
	ratio = rect.width / max_value
	bg_rect = rect.copy()
	progress = max(0,min(rect.width,(ratio * value)))
	progress_rect = pygame.FRect(rect.topleft,(progress,rect.height))
	pygame.draw.rect(surface,bg_color,bg_rect,0,radius)
	pygame.draw.rect(surface,color,progress_rect,0,radius)

def check_connection(radius: float, entity: Entity, target: Entity, tolerance = 30):
	relation = vector(target.rect.center) - vector(entity.rect.center)
	if relation.length() < radius:
		if 	entity.facing_direction == 'left' and relation.x < 0 and  abs(relation.y) < tolerance or\
			entity.facing_direction == 'right'and relation.x > 0 and  abs(relation.y) < tolerance or\
			entity.facing_direction == 'up' and relation.y < 0 and  abs(relation.x) < tolerance or\
			entity.facing_direction == 'down'and relation.y > 0 and  abs(relation.x) < tolerance :
				return True
