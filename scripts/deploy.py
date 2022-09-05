#!/usr/bin/env python3

import argparse
import os
import sys
import requests
import yaml

commands=[
    'deploy',
    'logs',
    'status'
]

if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('command', choices=commands)
    args = a.parse_args()

    with open('scripts/conf.yml', 'r') as h:
        conf=yaml.safe_load(h)

    for c in ['port', 'address']:
        if c not in conf:
            raise Exception(f'Missing {c} in conf')

    addr = conf['address']
    port = conf['port']

    res = requests.get(f'http://{addr}:{port}/{args.command}')
    print(res.url)
    if res.status_code != 200:
        print(f'Request ended with: {res.status_code}')
        print(res.text)
        sys.exit(1)

    print(res.text)
