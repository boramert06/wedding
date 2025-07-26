# 🎉 Düğün Hatıra Yükleme Uygulaması

Bu Flask tabanlı web uygulaması, düğün davetlilerinin kendi fotoğraflarını ve sesli mesajlarını yükleyerek hatıra bırakmalarını sağlar. Admin paneli ile tüm yüklemeler yönetilebilir, indirilebilir ve gerekirse silinebilir.

---

## 🚀 Özellikler

- 📸 Misafirler birden fazla fotoğraf yükleyebilir.
- 🎤 Web tarayıcı üzerinden ses kaydı alabilir ve yükleyebilir.
- 🧾 Fotoğraflar ve sesler kullanıcı adıyla birlikte veritabanına kaydedilir.
- 📥 Admin paneli ile tüm fotoğraf ve sesleri görme, indirme ve silme işlemleri yapılabilir.
- 🔐 Admin girişi şifre korumalıdır.
- 📦 Veritabanı PostgreSQL'dir.
- 🧾 QR kod üretimi ile kolay erişim linki sağlanır.

---

## 🛠 Kurulum

### 1. Gereksinimler

- Python 3.8+
- PostgreSQL (örneğin: `weddingphoto` adında bir veritabanı oluşturulmalı)
- Paketler: Flask, psycopg2, qrcode, werkzeug

---

## 📱 Ses Kaydı Özelliği
Tarayıcı mikrofon erişimiyle ses kaydı yapılabilir. Maksimum 1 dakika ile sınırlandırılmıştır. WebM formatında kaydedilir.

---

## 🔐 Admin Panel
Giriş: http://localhost:5000/admin/login

Admin panel üzerinden:

-Yüklenen tüm fotoğrafları ve sesleri görüntüleyebilir.
-Tek tek veya topluca indirebilir.
-Silme işlemleri yapabilir.
-QR kodu indirerek davetlilere gönderebilirsiniz.

---


