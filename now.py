import cloudscraper
from bs4 import BeautifulSoup
import time
import re
import subprocess
from urllib.parse import urljoin

# --- AYARLAR ---
BASE_URL = "https://www.nowtv.com.tr"
M3U_FILENAME = "nowtv.m3u"

# --- SABİT DİZİ LİSTESİ (Senin JSON Verin) ---
# Bot artık siteyi taramakla uğraşmaz, bu listedeki her şeye gidip bölüm arar.
STARTING_DATA = {
    "kizil-goncalar": { "isim": "Kızıl Goncalar", "link": "https://www.nowtv.com.tr/Kizil-Goncalar/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1721", "kategori": "NOW DIZILER" },
    "hudutsuz-sevda": { "isim": "Hudutsuz Sevda", "link": "https://www.nowtv.com.tr/Hudutsuz-Sevda/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1693", "kategori": "NOW DIZILER" },
    "yabani": { "isim": "Yabani", "link": "https://www.nowtv.com.tr/Yabani/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1691", "kategori": "NOW DIZILER" },
    "leyla-hayat-ask-adalet": { "isim": "Leyla: Hayat… Aşk… Adalet...", "link": "https://www.nowtv.com.tr/Leyla-Hayat-Ask-Adalet/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1780", "kategori": "NOW DIZILER" },
    "sakir-pasa-ailesi": { "isim": "Şakir Paşa Ailesi", "link": "https://www.nowtv.com.tr/Sakir-Pasa-Ailesi-Mucizeler-ve-Skandallar/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1786", "kategori": "NOW DIZILER" },
    "ask-evlilik-bosanma": { "isim": "Aşk Evlilik Boşanma", "link": "https://www.nowtv.com.tr/Ask-Evlilik-Bosanma/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1785", "kategori": "NOW DIZILER" },
    "gizli-bahce": { "isim": "Gizli Bahçe", "link": "https://www.nowtv.com.tr/Gizli-Bahce/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1777", "kategori": "NOW DIZILER" },
    "kirli-sepeti": { "isim": "Kirli Sepeti", "link": "https://www.nowtv.com.tr/Kirli-Sepeti/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1694", "kategori": "NOW DIZILER" },
    "kotu-kan": { "isim": "Kötü Kan", "link": "https://www.nowtv.com.tr/Kotu-Kan/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1759", "kategori": "NOW DIZILER" },
    "gaddar": { "isim": "Gaddar", "link": "https://www.nowtv.com.tr/Gaddar/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1719", "kategori": "NOW DIZI ARSIV" },
    "sahane-hayatim": { "isim": "Şahane Hayatım", "link": "https://www.nowtv.com.tr/Sahane-Hayatim/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1708", "kategori": "NOW DIZI ARSIV" },
    "yasak-elma": { "isim": "Yasak Elma", "link": "https://www.nowtv.com.tr/Yasak-Elma/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1324", "kategori": "NOW DIZI ARSIV" },
    "mucize-doktor": { "isim": "Mucize Doktor", "link": "https://www.nowtv.com.tr/Mucize-Doktor/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1495", "kategori": "NOW DIZI ARSIV" },
    "sen-cal-kapimi": { "isim": "Sen Çal Kapımı", "link": "https://www.nowtv.com.tr/Sen-Cal-Kapimi/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1536", "kategori": "NOW DIZI ARSIV" },
    "bambaska-biri": { "isim": "Bambaşka Biri", "link": "https://www.nowtv.com.tr/Bambaska-Biri/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1698", "kategori": "NOW DIZI ARSIV" },
    "adim-farah": { "isim": "Adım Farah", "link": "https://www.nowtv.com.tr/Adim-Farah/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1661", "kategori": "NOW DIZI ARSIV" },
    "mahkum": { "isim": "Mahkum", "link": "https://www.nowtv.com.tr/Mahkum/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1615", "kategori": "NOW DIZI ARSIV" },
    "son-yaz": { "isim": "Son Yaz", "link": "https://www.nowtv.com.tr/Son-Yaz/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1571", "kategori": "NOW DIZI ARSIV" },
    "savasci": { "isim": "Savaşçı", "link": "https://www.nowtv.com.tr/Savasci/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1167", "kategori": "NOW DIZI ARSIV" },
    "ask-mantik-intikam": { "isim": "Aşk Mantık İntikam", "link": "https://www.nowtv.com.tr/Ask-Mantik-Intikam/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1588", "kategori": "NOW DIZI ARSIV" },
    "karagul": { "isim": "Karagül", "link": "https://www.nowtv.com.tr/Karagul/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/35", "kategori": "NOW DIZI ARSIV" },
    "kiraz-mevsimi": { "isim": "Kiraz Mevsimi", "link": "https://www.nowtv.com.tr/Kiraz-Mevsimi/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/50", "kategori": "NOW DIZI ARSIV" },
    "bay-yanlis": { "isim": "Bay Yanlış", "link": "https://www.nowtv.com.tr/Bay-Yanlis/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1533", "kategori": "NOW DIZI ARSIV" },
    "korkma-ben-yanindayim": { "isim": "Korkma Ben Yanındayım", "link": "https://www.nowtv.com.tr/Korkma-Ben-Yanindayim/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1731", "kategori": "NOW DIZI ARSIV" },
    "sana-bir-sir-verecegim": { "isim": "Sana Bir Sır Vereceğim", "link": "https://www.nowtv.com.tr/Sana-Bir-Sir-Verecegim/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/38", "kategori": "NOW DIZI ARSIV" },
    "lale-devri": { "isim": "Lale Devri", "link": "https://www.nowtv.com.tr/Lale-Devri/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1", "kategori": "NOW DIZI ARSIV" },
    "no-309": { "isim": "No: 309", "link": "https://www.nowtv.com.tr/No-309/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/68", "kategori": "NOW DIZI ARSIV" },
    "bizim-hikaye": { "isim": "Bizim Hikaye", "link": "https://www.nowtv.com.tr/Bizim-Hikaye/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1266", "kategori": "NOW DIZI ARSIV" },
    "kadin": { "isim": "Kadın", "link": "https://www.nowtv.com.tr/Kadin/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1283", "kategori": "NOW DIZI ARSIV" },
    "now-ana-haber": { "isim": "NOW Ana Haber", "link": "https://www.nowtv.com.tr/Selcuk-Tepeli-ile-NOW-Ana-Haber", "resim": "https://www.nowtv.com.tr/i/thumbnail/1714", "kategori": "NOW HABER" },
    "now-haber-haftasonu": { "isim": "Gülbin Tosun ile NOW Ana Haber Hafta Sonu", "link": "https://www.nowtv.com.tr/Gulbin-Tosun-ile-NOW-Ana-Haber-Hafta-Sonu", "resim": "https://www.nowtv.com.tr/i/thumbnail/1715", "kategori": "NOW HABER" },
    "alar-saat": { "isim": "İlker Karagöz ile Çalar Saat", "link": "https://www.nowtv.com.tr/Ilker-Karagoz-ile-Calar-Saat", "resim": "https://www.nowtv.com.tr/i/thumbnail/1716", "kategori": "NOW HABER" },
    "cagla-ile-yeni-bir-gun": { "isim": "Çağla ile Yeni Bir Gün", "link": "https://www.nowtv.com.tr/Cagla-ile-Yeni-Bir-Gun/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1360", "kategori": "NOW PROGRAMLAR" },
    "en-hamarat-benim": { "isim": "En Hamarat Benim", "link": "https://www.nowtv.com.tr/En-Hamarat-Benim/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1592", "kategori": "NOW PROGRAMLAR" },
    "fatih-savas-ile-sabah-sohbetleri": { "isim": "Fatih Savaş ile Sabah Sohbetleri", "link": "https://www.nowtv.com.tr/Fatih-Savas-ile-Sabah-Sohbetleri/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1429", "kategori": "NOW PROGRAMLAR" },
    "memet-ozer-ile-mutfakta": { "isim": "Memet Özer ile Mutfakta", "link": "https://www.nowtv.com.tr/Memet-Ozer-ile-Mutfakta/izle", "resim": "https://www.nowtv.com.tr/i/thumbnail/1296", "kategori": "NOW PROGRAMLAR" }
}

def get_single_m3u8(scraper, url):
    """Eksik kalan tekil sayfalardan m3u8 çeker."""
    try:
        time.sleep(0.3)
        r = scraper.get(url, timeout=10)
        # Basit Regex ile m3u8 bul
        match = re.search(r'https?://[^\s"\'\\,]+\.m3u8[^\s"\'\\,]*', r.text)
        if match:
            return match.group(0).replace('\\/', '/')
        return url
    except:
        return url

def commit_and_push(file_name):
    print(f"\n📤 {file_name} GitHub'a gönderiliyor...")
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
        subprocess.run(["git", "add", file_name], check=True)
        
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if status:
            subprocess.run(["git", "commit", "-m", f"🔄 NOW TV Güncelleme: {time.strftime('%Y-%m-%d')}"], check=True)
            subprocess.run(["git", "push", "--force"], check=True)
            print("🚀 GitHub'a başarıyla yüklendi!")
        else:
            print("⚠️ Değişiklik yok.")
    except Exception as e:
        print(f"❌ Git Hatası: {e}")

def run_scraper():
    print(f"🚀 Bot Başlatıldı. {len(STARTING_DATA)} adet içerik işlenecek.")
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    
    memory_data = {}

    # Listeyi döngüye al
    for key, item in STARTING_DATA.items():
        title = item['isim']
        link = item['link']
        poster = item['resim']
        category = item.get('kategori', 'NOW GENEL')
        
        print(f"\n🔍 [{category}] {title} taranıyor...")

        # Link Düzenleme (/bolumler ekle)
        # Haber ve Spor sayfalarında /bolumler olmayabilir, direkt linki kullan
        if "Haber" in title or "Spor" in title:
            target_url = link
        else:
            target_url = link.split('/izle')[0] + "/bolumler"

        try:
            resp = scraper.get(target_url, timeout=10)
            
            # Tüm m3u8 linklerini çek
            all_m3u8s = re.findall(r'https?://[^\s"\'\\,]+\.m3u8[^\s"\'\\,]*', resp.text)
            all_m3u8s = list(dict.fromkeys([m.replace('\\/', '/') for m in all_m3u8s]))

            soup = BeautifulSoup(resp.text, 'html.parser')
            eps = []

            # 1. YÖNTEM: Select Box (Diziler)
            select_box = soup.find('select', id='video-finder-changer')
            
            if select_box:
                options = select_box.find_all('option', {'data-target': True})
                print(f"   ℹ️ {len(options)} Bölüm bulundu.")
                
                for i, opt in enumerate(options):
                    ep_name = opt.get_text(strip=True)
                    ep_url = opt['data-target']
                    
                    # Sıradaki m3u8'i kullan veya derin tarama yap
                    final_link = all_m3u8s[i] if i < len(all_m3u8s) else ep_url
                    
                    if ".m3u8" not in final_link:
                        if not ep_url.startswith('http'):
                            ep_url = urljoin(BASE_URL, ep_url)
                        final_link = get_single_m3u8(scraper, ep_url)
                    
                    eps.append({"ad": ep_name, "link": final_link})

            # 2. YÖNTEM: Video Kartları (Haber/Program/Arşiv)
            else:
                cards = soup.select('.video-item, .card-video, .col-md-4 a')
                valid_cards = [c for c in cards if c.get('href') and '/izle/' in c.get('href')]
                
                if valid_cards:
                    print(f"   ℹ️ {len(valid_cards)} Video bulundu (Alternatif).")
                    for c in valid_cards[:20]: # Son 20 video ile sınırla
                        v_link = urljoin(BASE_URL, c.get('href'))
                        v_title = c.get('title') or c.get_text(strip=True) or "Bölüm"
                        
                        # Ana dizi linkiyle aynıysa atla
                        if v_link == link: continue
                        
                        final_link = get_single_m3u8(scraper, v_link)
                        eps.append({"ad": v_title, "link": final_link})
                else:
                    print("   ❌ Bölüm bulunamadı.")

            # Veriyi kaydet
            if eps:
                memory_data[key] = {
                    "isim": title,
                    "resim": poster,
                    "kategori": category,
                    "bolumler": eps
                }
                print(f"   ✅ Eklendi: {len(eps)} parça.")

        except Exception as e:
            print(f"   ⚠️ Hata: {e}")

    # M3U Oluştur
    if memory_data:
        create_m3u(memory_data)
    else:
        print("❌ Hiçbir veri işlenemedi.")

def create_m3u(data):
    print(f"\n📝 {M3U_FILENAME} oluşturuluyor...")
    with open(M3U_FILENAME, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        # Kategoriye göre sırala
        sorted_keys = sorted(data.keys(), key=lambda k: data[k]['kategori'])
        
        for key in sorted_keys:
            item = data[key]
            group = item['kategori']
            poster = item['resim']
            series_name = item['isim']
            
            for bolum in item['bolumler']:
                f.write(f'#EXTINF:-1 group-title="{group}" tvg-logo="{poster}", {series_name} - {bolum["ad"]}\n')
                f.write(f'{bolum["link"]}\n')
    
    commit_and_push(M3U_FILENAME)

if __name__ == "__main__":
    run_scraper()
