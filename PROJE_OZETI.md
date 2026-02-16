# 🛡️ TR-Gate Pro (v2.5)
### Türkiye İçin Optimize Edilmiş Gelişmiş DPI Bypass & Filtreleme Sistemi

TR-Gate Pro, Türkiye'deki ISS bazlı engelleme (DPI) yöntemlerini aşmak için geliştirilmiş, hız kaybı yaşatmayan ve kullanıcı dostu bir tünelleme arayüzüdür. Özellikle Discord, Twitch ve benzeri platformlardaki erişim sorunlarını kökten çözmeyi hedefler.

## ✨ Öne Çıkan Özellikler

*   **⚡ Sıfır Hız Kaybı:** VPN tabanlı olmadığı için internet hızınızda veya oyunlardaki ping değerinizde hiçbir değişim olmaz.
*   **🎯 Seçici Tünelleme (Blacklist):** Sadece belirlediğiniz sitelere müdahale eder. Diğer tüm trafiğiniz (Bankacılık, Steam, Spotify vb.) doğrudan ISS üzerinden geçer.
*   **🖥️ Profesyonel GUI:** Modern, karanlık temalı ve kullanıcı dostu Python (Tkinter) arayüzü.
*   **📦 Standalone (Tek EXE):** Herhangi bir kütüphane veya Python kurulumuna ihtiyaç duymaz, tüm bağımlılıklar gömülüdür.
*   **🔄 Akıllı Başlangıç:** Windows ile otomatik başlama (isteğe bağlı) ve sistem tepsisine (Tray) küçülme özelliği.
*   **🧹 Derin Temizlik:** Uygulama kapandığında tüm servisleri ve sürücüleri (WinDivert, GoodbyeDPI) otomatik durdurur ve siler.

## 🧠 Çalışma Mantığı

TR-Gate Pro, arka planda **GoodbyeDPI** motorunu ve **WinDivert** sürücüsünü kullanır. 

1.  **Paket Yakalama:** WinDivert sürücüsü üzerinden sadece blacklistteki sitelere giden TCP paketleri yakalanır.
2.  **DPI Bypass:** Yakalanan paketler, ISS'nin DPI (Derin Paket İnceleme) sistemlerini şaşırtacak şekilde parçalanır veya başlık bilgileri manipüle edilir (Örn: HTTP Fragmentation, Host Header case manipulation).
3.  **Hizmet Yönetimi:** Python arayüzü, bu motoru bir Windows Servisi (`TRGatePro`) olarak kaydeder ve yönetir.

## ⚙️ Güvenli Kapanış & Temizlik Mechanisms

Uygulamanın en güçlü yanlarından biri "arkada çöp bırakmamasıdır". Uygulamadan tamamen çıktığınızda veya "STOP SYSTEM" dediğinizde şu işlemler sırasıyla yapılır:
*   `sc stop TRGatePro` & `sc delete TRGatePro`: Ana servis durdurulur ve Windows'tan kaldırılır.
*   `sc stop/delete WinDivert`: Paket yakalama sürücüsü kerneldan boşaltılır.
*   `taskkill /F /IM goodbyedpi.exe`: Arka planda asılı kalabilecek motor süreçleri zorla sonlandırılır.

## 🚀 Kullanım
1. `dist/TR-Gate_Pro.exe` dosyasını yönetici olarak çalıştırın.
2. **START SYSTEM** butonuna basın. Durum paneli **ACTIVE** olduğunda özgürsünüz.
3. Sadece istediğiniz siteleri tünellemek için "Domain Manager" kısmını kullanın.

---
*Geliştirici Notu: Bu proje, internet özgürlüğünü teknik sınırlarla korumak amacıyla tasarlanmıştır.*
