#!/bin/bash
cd bot
python3 -m unittest discover
cd ..
python3 main.py