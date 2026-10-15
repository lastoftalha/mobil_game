#!/usr/bin/env bash
# Bitasarımlazım sitesini yerel bilgisayarda kurar ve açar (macOS / Linux).
# Kullanım: proje klasöründe  ./baslat.sh
set -e
cd "$(dirname "$0")"

PY=python3
command -v $PY >/dev/null 2>&1 || PY=python
if ! command -v $PY >/dev/null 2>&1; then
  echo "Python bulunamadı. https://www.python.org/downloads/ adresinden Python 3.10+ kurun."
  exit 1
fi

if [ ! -d .venv ]; then
  echo ">> Sanal ortam oluşturuluyor..."
  $PY -m venv .venv
fi
VPY=.venv/bin/python

echo ">> Paketler kuruluyor..."
$VPY -m pip install -q --upgrade pip
$VPY -m pip install -q -r requirements.txt

[ -f .env ] || echo "DJANGO_DEBUG=1" > .env

echo ">> Veritabanı hazırlanıyor..."
$VPY manage.py migrate -v0
$VPY manage.py seed_site
DJANGO_SUPERUSER_PASSWORD="bitasarim2026" $VPY manage.py createsuperuser --noinput \
  --username admin --email admin@bitasarimlazim.com >/dev/null 2>&1 || true

echo ""
echo "=============================================="
echo " Site:  http://127.0.0.1:8000/"
echo " Panel: http://127.0.0.1:8000/panel/"
echo " Kullanıcı: admin   Şifre: bitasarim2026"
echo " (Şifreyi panelde Hesabım'dan değiştirin)"
echo " Kapatmak için: Ctrl+C"
echo "=============================================="
( sleep 3; (command -v open >/dev/null && open http://127.0.0.1:8000/) || (command -v xdg-open >/dev/null && xdg-open http://127.0.0.1:8000/) ) >/dev/null 2>&1 &
$VPY manage.py runserver 127.0.0.1:8000
