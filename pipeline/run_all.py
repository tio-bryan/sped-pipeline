# !/usr/bin/env python3
# -*- coding: utf-8 -*-


import subprocess


scripts = ['bronze.py', 'silver.py', 'gold.py']

for script in scripts:
    print(f'Starting {script}...')

    result = subprocess.run(['python', script], capture_output=True, text=True)

    print(result.stdout)

    if result.returncode != 0:
        print(f'Error in {script}: {result.stderr}')
        break