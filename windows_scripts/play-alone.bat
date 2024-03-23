@echo off
rem cd
CD Downloads/uno-py-master/uno-py-master
rem cd Downloads/uno-py-master
ECHO "What modes are you using?"
ECHO "Enter numbers, without spaces"
ECHO "0. Regular (no modes)"
ECHO "1. 7/0"
ECHO "2. Stack +2"
ECHO "3. Take many cards"
set /p modes="Enter numbers:"
rem set /p name="What's your name?"  &&

py server.py localhost 44444 2 %m% &
py client.py --human -name %name% &
sleep 2 &&
py client.py --sentient