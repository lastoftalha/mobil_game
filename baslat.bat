@echo off
REM Bitasarimlazim sitesini yerel bilgisayarda kurar ve acar (Windows).
REM Kullanim: proje klasorunde baslat.bat dosyasina cift tiklayin.
chcp 65001 >nul
cd /d "%~dp0"

set PY=
where py >nul 2>nul && set PY=py -3
if not defined PY (where python >nul 2>nul && set PY=python)
if not defined PY (
  echo Python bulunamadi. https://www.python.org/downloads/ adresinden Python 3.10+ kurun.
  echo Kurulumda "Add python.exe to PATH" kutusunu isaretlemeyi unutmayin.
  pause
  exit /b 1
)

if not exist .venv (
  echo ^>^> Sanal ortam olusturuluyor...
  %PY% -m venv .venv || goto :hata
)
set VPY=.venv\Scripts\python.exe

echo ^>^> Paketler kuruluyor...
%VPY% -m pip install -q --upgrade pip
%VPY% -m pip install -q -r requirements.txt || goto :hata

if not exist .env echo DJANGO_DEBUG=1> .env

echo ^>^> Veritabani hazirlaniyor...
%VPY% manage.py migrate -v0 || goto :hata
%VPY% manage.py seed_site || goto :hata
set DJANGO_SUPERUSER_PASSWORD=bitasarim2026
%VPY% manage.py createsuperuser --noinput --username admin --email admin@bitasarimlazim.com >nul 2>nul
set DJANGO_SUPERUSER_PASSWORD=

echo.
echo ==============================================
echo  Site:  http://127.0.0.1:8000/
echo  Panel: http://127.0.0.1:8000/panel/
echo  Kullanici: admin   Sifre: bitasarim2026
echo  (Sifreyi panelde Hesabim'dan degistirin)
echo  Kapatmak icin bu pencereyi kapatin.
echo ==============================================
start "" cmd /c "timeout /t 4 >nul & start http://127.0.0.1:8000/"
%VPY% manage.py runserver 127.0.0.1:8000
goto :eof

:hata
echo.
echo Bir hata olustu. Yukaridaki mesaji Claude'a gonderin.
pause
