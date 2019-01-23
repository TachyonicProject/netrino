#!/usr/bin/env python3 

import fileinput
import re
import json
import requests

resp = requests.get('https://tools.ietf.org/html/rfc6020')

r = {}

for line in resp.text.split('\n'):
    m = re.search("([^ ]+)'s Substatements", line)
    if m:
        name = m.group(1)
        r[name] = {'1': [], '0..1': [], '0..n':[]}

    m = re.search("\|(.*)\|.*\|.*0..1", line)
    if m:
        r[name]['0..1'].append(m.group(1).strip())
    m = re.search("\|(.*)\|.*\|.*0..n", line)
    if m:
        r[name]['0..n'].append(m.group(1).strip())
    m = re.search("\|(.*)\|.*\|.* 1", line)
    if m:
        r[name]['1'].append(m.group(1).strip())



print(json.dumps(r,indent=4))
