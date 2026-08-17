import socket, time
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
target = ("69.46.46.125", 8080)
end = time.time() + 30
while time.time() < end:
    sock.sendto(b"test", target)
    time.sleep(0.01)   # 100 пакетов в секунду
