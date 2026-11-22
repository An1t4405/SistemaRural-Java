@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist target\classes mkdir target\classes
javac -encoding UTF-8 -d target\classes src\main\java\pe\sistemarural\*.java
if errorlevel 1 (
  echo.
  echo No se pudo compilar. Verifique que tenga instalado JDK 17 o superior.
  pause
  exit /b 1
)
java -cp target\classes pe.sistemarural.App
if errorlevel 1 pause
