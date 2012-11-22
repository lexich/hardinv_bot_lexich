#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
from datetime import datetime
import traceback
import sys
from dom import DomEl
from signals import GameOver, Win, InterruptGame

from planet import Planet, Request
from xml.dom.minidom import parseString
import os

with open("log.txt","w") as f:
  f.write("")

def log_error(txt):
  try:
    with open("debug.txt","a") as f:
      f.write(txt)
    print txt
  except Exception,e:
    print("Logger error:%s" % e)

def log(txt):
  try:
    with open("log.txt","a") as f:
      f.write(txt)
  except Exception,e:
    print("Logger error:%s" % e)



class Logger(object):
  def __init__(self):
    self._start = False
    self.lof_dir = "log"
    self.log_file_dir = os.path.join(self.lof_dir, datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    self.history = {}

  def start(self):
    self._start = True

  def write(self, data, type, count=0):
    if not self._start: return
    if not self.history.has_key(type):
      self.history[type] = []
    self.history[type].append(data)

  def flush(self):
    if not os.path.exists(self.lof_dir):
      os.mkdir(self.lof_dir)
    os.mkdir(self.log_file_dir)

    for type, type_history in self.history.iteritems():
      count = 0
      for data in type_history:
        filename = os.path.join(self.log_file_dir, "{1}_{0}.xml".format(type, count))
        with open(filename, "w") as f:
          f.write(u"%s" % data)
        count+=1


class ClientBase(object):
  BUFFER_SIZE = 1024*8

  def __init__(self, host, port):
    self.host = host
    self.port = port
    self.s = self.connect()
    self.log = Logger()
    self.step = 0

  def connect(self):
    self.s = socket.socket(
      socket.AF_INET,
      socket.SOCK_STREAM
    )
    self.s.connect((self.host, self.port))
    return self.s

  def close(self):
    self.s.close()

  def _send(self, data):
    sendData = 0
    while sendData < len(data):
      sendData += self.s.send(data)
    self.log.write(data, "send", self.step)

  def _recv(self):
    data = ""
    while True:
      chunk = self.s.recv(self.BUFFER_SIZE)
      data += chunk
      if data == "":
        break
      if len(chunk) < self.BUFFER_SIZE and chunk == "":
        break
    self.log.write(data, "recv", self.step)
    return data

  def recv(self):
    data = self._recv()
    if data != "":
      return DomEl(parseString(data))
    else:
      return DomEl(parseString(""))

  def send(self, request):
    #log_error(unicode(request))
    return self._send(request.to_xml)

  def handle(self, planets, request):
    raise NotImplemented('Need to implement')


class Client(ClientBase):
  def __init__(self, host, port, token, user):
    super(Client, self).__init__(host, port)
    self.token = token
    self.user = user

  def auth(self):
    self.connect()
    self.send(Request(self.token))
    root = self.recv()
    self.close()
    return root.response

  def action(self, request):
    self.connect()
    self.send(request)
    root = self.recv()
    self.close()
    return root.response

  def _parceResponce(self, response):
    self.step += 1
    planets = {}
    for planet in response.planets:
      p = Planet(planet, planets, self.user)
      planets[p.id] = p
    request = Request(self.token)
    self.handle(planets, request)
    return  self.action(request)

  testMode = False
  def run(self):
    safeEndGame = 0
    safeEndGameMax = 3
    response = None
    while True:
      response = self.auth()
      errors = response.errors
      if len(errors) > 0:
        for error in errors:
          log_error("error:%s" % error)
      else:
        break

    log("Begin Game")
    if not self.testMode:
      self.log.start()
    while True:
      try:
        if len(response.errors) > 0:
          for error in response.errors:
            log_error("ERROR: %s" % error)
        response = self._parceResponce(response)
        log_error("step:%s" % self.step)
      except Win, e:
        log_error("You win")
        break
      except GameOver, e:
        if safeEndGame > safeEndGameMax:
          log_error("Game over")
          break
        safeEndGame += 1
      except InterruptGame,e:
        log_error("Interrupt game")
        break
      except socket.error, e:
        log_error(e.message)
      except Exception, e:
        traceback.print_exc(file=sys.stderr)
        log_error(e.message)
    if not self.testMode:
      self.log.flush()

