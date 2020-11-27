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
freshDuration = 0.1


class DrawEmitter(flx.Component):
    def init(self):
        self.refresh()
    
    @flx.emitter
    def redraw(self):
        return dict()

    def refresh(self):
        self.redraw()
        asyncio.get_event_loop().call_later(freshDuration, self.refresh)
        
emitter = DrawEmitter()


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
        self.ui.handleMsg(data)
    
    def error_erceived(self, exc):
        print("received error: {}".format(exc))

def howManyOne(data):
    result = 0
    while data != 0:
        result += 1
        data = data^(~(data-1))
    return result

class Receiver(flx.PyWidget):
    def init(self):
        self.running = False
        self.bitState = {"total":0, "error": 0}
        self.frameState = {"total":0, "error": 0}
        with flx.HBox():
            flx.Widget(flex=1)
            with flx.VBox():
                flx.Widget(flex=1)
                with flx.HBox():
                    flx.Label(text="IP地址")
                    self.ip = flx.LineEdit(placeholder_text="0.0.0.0", flex=1)
                with flx.HBox():
                    flx.Label(text="绑定端口")
                    self.port = flx.LineEdit(placeholder_text="0", flex=1)
                self.bind = flx.Button(text="绑定")
                self.status = flx.Label(text="测试尚未开始")
                with flx.HBox():
                    with flx.VBox():
                        with flx.HBox():
                            flx.Label(text="总比特数: ")
                            self.total_bits = flx.Label(text="0")
                            flx.Widget(flex=1)
                        with flx.HBox():
                            flx.Label(text="误比特数: ")
                            self.error_bits = flx.Label(text="0")
                            flx.Widget(flex=1)
                        with flx.HBox():
                            flx.Label(text="误码率: ")
                            self.error_bits_rate = flx.Label(text="0")
                            flx.Widget(flex=1)
                    with flx.VBox():
                        with flx.HBox():
                            flx.Label(text="总帧数: ")
                            self.total_frame = flx.Label(text="0")
                            flx.Widget(flex=1)
                        with flx.HBox():
                            flx.Label(text="误帧数: ")
                            self.error_frame = flx.Label(text="0")
                            flx.Widget(flex=1)
                        with flx.HBox():
                            flx.Label(text="误帧率: ")
                            self.error_frame_rate = flx.Label(text="0")
                            flx.Widget(flex=1)
                flx.Widget(flex=1)
            flx.Widget(flex=1)

    @flx.reaction('bind.pointer_down')
    def bind_address(self, *events):
        if self.bind.text != "已绑定":
            loop = asyncio.get_event_loop()
            coro = loop.create_datagram_endpoint(lambda: UDPReceiver(self), local_addr=(self.ip.text, int(self.port.text)))
            asyncio.ensure_future(coro, loop=loop)
            self.bind.set_text("已绑定")
    
    def handleMsg(self, data):
        headZero = 0
        for b in data[:100]:
            if b == 0:
                headZero += 1
        tailOne = 0
        for b in data[-100:]:
            if b == 0xff:
                tailOne += 1
        if headZero < 10:
            self.handleData(data)
        elif tailOne > 80:
            self.handleStop(data)
        else:
            self.handleStart(data)
        
    def handleData(self, data):
        if not self.running:
            return
        errBits = 0
        for byte in data:
            mask = byte ^ 0xff
            errBits += howManyOne(mask)
        self.bitState["total"] += len(data) * 8
        self.bitState["error"] += errBits
        self.frameState['total'] += 1
        if errBits > 0:
            self.frameState["error"] += 1

    def handleStart(self, data):
        self.bitState = {"total":0, "error": 0}
        self.frameState = {"total":0, "error": 0}
        self.status.set_text("测试中")
        self.running = True
    
    def handleStop(self, data):
        self.running = False
        self.status.set_text("测试结束")
    
    @emitter.reaction("redraw")
    def redraw(self, *events):
        self.total_bits.set_text(str(self.bitState["total"]))
        self.error_bits.set_text(str(self.bitState["error"]))
        if self.bitState["error"] == 0:
            self.error_bits_rate.set_text("0")
        else:
            self.error_bits_rate.set_text(str(self.bitState["error"]/self.bitState["total"]))
        self.total_frame.set_text(str(self.frameState["total"]))
        self.error_frame.set_text(str(self.frameState["error"]))
        if self.frameState["error"] == 0:
            self.error_frame_rate.set_text("0")
        else:
            self.error_frame_rate.set_text(str(self.frameState["error"]/self.frameState["total"]))

if __name__ == '__main__':
    flx.App(Receiver, title="误码率测试接收端").launch("app")
    flx.run()