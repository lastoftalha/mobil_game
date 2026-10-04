# NOVA ARMADA

Telefon için tasarlanmış, dikey kaydırmalı 2D uzay savaşı. Tarayıcıda çalışır, ana ekrana uygulama olarak eklenebilir (PWA) ve internet olmadan da oynanır.

## Oynanış

- **Kontrol:** Ekranın herhangi bir yerinde parmağını sürükle; gemi parmağının hareketini takip eder, parmağın gemiyi kapatmaz. Ateş otomatiktir.
- **Sektörler:** Her sektör 6 dalga ve sonunda bir **amiral gemisi** (boss) içerir. Amirali düşürünce yeni sektöre geçersin: gökyüzü, düşman renkleri ve zorluk değişir.
- **Düşmanlar:** Avcı, dalgalı uçan, nişancı, dalış yapan kamikaze, ağır tank, bonus UFO ve parçalanan meteorlar.
- **Amiraller:** Üç evreli savaş: dairesel yaylım, nişanlı atış, spiral, güdümlü füze, destek çağırma ve uyarılı lazer ışını.
- **Güçlendirmeler:** Mavi şimşek silahı 5 seviyeye kadar yükseltir (5. seviyede güdümlü füzeler). Yeşil kalkan 3 darbe emer, kırmızı hap gövdeyi onarır, sarı yıldız Nova'yı doldurur. Hasar alınca silah bir seviye düşer.
- **Nova bombası:** Düşman yok ettikçe dolar. Dolunca sağ alttaki düğmeye dokun: ekrandaki tüm mermileri siler, düşmanlara ağır hasar verir.
- **Kombo:** Arka arkaya hızlı öldürmeler çarpanı x8'e kadar yükseltir; hasar alınca sıfırlanır.
- **Hangar:** Topladığın kredilerle 3 gemiden birini (Şahin, Engerek, Titan) açar, 5 kalıcı yükseltmeyi 5 seviyeye kadar geliştirirsin.

Masaüstünde: yön tuşları / WASD ile hareket, **Boşluk** Nova, **Esc / P** duraklat.

## Çalıştırma

Statik dosyalardan oluşur, derleme gerekmez:

```bash
python3 -m http.server 8000
# tarayıcıda http://localhost:8000 adresini aç
```

Telefonda oynamak için klasörü herhangi bir statik sunucuya (GitHub Pages, Netlify vb.) yükle, sayfayı aç ve "Ana ekrana ekle"yi seç.

## Proje yapısı

```
index.html             giriş sayfası
src/config.js          gemi, yükseltme, sektör ve amiral verileri
src/save.js            ilerleme kaydı (localStorage)
src/audio.js           müzik geçişleri ve ses efektleri
src/ui.js              arayüz bileşenleri, prosedürel dokular, paralaks arka plan
src/scenes.js          açılış, menü, hangar, ayarlar, duraklatma, oyun sonu
src/game.js            oynanış: oyuncu, dalgalar, düşmanlar, amiraller, efektler
assets/                atlas, arka planlar, sesler, yazı tipleri
tools/build_assets.py  atlası ve sesleri orijinal paketlerden yeniden üretir
```

Varlık kaynakları ve lisanslar için [CREDITS.md](CREDITS.md) dosyasına bak.
