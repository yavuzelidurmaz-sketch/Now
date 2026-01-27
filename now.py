import cloudscraper
from bs4 import BeautifulSoup
import time
import re
import subprocess
from urllib.parse import urljoin

# --- AYARLAR ---
BASE_URL = "https://www.nowtv.com.tr"
M3U_FILENAME = "nowtv.m3u"

# KATEGORİ HARİTASI (URL -> Kategori Adı)
# Bu liste sırasıyla taranır.
CATEGORY_MAP = [
    {"url": "https://www.nowtv.com.tr/dizi-izle", "name": "NOW DIZILER"},
    {"url": "https://www.nowtv.com.tr/program-izle", "name": "NOW PROGRAMLAR"},
    {"url": "https://www.nowtv.com.tr/now-spor", "name": "NOW SPOR"},
    {"url": "https://www.nowtv.com.tr/now-haber", "name": "NOW HABER"},
    {"url": "https://www.nowtv.com.tr/dizi-arsivi", "name": "NOW DIZI ARSIV"},
    {"url": "https://www.nowtv.com.tr/program-arsivi", "name": "NOW PROGRAM ARSIV"}
]

def get_single_m3u8(scraper, url):
    """Eksik kalan tekil sayfalardan m3u8 çeker."""
    try:
        time.sleep(0.3)
        r = scraper.get(url, timeout=10)
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
            subprocess.run(["git", "commit", "-m", f"🔄 NOW TV M3U Update: {time.strftime('%Y-%m-%d')}"], check=True)
            subprocess.run(["git", "push", "--force"], check=True)
            print("🚀 GitHub'a başarıyla yüklendi!")
    except Exception as e:
        print(f"❌ Git Hatası: {e}")

def collect_dynamic_series(scraper):
    """
    Kategorileri tarar ve içerikleri kategorisine göre etiketleyerek listeler.
    """
    dynamic_data = {}
    print("🌍 Kategori sayfaları taranıyor...")

    for cat in CATEGORY_MAP:
        url = cat["url"]
        cat_name = cat["name"]
        print(f"   📂 Kategori Taranıyor: {cat_name} ({url})")
        
        try:
            resp = scraper.get(url, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Geniş selector ile içerikleri bul
            items = soup.select('ul.index-list li, .archive-list .row .col-md-3, .col-6.col-md-3, .col-lg-3, .video-item')

            for item in items:
                try:
                    link_tag = item.find('a', href=True)
                    if not link_tag: continue

                    href = link_tag['href']
                    full_link = urljoin(BASE_URL, href)
                    
                    # Filtreleme
                    if not any(x in href for x in ['/dizi/', '/program/', '/now-haber', '/now-spor', '/izle/']):
                        continue

                    # İsim Çıkarma
                    title = ""
                    img_tag = link_tag.find('img')
                    
                    if item.find('span', class_='title'):
                        title = item.find('span', class_='title').get_text(strip=True)
                    elif item.find('div', class_='title'):
                        title = item.find('div', class_='title').get_text(strip=True)
                    elif img_tag and img_tag.get('alt'):
                        title = img_tag.get('alt').strip()
                    else:
                        title = href.split('/')[-1].replace('-', ' ').title()

                    # Resim Çıkarma
                    img_url = ""
                    if img_tag:
                        img_url = img_tag.get('data-src') or img_tag.get('src')
                        if img_url and not img_url.startswith('http'):
                            img_url = urljoin(BASE_URL, img_url)

                    # ID (Key) oluşturma ve Kayıt
                    dizi_key = href.strip('/').split('/')[-1]

                    # Eğer bu içerik daha önce eklenmemişse ekle
                    if dizi_key not in dynamic_data:
                        dynamic_data[dizi_key] = {
                            "isim": title,
                            "link": full_link,
                            "resim": img_url,
                            "kategori": cat_name  # KATEGORİYİ BURADA ATIYORUZ
                        }
                except:
                    continue
        except Exception as e:
            print(f"   ⚠️ Hata ({url}): {e}")
    
    print(f"✅ Toplam {len(dynamic_data)} farklı içerik bulundu.\n")
    return dynamic_data

def run_scraper():
    print("🚀 Bot Başlatıldı. M3U Modu Aktif...")
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    
    target_series = collect_dynamic_series(scraper)
    
    if not target_series:
        print("❌ Hiçbir içerik bulunamadı!")
        return

    memory_data = {}

    for dizi_key, info in target_series.items():
        title = info.get('isim', 'Dizi')
        dizi_url = info.get('link', '')
        poster = info.get('resim', '')
        category = info.get('kategori', 'GENEL')
        
        # Link Düzenleme
        base_series_url = dizi_url.split('/izle')[0].rstrip('/')
        if "now-haber" in base_series_url or "now-spor" in base_series_url:
            bolumler_url = base_series_url 
        else:
            bolumler_url = base_series_url + "/bolumler"

        print(f"🔍 [{category}] {title} işleniyor...", end=" ", flush=True)
        
        try:
            response = scraper.get(bolumler_url, timeout=10)
            
            # Sayfadaki tüm m3u8'leri önbelleğe al
            found_m3u8s = re.findall(r'https?://[^\s"\'\\,]+\.m3u8[^\s"\'\\,]*', response.text)
            found_m3u8s = [m.replace('\\/', '/') for m in found_m3u8s]
            unique_m3u8s = list(dict.fromkeys(found_m3u8s))

            b_soup = BeautifulSoup(response.text, 'html.parser')
            eps = []
            
            select_box = b_soup.find('select', id='video-finder-changer')
            
            # 1. YÖNTEM: Select Box (Diziler/Programlar)
            if select_box:
                options = select_box.find_all('option', {'data-target': True})
                print(f"({len(options)} Bölüm)")
                
                for i, opt in enumerate(options):
                    b_title = opt.get_text(strip=True)
                    b_target = opt['data-target']
                    
                    # Sıradaki m3u8'i eşleştir veya derin tarama yap
                    link = unique_m3u8s[i] if i < len(unique_m3u8s) else b_target
                    
                    if ".m3u8" not in link:
                        if not b_target.startswith('http'):
                            b_target = urljoin(BASE_URL, b_target)
                        link = get_single_m3u8(scraper, b_target)
                    
                    eps.append({"ad": b_title, "link": link})
            
            # 2. YÖNTEM: Video Kartları (Haber/Spor)
            else:
                video_cards = b_soup.select('.video-item, .grid-item, .col-md-4 a')
                if video_cards:
                     print(f"({len(video_cards)} Video - Alternatif)")
                     for card in video_cards:
                         v_link = card.get('href')
                         v_title = card.get('title') or card.get_text(strip=True)
                         if v_link and "/izle/" in v_link:
                             full_v_link = urljoin(BASE_URL, v_link)
                             link = get_single_m3u8(scraper, full_v_link)
                             eps.append({"ad": v_title, "link": link})
                else:
                    print("(Boş)")

            if eps:
                # Veriyi kaydet
                memory_data[dizi_key] = {
                    "isim": title, 
                    "resim": poster, 
                    "kategori": category,
                    "bolumler": eps
                }

        except Exception as e:
            print(f"⚠️ Hata: {e}")

    if memory_data:
        create_m3u(memory_data)
    else:
        print("❌ M3U oluşturulacak veri yok.")

def create_m3u(data):
    print(f"\n📝 {M3U_FILENAME} dosyası oluşturuluyor...")
    
    with open(M3U_FILENAME, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        # Verileri kategoriye göre gruplayalım ki M3U'da düzenli dursun
        sorted_keys = sorted(data.keys(), key=lambda k: data[k]['kategori'])
        
        for key in sorted_keys:
            item = data[key]
            group = item['kategori']
            poster = item['resim']
            series_name = item['isim']
            
            # Bölümleri tersten sırala (Son bölüm en üstte olsun istersen 'reverse=True' yap)
            # Şu an normal sıralama: 1. Bölüm -> Son Bölüm
            for bolum in item['bolumler']:
                ep_name = bolum['ad']
                link = bolum['link']
                
                # M3U Satırları
                # group-title: Kategori (Örn: NOW DIZILER)
                # tvg-logo: Afiş
                # İsim: Dizi Adı - Bölüm Adı
                f.write(f'#EXTINF:-1 group-title="{group}" tvg-logo="{poster}", {series_name} - {ep_name}\n')
                f.write(f'{link}\n')

    commit_and_push(M3U_FILENAME)

if __name__ == "__main__":
    run_scraper()
