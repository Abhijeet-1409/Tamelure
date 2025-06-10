from random import randint
from typing import Literal

from settings import *
from game_data import *


class Monster():

    def __init__(self, name: str, level: int):
        self.name, self.level = name, level
        self.paused = False

        # stats
        self.element: str = MONSTER_DATA[name]['stats']['element']
        self.base_stats: dict[str, str | float] = MONSTER_DATA[name]['stats']
        self.health = self.base_stats['max_health'] * self.level
        self.energy = self.base_stats['max_energy'] * self.level
        self.initiative = 0
        self.abilities: dict[int, str] = MONSTER_DATA[name]['abilities']
        self.defending = False

        # experience
        self.xp = 0
        self.level_up = self.level * 150
        self.evolution: tuple[str, int] | None = MONSTER_DATA[self.name]['evolve']

    def __repr__(self):
        return f"Monster: {self.name}, Lvl: {self.level}"

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

    def get_abilities(self, all: bool = True):
        if all:
            return [ ability for level, ability in self.abilities.items() if self.level >= level]
        return [ ability for level, ability in self.abilities.items() if self.level >= level and ATTACK_DATA[ability]['cost'] < self.energy]

    def get_info(self):
        return (
            (self.health,self.get_stat('max_health')),
            (self.energy,self.get_stat('max_energy')),
            (self.initiative,100)
        )

    def reduce_energy(self, attack: Literal['burn','heal','battlecry','spark','scratch','splash','fire','explosion','annihilate','ice']):
        self.energy -= ATTACK_DATA[attack]['cost']

    def get_base_damage(self, attack: Literal['burn','heal','battlecry','spark','scratch','splash','fire','explosion','annihilate','ice']):
        return self.get_stat('attack') * ATTACK_DATA[attack]['amount']

    def update_xp(self, amount: float):
        if self.level_up - self.xp > amount:
            self.xp += amount
        else:
            self.xp = amount - (self.level_up - self.xp)
            self.level += 1
            self.level_up = self.level * 150

    def stat_limiter(self):
        self.health = max(0, min(self.health, self.get_stat('max_health')))
        self.energy = max(0, min(self.energy, self.get_stat('max_energy')))

    def update(self, dt: float):
        self.stat_limiter()
        if not self.paused:
            self.initiative += self.get_stat('speed') * dt
            self.energy += self.get_stat('recovery') * 0.009 * dt
            self.stat_limiter()