#!/bin/bash

cmd.exe /C taskkill /IM CommUMotion.exe /F
cd C:/Users/kumadalab/Desktop/COMMU/COMMU/motion/
start CommUMotion.exe

python C:/Users/kumadalab/Desktop/COMMU/Shiro/auto.py