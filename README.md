📝 NoteFlow

Modern, AI destekli ve Dockerize edilmiş Python tabanlı not alma uygulaması.

NoteFlow; güçlü not yönetimi, zengin metin düzenleme araçları ve yapay zeka destekli özellikleri modern ve kullanıcı dostu bir arayüzde bir araya getirir.

✨ Özellikler
📚 Not Yönetimi
Not oluşturma, düzenleme ve silme
Gerçek zamanlı arama
Etiket tabanlı organizasyon
Otomatik kayıt
Kelime ve karakter sayacı
JSON tabanlı yerel depolama
🎨 Zengin Metin Düzenleme
Kalın yazı
İtalik yazı
Altı çizili metin
Metin rengi değiştirme
Metin vurgulama
Özel font ve boyut desteği
Modern düzenleme deneyimi
🌙 Modern Arayüz
Açık ve Koyu Tema
Üç panelli tasarım
Responsive yapı
CustomTkinter tabanlı arayüz
Verimlilik odaklı klavye kısayolları
🤖 Yapay Zeka Özellikleri
Gemini AI entegrasyonu
Not özetleme
Yazım ve dil bilgisi düzeltme
Benzer notları birleştirme
Not içeriklerine göre sohbet desteği
⌨️ Klavye Kısayolları
Kısayol	İşlev
Ctrl + N	Yeni Not
Ctrl + S	Kaydet
Ctrl + A	Tümünü Seç
Ctrl + Shift + A	AI Asistanını Aç
🛠️ Kullanılan Teknolojiler
Python 3.12+
Tkinter
CustomTkinter
Google Gemini API
Keyring
JSON Storage
Docker
Docker Compose
🚀 Kurulum (Linux)
1. Ön Gereksinimler

Sisteminizde Docker ve Docker Compose kurulu olmalıdır:

sudo apt update
sudo apt install docker.io docker-compose

sudo usermod -aG docker $USER

Docker grubunun aktif olması için oturumu kapatıp tekrar açın veya yeni bir terminal başlatın.

2. Projeyi Klonlayın
git clone https://github.com/Ahmetdemirci17/Noteapp.git

cd Noteapp
3. Uygulamayı Başlatın

İlk çalıştırmada:

docker-compose up -d --build

Bu komut:

Docker imajını oluşturur
Gerekli bağımlılıkları yükler
Uygulamayı arka planda başlatır
4. Kullanım

Uygulama arka planda çalışacaktır.

Terminalden hızlı başlatmak için ~/.bashrc dosyanıza aşağıdaki satırı ekleyebilirsiniz:

alias noteapp='cd /path/to/Noteapp && docker-compose up -d'

/path/to/Noteapp kısmını kendi proje dizininiz ile değiştirin.

Daha sonra:

source ~/.bashrc

ve uygulamayı şu şekilde başlatabilirsiniz:

noteapp
🔧 Sorun Giderme

Konteyner veya yapılandırma hatalarıyla karşılaşırsanız temiz kurulum yapın:

docker-compose down

docker-compose up -d --build
🧠 Yapay Zeka Yetenekleri

Gemini AI sayesinde:

Uzun notları özetleme
Yazım düzeltme
Benzer notları birleştirme
Notlar hakkında soru-cevap
İçerik üretme desteği
📁 Veri Depolama

Tüm notlar ve ayarlar yerel olarak JSON formatında saklanır.

data/
├── notes.json
└── settings.json
🚀 Yol Haritası
Markdown desteği
PDF dışa aktarma
Bulut senkronizasyonu
Çoklu çalışma alanları
Otomatik AI etiketleme
Cihazlar arası senkronizasyon
🔒 Gizlilik

Notlarınız cihazınızda yerel olarak saklanır. Yapay zeka özelliklerini kullanmadığınız sürece hiçbir veri dış servislere gönderilmez.

📄 Lisans

Bu proje MIT Lisansı ile lisanslanmıştır.

👨‍💻 Geliştirici

Ahmet Demirci

GitHub: https://github.com/Ahmetdemirci17
