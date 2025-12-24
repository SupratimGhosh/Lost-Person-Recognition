@echo off
start cmd /k "cd Frontend && npm install && npm run dev"
start cmd /k "cd Backend && npm install && npm run start"
echo Both frontend and backend are starting in separate windows.
echo Close the command prompt windows to stop the applications.
pause