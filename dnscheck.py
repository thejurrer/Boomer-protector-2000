#!/usr/bin/env python3
import os
import sys
import json
import random
import string
import socket
import subprocess
import platform
from typing import List, Tuple, Set

def make_random_name(domain="example.com"):
    s = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    return f"{s}.{domain}"

def build_query(qname: str) -> bytes:
    tid = random.getrandbits(16)
    header = tid.to_bytes(2, 'big') + b'\x01\x00' + b'\x00\x01' + b'\x00\x00' + b'\x00\x00' + b'\x00\x00'
    parts = qname.split('.')
    qname_bytes = b''.join(len(p).to_bytes(1, 'big') + p.encode() for p in parts) + b'\x00'
    qtype_qclass = (1).to_bytes(2, 'big') + (1).to_bytes(2, 'big')
    return header + qname_bytes + qtype_qclass

def udp_query_and_responder(resolver: str, qname: str, port=53, timeout=2.0) -> Tuple[str, bytes]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(build_query(qname), (resolver, port))
        data, addr = sock.recvfrom(4096)
        return addr[0], data
    finally:
        sock.close()

def get_system_resolvers() -> List[str]:
    system = platform.system().lower()
    resolvers = []
    try:
        if system == "windows":
            out = subprocess.check_output(["netsh", "interface", "ip", "show", "dns"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                line = line.strip()
                parts = line.split()
                for part in parts:
                    if part.count('.') == 3:
                        resolvers.append(part)
        else:
            if os.path.exists("/etc/resolv.conf"):
                with open("/etc/resolv.conf", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("nameserver"):
                            parts = line.split()
                            if len(parts) >= 2:
                                resolvers.append(parts[1])
    except Exception:
        pass
    if not resolvers:
        resolvers = ["127.0.0.1"]
    seen = []
    for r in resolvers:
        if r not in seen:
            seen.append(r)
    return seen

def classify(responder_ips: Set[str], queried_resolvers: Set[str], gateway_ips: Set[str]) -> str:
    if not responder_ips:
        return "ERROR"
    if responder_ips.issubset(queried_resolvers):
        return "NO LEAK"
    if responder_ips & gateway_ips and responder_ips & queried_resolvers:
        return "POSSIBLE LEAK"
    return "LEAK"

def get_default_gateway_ips() -> Set[str]:
    system = platform.system().lower()
    gw = set()
    try:
        if system == "windows":
            out = subprocess.check_output(["ipconfig"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                line = line.strip()
                if line.lower().startswith("default gateway"):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        ip = parts[1].strip()
                        if ip:
                            gw.add(ip)
        else:
            try:
                out = subprocess.check_output(["ip", "route"], text=True, stderr=subprocess.DEVNULL)
                for line in out.splitlines():
                    if line.startswith("default via"):
                        parts = line.split()
                        if len(parts) >= 3:
                            gw.add(parts[2])
            except Exception:
                try:
                    out = subprocess.check_output(["netstat", "-rn"], text=True, stderr=subprocess.DEVNULL)
                    for line in out.splitlines():
                        parts = line.split()
                        if parts and parts[0] == "0.0.0.0" and len(parts) >= 2:
                            gw.add(parts[1])
                except Exception:
                    pass
    except Exception:
        pass
    return gw

def load_existing_json(path="data.json"):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def write_json_atomic(data, path="data.json"):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

def main():
    result_status = "ERROR"
    try:
        sys_resolvers = get_system_resolvers()
        public_resolvers = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
        queried = set(sys_resolvers + public_resolvers)
        qname = make_random_name("example.com")
        responder_ips = set()
        any_success = False
        for r in queried:
            try:
                responder, _ = udp_query_and_responder(r, qname)
                responder_ips.add(responder)
                any_success = True
            except Exception:
                pass
        if not any_success:
            result_status = "ERROR"
        else:
            gateway_ips = get_default_gateway_ips()
            result_status = classify(responder_ips, queried, gateway_ips)
    except Exception:
        result_status = "ERROR"

    # Load existing JSON, set DNS_leak key, write back
    data = load_existing_json("data.json")
    data["DNS_leak"] = result_status
    try:
        write_json_atomic(data, "data.json")
    except Exception:
        print(json.dumps({"DNS_leak": result_status}))

if __name__ == "__main__":
    main()
