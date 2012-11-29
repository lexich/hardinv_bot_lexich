#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'lexich'

#Константы

#Рейтинг показывает удовлетворительную
#скорость прироста дройдов, которая вычисляется speedGrowRating
SPEED_GROW_RATING = 0.3

#Стратегии
AGGRESSIVE      = "aggressive"
RUSH            = "rush"
QUICKEXPLORE    = "quickexplore",
SUPPORT         = "support",
EXPLORER        = "explorer",
PATIENT         = "patient",
REDISTRIBUTION  = "redistribution",
RUNAWAY         = "runaway"

# [0..1] - используется в стратегии QUICKEXPLORE, RUSH, EXPLORER
# Устанавливает лимит сопротивления, на которой атака может быть меньше
# опасности
QUICKEXPLORE_ATTACK_RESIST  = 0.6
RUSH_ATTACK_RESIST          = 0.7
EXPLORER_ATTACK_RESIST      = 0.7
PATIENT_ATTACK_RESIST       = 0.9

#Список быстрых стратегий
QUICK_STATEGY = (EXPLORER, RUSH, AGGRESSIVE, QUICKEXPLORE)

# [0..1] - используется в стратегии RUSH
# Показывает колличество дройдов, которых можно отправить в атаку,
# от общего числа
RUSH_ATTACK_DROIDS = 0.7

# [0..1] - используется в стратегии RUSH
# определяет максимальную заполненость планеты
RUSH_PLANET_FULL_MAX = 0.3

# >= 0 Используется в стратегии EXPLORER
# определяет колличество дройдов используемое для атаки
EXPLORER_ATTACK = 10

# Используется в стратегии EXPLORER
# Минимальный рейтин планеты который необходим для начала применения стратегии
EXPLORER_GROW_RATING = 7

REDISTRIBUTION_MULTIPLICATOR = 2
REDISTRIBUTION_MAX_MULTIPLICATOR = 2
# Устанавливает рейтинг для запертой планеты, для которой
# не нужно перераспределение
REDISTRIBUTION_SINGLE_GROW_FILTER = 2

ACTION_FIXPOSITION_RATING_FILTER = 0.5

# Рейтинг для атаки используется в Game.attack
# показывает какой должен быть рейтиг планеты, чтобы она 
# могла атаковать
GAME_RATING_ATTACK = 3
