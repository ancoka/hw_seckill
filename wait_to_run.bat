@echo off
setlocal

:: 目标时间（10:02）
set TARGET_HOUR=10
set TARGET_MINUTE=02

:check_time
:: 获取当前时间的小时和分钟
for /f "tokens=1,2 delims=:" %%a in ("%time%") do (
    set CURRENT_HOUR=%%a
    set CURRENT_MINUTE=%%b
)

:: 去掉小时和分钟中的空格（如果小时为单数，系统会添加前导空格）
set CURRENT_HOUR=%CURRENT_HOUR: =%
set CURRENT_MINUTE=%CURRENT_MINUTE: =%

echo %CURRENT_HOUR%:%CURRENT_MINUTE% | checking ...
:: 如果当前时间等于目标时间，运行命令并退出
if "%CURRENT_HOUR%"=="%TARGET_HOUR%" if "%CURRENT_MINUTE%"=="%TARGET_MINUTE%" (
    echo %CURRENT_HOUR%:%CURRENT_MINUTE% | 执行 python main.py ...
    python main.py
    exit /b
)

:: 每隔 60 秒检查一次时间
timeout /t 60 /nobreak >nul
goto check_time