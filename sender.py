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
hostname = "127.0.0.1"
duration = 1
username = "南海渔船"

class SendEmitter(flx.Component):

    def init(self):
        self.refresh()
    
    @flx.emitter
    def check_auto(self):
        return dict()

    def refresh(self):
        self.check_auto()
        asyncio.get_event_loop().call_later(duration, self.refresh)
        
emitter = SendEmitter()

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
                    self.frameSize = flx.LineEdit(placeholder_text="20000", flex=2)
                with flx.HBox():
                    flx.Label(text="测试模式", flex=1)
                    self.mode = flx.LineEdit(placeholder_text="测试模式", flex=2)
                with flx.HBox():
                    self.button = flx.Button(text="开始")
                flx.Widget(flex=1)
            flx.Widget(flex=1)
        self.resendIndex = 0

    @flx.reaction('ok.pointer_down', 'msg_edit.submit')
    def _send_message(self, *events):
        text = self.msg_edit.text
        if text:
            result = self.send_message(text, username, self.ip.text, self.port.text)
            if result == "ok":
                self.msg_edit.set_text('')
                self.messages.add_message("{} {}:{}".format(datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S"), self.ip.text, self.port.text))
                self.messages.add_message(text)
            else:
                self.messages.add_message("{} {}:{}".format(datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S"), self.ip.text, self.port.text))
                self.messages.add_message(result)
    
    def _try_send_message(self):
        if self.resendIndex >= len(resendText):
            self.resendIndex = 0
        text = resendText[self.resendIndex]
        if len(text) > 0:
            self.send_message(text, username, self.ip.text, self.port.text)
            self.messages.add_message("{} {}:{}".format(datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S"), self.ip.text, self.port.text))
            self.messages.add_message(text)
        self.resendIndex += 1
    
    @flx.reaction("autosend.pointer_down")
    def _change_auto_mode(self, *events):
        if self.autosend.text == "自动发送已关闭":
            self.autosend.set_text("自动发送已打开")
        else:
            self.autosend.set_text("自动发送已关闭")
    
    def send_message(self, msg, name, ip, port):
        msg = "{}:{}".format(name, msg)
        if len(msg) > packetLength:
            msg = msg[:packetLength]
        else:
            msg = msg + ' '*(packetLength-len(msg))
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(msg.encode(), (ip, int(port)))
        print("result: socket done")
        return "ok" 
    
    @emitter.reaction("check_auto")
    def _auto_send(self, *events):
        if self.autosend.text == "自动发送已打开":
            self._try_send_message()
    

if __name__ == '__main__':
    # flx.App(SenderRoom, title="短消息测试发送端").launch("app")
    # flx.run()
    flx.config.hostname = "162.105.85.184"
    flx.App(SenderRoom).server()
    flx.start()