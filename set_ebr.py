import fire
import socket

def SetEbr(ip:str="127.0.0.1", port:int=4000, ebr:float=1e-5):
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(str(ebr).encode(), (ip, port))

fire.Fire(SetEbr)
