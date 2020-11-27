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

hostname = "127.0.0.1"
leftuser = "南海渔船"
rightuser = "北京大学"

class UDPReceiver:
    def __init__(self, ui):
        self.ui = ui
        self.transport = None

    def connection_made(self, transport):
        print("connection made")
        self.transport = transport
    
    def connection_lost(self, exc):
        print("socket closed {}".format(exc))

    def datagram_received(self, data, addr):
        addr = "{}:{}".format(addr[0], addr[1])
        rawMsg = data.decode()
        name, msg = rawMsg.split(":", 1)
        msg.rstrip()
        self.ui._show_message(name, msg)
    
    def error_erceived(self, exc):
        print("received error: {}".format(exc))


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

class ReceiverChannel(flx.PyWidget):
    def init(self):
        with flx.HBox():
            flx.Widget(flex=1)
            with flx.VBox(minsize=200):
                with flx.HBox():
                    flx.Label(text="IP地址")
                    self.ip = flx.LineEdit(placeholder_text="0.0.0.0", flex=1)
                with flx.HBox():
                    flx.Label(text="绑定端口")
                    self.port = flx.LineEdit(placeholder_text="0", flex=1)
                self.bind = flx.Button(text="绑定")
                flx.Widget(flex=1)
            with flx.VBox(minsize=350):
                flx.Label(text="{}消息展示".format(leftuser))
                self.left_messages = MessageBox(flex=1)
            with flx.VBox(minsize=350):
                flx.Label(text="{}消息展示".format(rightuser))
                self.right_messages = MessageBox(flex=1)
            flx.Widget(flex=1)

    @flx.reaction('bind.pointer_down')
    def bind_address(self, *events):
        loop = asyncio.get_event_loop()
        coro = loop.create_datagram_endpoint(lambda: UDPReceiver(self), local_addr=(self.ip.text, int(self.port.text)))
        asyncio.ensure_future(coro, loop=loop)

    def _show_message(self, name, data):
        box = None
        if name == leftuser:
            box = self.left_messages
        else:
            box = self.right_messages
        box.add_message("{} {}".format(datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S"), name))
        box.add_message(data)


if __name__ == '__main__':
    flx.App(ReceiverChannel, title="短消息测试接收端").launch("app")
    flx.run()