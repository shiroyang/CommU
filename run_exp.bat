@echo off
echo Killing all Python processes...
taskkill /F /IM python.exe
taskkill /F /IM python3.exe
echo All Python processes have been terminated.

echo Executing your Python script...
python "C:/Users/kumadalab/Desktop/COMMU/carlos/motionsender_edit.py"
echo Script execution complete.
