#!/usr/bin/env sh

kill $(pgrep -a python | grep bot.py | cut -d ' ' -f 1)
