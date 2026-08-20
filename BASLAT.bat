@echo off
setlocal
cd /d "%~dp0"

if /i "%~1"=="api" goto api
if /i "%~1"=="web" goto web

echo PTT AI servisleri hazirlaniyor...
start "PTT AI - FastAPI" cmd /k call "%~f0" api
start "PTT AI - Next.js" cmd /k call "%~f0" web

echo FastAPI ve Next.js iki ayri terminalde baslatiliyor.
echo Web arayuzu: http://localhost:3000
echo API belgeleri: http://localhost:8000/docs
echo Ilk kurulum bilgisayar ve internet hizina gore birkac dakika surebilir.
endlocal
exit /b 0

:api
set "PYTHON_EXE="
set "PYTHON_EXTRA="

if exist "%USERPROFILE%\anaconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\python.exe"

if not defined PYTHON_EXE (
  for /d %%D in ("%APPDATA%\uv\python\cpython-*") do (
    if exist "%%~fD\python.exe" if not defined PYTHON_EXE set "PYTHON_EXE=%%~fD\python.exe"
  )
)

if not defined PYTHON_EXE (
  for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%~fD\python.exe" if not defined PYTHON_EXE set "PYTHON_EXE=%%~fD\python.exe"
  )
)

if not defined PYTHON_EXE (
  for /f "delims=" %%P in ('where python.exe 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
)

if defined PYTHON_EXE (
  "%PYTHON_EXE%" --version >nul 2>nul || set "PYTHON_EXE="
)

if not defined PYTHON_EXE (
  for /f "delims=" %%P in ('where py.exe 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
  if defined PYTHON_EXE set "PYTHON_EXTRA=-3"
)

if not defined PYTHON_EXE goto python_missing

echo Kullanilan Python: %PYTHON_EXE%
if not exist ".api-venv\Scripts\python.exe" (
  echo API sanal ortami olusturuluyor...
  "%PYTHON_EXE%" %PYTHON_EXTRA% -m venv .api-venv || goto api_failed
)

echo API paketleri kontrol ediliyor...
".api-venv\Scripts\python.exe" -m pip install -r backend\requirements.txt || goto api_failed
echo FastAPI baslatiliyor: http://localhost:8000
".api-venv\Scripts\python.exe" -m uvicorn backend.main:app --reload --port 8000
goto end

:web
set "NPM_EXE="
if exist "%ProgramFiles%\nodejs\npm.cmd" set "NPM_EXE=%ProgramFiles%\nodejs\npm.cmd"
if not defined NPM_EXE (
  for /f "delims=" %%N in ('where npm.cmd 2^>nul') do if not defined NPM_EXE set "NPM_EXE=%%N"
)
if not defined NPM_EXE goto node_missing

cd /d "%~dp0frontend"
if not exist ".env.local" copy /y ".env.example" ".env.local" >nul
if not exist "node_modules\next\package.json" (
  echo Web paketleri kuruluyor...
  call "%NPM_EXE%" install || goto web_failed
)
echo Next.js baslatiliyor: http://localhost:3000
call "%NPM_EXE%" run dev
goto end

:python_missing
echo.
echo HATA: Calisabilen bir Python kurulumu bulunamadi.
echo Anaconda aciksa kapatip yeniden deneyin veya Python 3.12/3.13 kurarken PATH secenegini acin.
goto end

:node_missing
echo.
echo HATA: Node.js / npm bulunamadi.
echo https://nodejs.org adresinden LTS surumunu kurup VS Code'u yeniden acin.
goto end

:api_failed
echo.
echo HATA: API kurulumu veya baslatmasi tamamlanamadi. Yukaridaki ilk kirmizi satiri paylasin.
goto end

:web_failed
echo.
echo HATA: Web kurulumu veya baslatmasi tamamlanamadi. Yukaridaki ilk kirmizi satiri paylasin.
goto end

:end
echo.
echo Bu pencereyi kapatmak icin bir tusa basin.
pause >nul
endlocal
