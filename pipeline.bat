@echo off
set GCC_DIR=C:\msys64\ucrt64\bin
set PATH=%GCC_DIR%;%PATH%
python generateur\generateur.py --suite -o instances\generated || goto :fin
python generateur\validateur.py instances instances\generated || goto :fin
g++ -std=c++17 -O2 -static my_solution.cpp -o solution.exe || goto :fin
if not exist outputs mkdir outputs
for %%f in (instances\*.in instances\generated\*.in) do (
    echo.
    echo ==================== %%~nf ====================
    solution.exe < "%%f" > "outputs\%%~nf.out" 2>nul
    <nul set /p ="score.py : "
    python score.py "%%f" "outputs\%%~nf.out"
    python statistiques\stats_instance.py "%%f" > nul
    python statistiques\stats_solution.py "%%f" "outputs\%%~nf.out"
)
echo.
echo reports and charts: statistiques\sorties\INSTANCE_NAME\
:fin
pause
