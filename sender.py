"""
Simple chat web app inabout 80 lines.

This app might be running at the demo server: http://flexx1.zoof.io
"""

from flexx import flx
import datetime
import time
import threading
import asyncio
import socket

packetLength = 491
packetPrefix = 100
hostname = "127.0.0.1"
duration = 1
username = "南海渔船"

class SendEmitter(flx.Component):

    def init(self):
        self.refresh()
    
    @flx.emitter
    def send_packet(self):
        return dict()

    def refresh(self):
        self.send_packet()
        asyncio.get_event_loop().call_later(duration, self.refresh)
        
emitter = SendEmitter()

headPacket = bytearray(packetLength)
for i in range(packetLength):
    if i < packetPrefix:
        headPacket[i] = 0
    else:
        headPacket[i] = 0x0f

dataPacket = bytearray(packetLength)
for i in range(packetLength):
    dataPacket[i] = 0xff

tailPacket = bytearray(packetLength)
for i in range(packetLength):
    if i < packetPrefix:
        tailPacket[i] = 0
    else:
        tailPacket[i] = 0xff


class Sender(flx.PyWidget):
    """ This represents one connection to the chat room.
    """

    def init(self):
        with flx.HBox():
            flx.Widget(flex=1)
            with flx.VBox():
                flx.Widget(flex=1)
                with flx.HBox():
                    flx.Widget(flex=1)
                    flx.Label(text="误码率测试发送端")
                    flx.Widget(flex=1)
                with flx.HBox():
                    self.bar = flx.Label(text="bar")
                with flx.HBox():
                    flx.Label(text="IP地址", flex=1)
                    self.ip = flx.LineEdit(placeholder_text="0.0.0.0", flex=2)
                with flx.HBox():
                    flx.Label(text="目的端口", flex=1)
                    self.port = flx.LineEdit(placeholder_text="0", flex=2)
                with flx.HBox():
                    flx.Label(text="测试帧数", flex=1)
                    self.frameNum = flx.LineEdit(placeholder_text="20000", flex=2)
                with flx.HBox():
                    flx.Label(text="测试模式", flex=1)
                    self.mode = flx.LineEdit(placeholder_text="测试模式", flex=2)
                with flx.HBox():
                    self.startButton = flx.Button(text="开始")
                flx.Widget(flex=1)
            flx.Widget(flex=1)
        self.headCount = 0
        self.tailCount = 0
        self.dataCount = 0
        self.socket = None 

    @flx.reaction('startButton.pointer_down')
    def change_state(self, *events):
        if self.startButton.text == "停止中...":
            return
        if self.startButton.text == "开始":
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.startButton.set_text("提前结束")
        else:
            self.startButton.set_text("停止中...")
            def getReady():
                self.tailCount = 0
                self.headCount = 0
                self.dataCount = 0
                self.startButton.set_text("开始")
            asyncio.get_event_loop().call_later(3, getReady)
    
    @emitter.reaction("send_packet")
    def send_packet(self, *events):
        if self.startButton.text == "开始" or self.socket is None:
            pass
        elif self.startButton.text == "提前结束":
            if self.headCount < 3:
                self.send_head()
                self.headCount += 1
            else:
                self.dataCount += 1
                self.send_data()
                if self.dataCount >= int(self.frameNum.text):
                    self.change_state()
        else:
            if self.tailCount < 3:
                self.send_tail()
                self.tailCount += 1
    
    def send_head(self):
        # TODO add information in head
        self.socket.sendto(headPacket, (self.ip.text, int(self.port.text)))
    
    def send_data(self):
        self.socket.sendto(dataPacket, (self.ip.text, int(self.port.text)))
    
    def send_tail(self):
        self.socket.sendto(tailPacket, (self.ip.text, int(self.port.text)))
    
if __name__ == '__main__':
    flx.App(Sender, title="误码率测试发送端").launch("app")
    flx.run()
    # flx.config.hostname = "162.105.85.184"
    # flx.App(SenderRoom).server()
    # flx.start()