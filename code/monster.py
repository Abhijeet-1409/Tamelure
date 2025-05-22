from random import randint

from settings import *
from game_data import *


class Monster():

    def __init__(self, name: str, level: int):
        self.name, self.level = name, level

        # stats
        self.element: str = MONSTER_DATA[name]['stats']['element']
        self.base_stats: dict[str, str | float] = MONSTER_DATA[name]['stats']
        self.health = self.base_stats['max_health'] * self.level
        self.energy = self.base_stats['max_energy'] * self.level
        self.health -= randint(0,self.health//2)
        self.energy -= randint(0,self.energy//2)
        self.initiative = randint(0,100)
        self.abilities: dict[int, str] = MONSTER_DATA[name]['abilities']

        # experience
        self.xp = randint(0,1000)
        self.level_up = self.level * 150

    def get_stat(self, stat: str):
        return self.base_stats[stat] * self.level

    def get_stats(self):
        return {
            'health': self.get_stat('max_health'),
            'energy': self.get_stat('max_energy'),
            'attack': self.get_stat('attack'),
            'defense': self.get_stat('defense'),
            'speed': self.get_stat('speed'),
            'recovery': self.get_stat('recovery')
        }

    def get_abilites(self):
        return [ ability for level, ability in self.abilities.items() if self.level >= level]

    def get_info(self):
        return (
            (self.health,self.get_stat('max_health')),
            (self.energy,self.get_stat('max_energy')),
            (self.initiative,100)
        )