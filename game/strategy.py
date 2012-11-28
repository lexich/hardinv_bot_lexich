# -*- coding: utf-8 -*-
import math
from constants import *
__author__ = 'lexich'


class MixinStrategies(object):
  #Приоритетность использования стратегий
  STRATEGIES_PRIORITY = (
    AGGRESSIVE,
    RUSH,
    QUICKEXPLORE,
    SUPPORT,
    EXPLORER,
    PATIENT,
    REDISTRIBUTION,
    RUNAWAY
  )

  def strategy_quickexplore(self, plan, request, _from, _to):
    """
    Стратегия быстрого исследования территории
    Используется когда нужно быстро занять более
    выигрышную позицию на карте
    """
    if _to.is_enemy:
      return
    if _from.limit > _to.limit:
      return
    if _from.droids > _to.danger * QUICKEXPLORE_ATTACK_RESIST:
      request.add(
        _from.id,
        _to.id,
        _from.sendDroids(
          _from.droids, limit=0
        ),
        QUICKEXPLORE)


  def strategy_aggressive(self, plan, request, _from, _to):
    """
    Стратегия агрессивного нападения, используется,
    когда нужно добить соперника
    """

    needToAttack = _to.grow + 1
    #Если достаточно дройдов для захвата
    if _from.droids >= needToAttack:
      #Если опасность не угрожает
      #Патчим метод _from.get_danger()
      #Уменьшаем уровень опасности атакуемой планеты на величину атаки
      rating = _from.get_danger_rating()
      rating[_to.owner] -= needToAttack
      _from_danger = max(rating.values()) if len(rating.values()) > 0 else 0
      #Если уровень опасности достаточен для атаки
      if _from_danger < _from.droids - needToAttack:
        if _from.limit < _to.limit:
          request.add(_from.id, _to.id, _from.sendDroids(_from.droids), AGGRESSIVE)
        else:
          request.add(_from.id, _to.id, _from.sendDroids(needToAttack + 9, limit=1), AGGRESSIVE)
          return

      #Если опасность угрожает но есть подмога
      friends = filter(lambda x: x.is_myself, _from.neighbours)
      maxHelp = sum(map(lambda x: x.attack, friends))

      #Если помощь подмоги достаточна
      if _from.danger < (_from.droids - needToAttack) + maxHelp:
        #Определяем коэффициент равномерности поддержки
        kSupport = (_from.droids - needToAttack) / maxHelp
        if kSupport < 0:
          return
          #Отправляем на атаку
        request.add(_from.id, _to.id, _from.sendDroids(needToAttack, limit=1), AGGRESSIVE)
        #Равномерно оказываем поддержку
        for friend in friends:
          droids = int(math.ceil(friend.attack * kSupport))
          request.add(friend.id, _from.id, friend.sendDroids(droids), AGGRESSIVE)
        return
    #Если агрессивное нападение не удалось пробрасваем его до умеренного
    super(MixinStrategies, self).trySendDroids(plan, _from, _to, PATIENT)

  def strategy_rush(self, plan, request, _from, _to):
    """
    Реализация быстрого нападения
    """

    #Атака дройдов
    attackDroids = _from.droids * RUSH_ATTACK_DROIDS
    #Если сосед не враг
    if not _to.is_enemy:
      #Проверяем окружение планеты приемника на злобность
      if attackDroids > _to.get_danger() * RUSH_ATTACK_RESIST:
        request.add(_from.id, _to.id, _from.sendDroids(attackDroids), RUSH)
    #Если сосед - враг
    else:
      #Заполненность планеты
      k = _from.growRating(_from.droids) / _from.growRating(10)
      #если заполненность меньше RUSH_PLANET_FULL_MIN, отказываемся
      if k > RUSH_PLANET_FULL_MAX:
        return
      maxResist = _to.danger

      #Если атака больше преодолевает сопротивление
      if attackDroids > maxResist * RUSH_ATTACK_RESIST:
        #Если атакуемая планета имеет более высокий тип
        if _to.limit > _from.limit:
          request.add(_from.id, _to.id, _from.sendDroids(_from.droids), RUSH)
        else:
          request.add(_from.id, _to.id, _from.sendDroids(attackDroids), RUSH)

  def strategy_support(self, plan, request, _from, _to):
    """
    Стратегия помощи планетам ускорить рост популяции,
    целесообразно для планет доноров
    """
    #Если планета приемник в безопасности
    if not _to.danger:
      maxSendDroids = _from.attack
      #если допустимое для атаки кол-во дройдов ненулевое
      if maxSendDroids > 10 - _to.droids:
        needToSend = SPEED_GROW_RATING * _to.limit - _to.droids
        sendToDroids = maxSendDroids if needToSend > maxSendDroids else needToSend
        request.add(_from.id, _to.id, _from.sendDroids(sendToDroids), SUPPORT)
        #если у планеты приемника меньше 10 юнитов то отправим недостающее кол-во
      if _to.droids < 10 and not _to.maxMyselfNeighboursAttack():
        neighboursMyselfCount = len(filter(
          lambda x: x.droids > 10,
          _to.neighboursMyself()
        ))
        sendDroids = math.ceil(
          (10.0 - _to.droids) / neighboursMyselfCount
        ) if neighboursMyselfCount > 0 else 10
        request.add(_from.id, _to.id, _from.sendDroids(sendDroids), SUPPORT)

  def strategy_explorer(self, plan, request, _from, _to):
    #Если текущая планета менее привлектельна нежели соседняя
    #И одновременная атака нас не уничтожит
    #Переселяем всю планету кроме сухого остатка
    if _from.limit < _to.limit and\
       (_from.droids - EXPLORER_ATTACK) > _to.danger * EXPLORER_ATTACK_RESIST:
      request.add(_from.id, _to.id, _from.sendDroids(_from.droids), EXPLORER)
    #Если допустима атака выше атаки исследования и ретинг роста позволяет
    #Начинаем исследование планет
    elif _from.attack > EXPLORER_ATTACK and\
         _from.growRating(_from.droids) < EXPLORER_GROW_RATING:
      #Если исследование территории  опасно
      #И уровень опасности больше атаки планеты источника
      #То отправляем дройда на разведку
      if _to.danger > _from.attack:
        request.add(_from.id, _to.id, _from.sendDroids(1), EXPLORER)
      #Иначе проводим настоящую атаку
      else:
        #TODO:нехарактерное поведение стратегии
        request.add(_from.id, _to.id, _from.sendDroids(_to.danger + EXPLORER_ATTACK), EXPLORER)

  def strategy_patient(self, plan, request, _from, _to):
    """
    Стратегия умеренного нападения, используется когда нельзя
    захватить планету нахрапом
    """
    to_plan = plan["to"].get(_to, [])
    maxAttack = sum(map(
      lambda item: item[0].attack, to_plan
    )) if len(to_plan) > 0 else 0
    #Если максимаотная атака меньше PATIENT_ATTACK_RESIST то отказываемся но
    if maxAttack < _to.danger * PATIENT_ATTACK_RESIST:
      #Но если планета заполнена атакуем в любом случае
      if _from.growRating(_from.droids) < 3:
        request.add(_from.id, _to.id, _from.sendDroids(_from.attack), PATIENT)

    else:
      for from_item in to_plan:
        src = from_item[0]
        request.add(src.id, _to.id, src.sendDroids(src.attack), PATIENT)

  def strategy_redistribution(self, plan, request, _from, _to):
    """
    Стратегия перераспределения дройдов
    Используется когда планеты в безопасности и нужно
    отправить дройдов к нуждающимся планетам
    """
    len_to_neighbours = len(_to.get_neighbours())
    to_growRating_full = _to.growRating(_to.droids)
    from_growRating_full = _from.growRating(_from.droids)

    #Если рейтинг роста планеты источника больше 1(хода) то не учасвуем
    if from_growRating_full > 1:
      return
      #Вычисляем колличество дройдов для перераспределения c учетом тех дройдов которые могли сюда попасть по
    #перераспределению
    droidsRedistribution = _from.droids - int(_from.limit / ((1 + _from.percent)) ** REDISTRIBUTION_MULTIPLICATOR) + _from.receive_droids

    if droidsRedistribution < 0:
      print "ERROR: executePlanRedistribution: Error droidsRedistribution %s" % droidsRedistribution
      return

    if _to.is_enemy:
      return

    #Если у планеты приемника 1 сосед(источник) и заполнена, то пропускаем
    if len_to_neighbours == 1 and to_growRating_full < REDISTRIBUTION_SINGLE_GROW_FILTER:
      return

    #Если рейтинг планет учавствующих в обмене меньше 1(хода)
    if to_growRating_full <= 1 and from_growRating_full <= 1:
      #Если дройдов на приемнике больше чем в источнике, пропускаем
      #if _to.droids > _from.droids:
      #  return
      #Если опасность источника больше опасности приемника
      if 0 < _to.danger < _from.danger:
        return

      #Вычисляем чьим соседям может понадобится помощь
      fromDanger = _from.fullNeighboursDanger()
      toDanger = _to.fullNeighboursDanger(fromDanger)

      #Если опасность соселей приемника больше чем опасность соседей источника
      #То исходя из того что враг далеко, увеличиваем размер атаки на кол-во регенерации за 2 хода
      if fromDanger < toDanger:
        print "DOUBLE REDISTRIBUTION"
        droidsRedistribution2 = _from.droids - int(_from.limit / ((1 + _from.percent) ** REDISTRIBUTION_MAX_MULTIPLICATOR)) + _from.receive_droids
        request.add(_from.id, _to.id, _from.sendDroids(droidsRedistribution2), REDISTRIBUTION)
        return

    #Если все фильтры пройдены, то перераспределяем
    request.add(_from.id, _to.id, _from.sendDroids(droidsRedistribution), REDISTRIBUTION)

  def strategy_runaway(self, plan, request, _from, _to):
    """
    Стратегия убегания с поля боя
    Когда планета обречена на атаку, которая ее добьет,
    убегаем, сохраняя дройдов
    """
    if _to.is_enemy:
      return
    if _to.danger > _from.droids:
      return
    request.add(_from.id, _to.id, _from.sendDroids(_from.droids, limit=0), RUNAWAY)

  def is_strategy_check(self, plan, request, _from, _to, _strategy):
    """
    Проверка параметров перед вызывом стратегий
    """
    if not _from.is_myself:
      print "ERROR: is_strategy_check _from is not myself"
      return False

    if _strategy == RUNAWAY:
      return True

    if _from.id in _to.receive_from:
      return False

    # Если для источника была использована быстрая стратегия, а его используют
    # для исследования иои быстрых стратегий,
    # то отказываемся, тк быстрая стратегия уже подразумевает захват новой территории
    if _strategy in QUICK_STATEGY and _from.is_fast_strategy():
      return False

    #Если планета источник мертва
    if _from.is_dead():
      #Находим живых не чужих соседей
      arr = filter(
        lambda n: not n.is_dead() and not n.is_enemy,
        _from.neighbours
      )
      for target in arr:
        super(MixinStrategies, self).trySendDroids(plan, _from, target, RUNAWAY)
      return False
    #если наша и планета приемник мертвы
    if _to.is_myself and _to.is_dead():
      #Находим живых не чужих соседей
      arr = filter(
        lambda n: not n.is_dead() and not n.is_enemy,
        _to.neighbours
      )
      for target in arr:
        super(MixinStrategies, self).trySendDroids(plan, _to, target, RUNAWAY)
      return False

    if _from.is_dead() or _to.is_dead():
      return False
    return True