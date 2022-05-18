#!/usr/bin/env python3

import subprocess

# from netaddr import EUI, mac_unix_expanded

data = [{
    "node": "1134911-02",
    "mac": "3CECEFFBE12E"
}, {
    "node": "1134911-09",
    "mac": "3CECEFFBE136"
}, {
    "node": "1134911-01",
    "mac": "3CECEFFBE10E"
}, {
    "node": "1134911-05",
    "mac": "3CECEFFC378E"
}, {
    "node": "1134911-12",
    "mac": "3CECEFFC3534"
}, {
    "node": "1134911-13",
    "mac": "3CECEFFC375C"
}, {
    "node": "1134911-03",
    "mac": "3CECEFFBE12C"
}, {
    "node": "1134911-08",
    "mac": "3CECEFFC3538"
}, {
    "node": "1134911-14",
    "mac": "3CECEFFC3750"
}, {
    "node": "1134911-10",
    "mac": "3CECEFFC3768"
}, {
    "node": "1134911-07",
    "mac": "3CECEFFC3784"
}, {
    "node": "1134911-04",
    "mac": "3CECEFFC377E"
}, {
    "node": "1134911-06",
    "mac": "3CECEFFC3812"
}, {
    "node": "1134911-11",
    "mac": "3CECEFFC36CE"
}]

# ip_range = range(10, 25)

# for ip, n in list(zip(ip_range, data)):
#     mac = str(EUI(n['mac'], dialect=mac_unix_expanded)).lower()
#     txt = 'host %s {\n\thardware ethernet %s;\n\tfixed-address 172.17.34.%s;\n}' % (
#         n['node'], mac, ip)

#     print(txt)

for h in data:

    cmd = './pxu assign -m {} -n "Ubuntu 20.04 Small SSD"'.format(h.get("mac"))
    cmd = subprocess.run(cmd,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    print(cmd.returncode)
