from abc import ABC
from typing import List, Dict, Optional
#import requests




class Dog:
    def __init__(self, kind, color, weight, mph):
        self.kind = kind
        self.color = color
        self.weight = weight
        self.mph = mph

    def attributes(self):
        print(f"This dog is a {self.kind}, of the color {self.color}, " 
              f"weighing at {self.weight} lbs and can run {self.mph} miles per hour!")

    def speed_boost(self, added_speed):
        self.mph += added_speed


myDog = Dog("Australian Shepard", "brown and white", "40", 20)

myDog.attributes()
myDog.speed_boost(100)
myDog.attributes()

myDog = Dog(...)





        