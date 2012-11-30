#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
from datetime import datetime
import traceback
import sys
from dom import DomEl
from request import Request
from signals import GameOver, Win, InterruptGame

from planet import Planet
from xml.dom.minidom import parseString
import os

with open("log.txt","w") as f:
  f.write("")

def logDebug(txt):
  try:
    with open("debug.txt","a") as f:
      f.write(txt)
      f.write("\n")
    print txt
  except Exception,e:
    print("Logger error:%s" % e)

class Logger(object):
  ROOT_DIR = "log"
  def __init__(self,host="default"):
    self._start = False
    self.host = host
    self.log_file_dir = os.path.join(
      self.ROOT_DIR,
      self.host,
      datetime.now().strftime("%Y-%m-%d{0}%H-%M-%S".format(os.path.sep))
    )
    self.history = {}

  def start(self):
    self._start = True

  def write(self, data, type, count=0):
    if not self._start: return
    if not self.history.has_key(type):
      self.history[type] = []
    self.history[type].append(data)

  def flush(self):
    from xml.dom.minidom import parseString
    folders = self.log_file_dir.split(os.path.sep)
    path = ""
    for folder in folders:
      path = os.path.join(path,folder)
      if not os.path.exists(path):
        os.mkdir(path)

    for type, type_history in self.history.iteritems():
      count = 0
      for data in type_history:
        filename = os.path.join(self.log_file_dir, "{1}_{0}.xml".format(type, count))
        try:
          xml = parseString(data)
          data = xml.toprettyxml()
        except Exception,e:
          print "Logger,exeption %s" % e.message
        with open(filename, "w") as f:
          f.write(u"%s" % data)
        count+=1


class ClientBase(object):
  BUFFER_SIZE = 1024*8

  def __init__(self, host, port):
    self.host = host
    self.port = port
    self.s = self.connect()
    self.log = Logger(host=host)
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
    return None

  def send(self, request):
    return self._send(request.to_xml)

  def handle(self, planets, request):
    raise NotImplemented('Need to implement')


class Client(ClientBase):
  testMode = False

  def __init__(self, host, port, token, user):
    super(Client, self).__init__(host, port)
    self.token = token
    self.user = user
    self.start_game = None

  def action(self, request):
    root = None
    while not root:      
      try:
        self.connect()
        self.send(request)
        root = self.recv()
        self.close()
        if not root:
          continue
      except socket.error, e:
          traceback.print_exc(file=sys.stderr)
          logDebug(e.message)
      except Exception, e:
        traceback.print_exc(file=sys.stderr)
        logDebug(e.message)
    return root.response

  def _start_game(self,txt=""):
    if self.start_game is None:
      logDebug(txt)
    self.start_game = True

  def _end_game(self,txt=""):
    logDebug(txt)
    if not self.testMode:
      self.log.flush()
    self.start_game = False

  def start(self):
    response = None
    request = Request(self.token)    
    while self.start_game is not False:
      try:
        request = self.run(request)    
      except Exception, e:
        traceback.print_exc(file=sys.stderr)
        logDebug(e.message)

  def run(self,request):            
    response = self.action(request)       
    errors = response.errors
    if len(errors) > 0:
      for error in errors:
        logDebug("error:%s" % error)
    
    if len(response.planets) > 0:
      self._start_game("Game begin")
      if not self.testMode:
        self.log.start()
      self.step += 1
      planets = {}

      for planet in response.planets:
        p = Planet(planet, planets, self.user)
        planets[p.id] = p

      request = Request(self.token,planets)      
      start = datetime.now()
      try:
        self.handle(planets, request)
      except Win, e:
        self._end_game("You win")        
      except GameOver, e:
        self._end_game("Game over")
      except InterruptGame,e:
        self._end_game("Interrupt game") 

      delta = datetime.now() - start
      logDebug("step:%s speed:%s" % (self.step,delta.total_seconds()))
    return request
