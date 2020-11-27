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
username = "北京大学"

resendText = [
    "你好",
    "今天天气不错",
    "欢迎专家前来检查"
]

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

class MessageBox(flx.Label):

    CSS = """
    .flx-MessageBox {
        overflow-y:scroll;
        background: #e8e8e8;
        border: 1px solid #444;
        margin: 3px;
    }
    """

    def init(self):
        super().init()
        global window
        self._se = window.document.createElement('div')

    def sanitize(self, text):
        self._se.textContent = text
        text = self._se.innerHTML
        self._se.textContent = ''
        return text

    @flx.action
    def add_message(self, msg):
        line = self.sanitize(msg)
        self.set_html(self.html + line + '<br />')

class SenderRoom(flx.PyWidget):
    """ This represents one connection to the chat room.
    """

    def init(self):
        with flx.HBox():
            flx.Widget(flex=1)
            with flx.VBox():
                with flx.HBox():
                    flx.Label(text="用户名: {}".format(username), flex=1)
                with flx.HBox():
                    flx.Label(text="IP地址", flex=1)
                    self.ip = flx.LineEdit(placeholder_text="0.0.0.0", flex=2)
                with flx.HBox():
                    flx.Label(text="目的端口", flex=1)
                    self.port = flx.LineEdit(placeholder_text="0", flex=2)
                flx.Widget(flex=1)
            with flx.VBox(minsize=300):
                self.messages = MessageBox(flex=1)
                with flx.HBox():
                    self.msg_edit = flx.LineEdit(flex=1, placeholder_text='请输入内容(不超过30个汉字)')
                    self.ok = flx.Button(text='发送')
                    self.autosend = flx.Button(text='自动发送已关闭')
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
    flx.App(SenderRoom, title="短消息测试发送端").launch("app")
    flx.run()