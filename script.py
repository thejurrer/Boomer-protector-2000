import subprocess
import requests
import dnscheck
import time
import json
import mirror_lcd
#import speedtest #https://www.geeksforgeeks.org/python/test-internet-speed-using-python/

def wpa_scan():
    ssid = "WPA3"
    pw = "usggast123"
    https_request()


def https_request():
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    resp = requests.get("https://example.com")
    code = resp.status_code
    
    if 200 <= code < 300:
        status = "success"
    elif 400 <= code < 500:
        status = "client_error"
    elif 500 <= code < 600:
        status = "server_error"
    else:
        status = "other"
    data["HTTPS_code"] = {"code": code, "class": status}
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    dns_leaks()

def dns_leaks():
    dnscheck.main()
    result()

#def speed_check():
#    st = speedtest.Speedtest()
#    servernames =[]  
#
 #   st.get_servers(servernames)
#
 #   ping = st.results.ping
#     if ping <= 100:
#         outcome = "GOOD"
#     else:
#         outcome = "BAD"
  #  with open("data.json", "r", encoding="utf-8") as f:
    #    data = json.load(f)
   # data["speedtest"] = {"ping": ping, "outcome": outcome}
   # with open("data.json", "w", encoding="utf-8") as f:
    #    json.dump(data, f, indent=2)

    

def result():
    result = 0 #0-1 = green so good 2-3 = orange and 4-6 = red

    with open("data.json") as f:
        data = json.load(f)
    key = "DNS_leak"
    if data[key] == "LEAK":
        result += 2
    elif data[key] == "NO LEAK":
        print()
    elif data[key] == "ERROR":
        print("ERROR: dns_leak")
    elif data[key] == "POSSIBLE LEAK":
        result += 1
    else:
        print("crash!")

    key = "HTTPS_code"
    if data[key]["class"] == "success":
        print()
    else:
        print("ERROR: https_code")
        result += 2
    
    #key = "speedtest"
    #if data[key]["outcome"] == "GOOD":
    #    print()
    #else:
    #    result += 1

    key = "password"
    if data[key] == "":
        result += 2
    else:
        print()
    
    key = "SSID"
    if data[key] == "wpa" or "":
        result += 2
    else:
        print()
        
    print(result)
    
    with open('data.json', 'r') as f:
        obj = json.load(f)
        
    if result in (0, 1, 2, 3):
        obj["result"] = "green"
        obj["advice"] = "Dit wifi-netwerk is veilig!"
    elif result in (4, 5, 6):
        obj["result"] = "orange"
        obj["advice"] = "Pas op, dit wifi-netwerk is niet helemaal veilig!"
    else:
        obj["result"] = "red"
        obj["advice"] = "Ga onmiddellijk van dit wifi-netwerk af!"
        
    with open('data.json', 'w') as f:
        json.dump(obj, f, indent=2)
    
    mirror_lcd.main()
        


def main():
    wpa_scan()

if __name__ == "__main__":
    main()