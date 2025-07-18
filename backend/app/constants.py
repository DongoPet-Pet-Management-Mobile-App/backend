from enum import Enum, unique

@unique
class Language(int, Enum):
    sp = 1
    pt = 2
    fr = 3
    en = 4
    ge = 5
    ma = 6
    jp = 7
    ita = 8
    ko = 9

@unique
class Teacher(int, Enum):
    mary = 1
    james = 2
    machael = 3
    emily = 4

@unique
class Time(int, Enum):
    five_min = 1
    ten_min = 2
    twenty_min = 3
    thirty_min = 4

@unique
class LessonStatus(int, Enum):
    disable = 0
    active = 1
    in_progress = 2
    completed = 3

