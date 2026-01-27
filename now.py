import cloudscraper
from bs4 import BeautifulSoup
import time
import re
import subprocess
from urllib.parse import urljoin

# --- AYARLAR ---
BASE_URL = "https://www.nowtv.com.tr"
M3U_FILENAME = "nowtv.m3u"

# KATEGORİ HARİTASI
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
        else:
            print("⚠️ Değişiklik yok, push atlanıyor.")
    except Exception as e:
        print(f"❌ Git Hatası: {e}")

def collect_dynamic_series(scraper):
    """
    Kategorileri tarar ve içerikleri kategorisine göre etiketleyerek listeler.
    YENİ YÖNTEM: Class bağımsız, direkt link analizi.
    """
    dynamic_data = {}
    print("🌍 Kategori sayfaları taranıyor...")

    for cat in CATEGORY_MAP:
        url = cat["url"]
        cat_name = cat["name"]
        print(f"   📂 Kategori Taranıyor: {cat_name} ({url})")
        
        try:
            resp = scraper.get(url, timeout=15)
            # Sayfa gerçekten yüklendi mi kontrol et
            if resp.status_code != 200:
                print(f"      ❌ Hata: Sayfa yüklenemedi (Kod: {resp.status_code})")
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Sayfa başlığını yazdır (Cloudflare engeli var mı anlamak için)
            page_title = soup.title.string.strip() if soup.title else "Başlık Yok"
            # print(f"      ℹ️ Sayfa Başlığı: {page_title}") 

            # YENİ YÖNTEM: Tüm 'a' etiketlerini bul ve link yapılarına göre filtrele
            all_links = soup.find_all('a', href=True)
            
            count_in_cat = 0
            for link_tag in all_links:
                href = link_tag['href']
                full_link = urljoin(BASE_URL, href)
                
                # Gereksiz linkleri ele (iletişim, künye, kategori ana linkleri vb.)
                if any(x in href for x in ['/iletisim', '/kunye', '/yayin-akisi', 'facebook', 'twitter', 'instagram']):
                    continue
                if full_link.rstrip('/') == url.rstrip('/'): # Kendi linkini alma
                    continue

                # Sadece hedef yapıya uyan linkleri al
                # Örn: /dizi/kizil-goncalar, /program/cagla-ile-yeni-bir-gun
                is_valid_content = False
                if '/dizi/' in href and '/dizi-izle' not in href and '/dizi-arsivi' not in href:
                    is_valid_content = True
                elif '/program/' in href and '/program-izle' not in href and '/program-arsivi' not in href:
                    is_valid_content = True
                elif '/now-haber' in href or '/now-spor' in href:
                    # Haber ve Spor linkleri genelde ana kategori linkiyle aynı olabiliyor, alt içerikleri ayır
                    if len(href.split('/')) > 2: 
                        is_valid_content = True

                if not is_valid_content:
                    continue

                try:
                    # İsim Çıkarma (Title > Alt Text > Link Sonu)
                    title = ""
                    img_tag = link_tag.find('img')
                    
                    if link_tag.get('title'):
                        title = link_tag.get('title').strip()
                    elif img_tag and img_tag.get('alt'):
                        title = img_tag.get('alt').strip()
                    elif link_tag.find('span', class_='title'): # Yedek class kontrolü
                        title = link_tag.find('span', class_='title').get_text(strip=True)
                    else:
                        # Linkten isim üret: /dizi/yabani -> Yabani
                        title = href.strip('/').split('/')[-1].replace('-', ' ').title()

                    # Resim Çıkarma
                    img_url = ""
                    if img_tag:
                        img_url = img_tag.get('data-src') or img_tag.get('src')
                        if img_url and not img_url.startswith('http'):
                            img_url = urljoin(BASE_URL, img_url)
                    
                    # Eğer resim yoksa varsayılan bir logo koyalım
                    if not img_url:
                        img_url = "https://img-nowtv.mncdn.com/assets/images/nowtv-logo-share.jpg"

                    # ID (Key) oluşturma
                    dizi_key = href.strip('/').split('/')[-1]

                    # Mükerrer kayıt önleme
                    if dizi_key not in dynamic_data:
                        dynamic_data[dizi_key] = {
                            "isim": title,
                            "link": full_link,
                            "resim": img_url,
                            "kategori": cat_name
                        }
                        count_in_cat += 1
                except:
                    continue
            
            print(f"      ✅ Bu kategoriden {count_in_cat} içerik eklendi.")

        except Exception as e:
            print(f"   ⚠️ Hata ({url}): {e}")
    
    print(f"\n🌍 Toplam {len(dynamic_data)} farklı içerik bulundu.\n")
    return dynamic_data

def run_scraper():
    print("🚀 Bot Başlatıldı. M3U Modu Aktif...")
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    
    target_series = collect_dynamic_series(scraper)
    
    if not target_series:
        print("❌ Hiçbir içerik bulunamadı! Site yapısı değişmiş veya IP engelli olabilir.")
        # Dosya boş olsa bile eskiyi silmek için commit atabiliriz ama şimdilik durduralım.
        return

    memory_data = {}

    for dizi_key, info in target_series.items():
        title = info.get('isim', 'Dizi')
        dizi_url = info.get('link', '')
        poster = info.get('resim', '')
        category = info.get('kategori', 'GENEL')
        
        # Link Düzenleme: Haber/Spor için direkt link, diziler için /bolumler
        base_series_url = dizi_url.split('/izle')[0].rstrip('/')
        
        # Haber ve Spor sayfalarında yapı farklı olabiliyor, direkt tarayalım
        if "now-haber" in base_series_url or "now-spor" in base_series_url:
            bolumler_url = base_series_url 
        else:
            bolumler_url = base_series_url + "/bolumler"

        print(f"🔍 [{category}] {title} işleniyor...", end=" ", flush=True)
        
        try:
            response = scraper.get(bolumler_url, timeout=10)
            
            # 1. Aşama: Sayfa içindeki tüm .m3u8 linklerini topla (Hızlı Yöntem)
            found_m3u8s = re.findall(r'https?://[^\s"\'\\,]+\.m3u8[^\s"\'\\,]*', response.text)
            found_m3u8s = [m.replace('\\/', '/') for m in found_m3u8s]
            unique_m3u8s = list(dict.fromkeys(found_m3u8s))

            b_soup = BeautifulSoup(response.text, 'html.parser')
            eps = []
            
            select_box = b_soup.find('select', id='video-finder-changer')
            
            # --- SENARYO A: Select Box Var (Standart Dizi Sayfası) ---
            if select_box:
                options = select_box.find_all('option', {'data-target': True})
                print(f"({len(options)} Bölüm)")
                
                for i, opt in enumerate(options):
                    b_title = opt.get_text(strip=True)
                    b_target = opt['data-target']
                    
                    # Elimizdeki hazır m3u8 listesinden eşleştirmeye çalış
                    link = unique_m3u8s[i] if i < len(unique_m3u8s) else b_target
                    
                    # Eğer link bir sayfa linkiyse (m3u8 değilse), içine girip al (Deep Scan)
                    if ".m3u8" not in link:
                        if not b_target.startswith('http'):
                            b_target = urljoin(BASE_URL, b_target)
                        # Çok yavaşlamaması için sadece ilk ve son bölümlerde deep scan yapabilirsin
                        # Ama tam liste için mecbur hepsine bakacağız:
                        link = get_single_m3u8(scraper, b_target)
                    
                    eps.append({"ad": b_title, "link": link})
            
            # --- SENARYO B: Select Box Yok (Video Kartları / Haber / Spor) ---
            else:
                # Video kartlarını bul (Geniş selector)
                video_cards = b_soup.select('.video-item, .grid-item, .col-md-4 a, .card-video a')
                
                # Eğer direkt video kartı bulamadıysa, sayfadaki tüm 'izle' linklerine bak
                if not video_cards:
                     all_links = b_soup.find_all('a', href=True)
                     video_cards = [l for l in all_links if '/izle/' in l['href']]

                if video_cards:
                     print(f"({len(video_cards)} Video - Alternatif)")
                     count = 0
                     for card in video_cards:
                         if count >= 20: break # Çok fazla video varsa limitle (haberler vb.)
                         
                         v_link = card.get('href')
                         # Başlık bulma çabası
                         v_title = card.get('title') 
                         if not v_title: 
                             v_title = card.find('img')['alt'] if card.find('img') else card.get_text(strip=True)
                         if not v_title:
                             v_title = "Video"

                         if v_link and "/izle/" in v_link:
                             full_v_link = urljoin(BASE_URL, v_link)
                             # Link ana dizi linkiyle aynıysa atla
                             if full_v_link.rstrip('/') == base_series_url.rstrip('/'): continue

                             link = get_single_m3u8(scraper, full_v_link)
                             eps.append({"ad": v_title, "link": link})
                             count += 1
                else:
                    print("(Bölüm bulunamadı)")

            if eps:
                memory_data[dizi_key] = {
                    "isim": title, 
                    "resim": poster, 
                    "kategori": category,
                    "bolumler": eps
                }
            else:
                # Bölüm bulamasa bile 'Canlı Yayın' veya tekil içerik olabilir mi?
                # Şimdilik boş geçiyoruz.
                pass

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
        
        # Kategorilere göre sırala
        sorted_keys = sorted(data.keys(), key=lambda k: data[k]['kategori'])
        
        for key in sorted_keys:
            item = data[key]
            group = item['kategori']
            poster = item['resim']
            series_name = item['isim']
            
            for bolum in item['bolumler']:
                ep_name = bolum['ad']
                link = bolum['link']
                
                # M3U Satır Formatı
                f.write(f'#EXTINF:-1 group-title="{group}" tvg-logo="{poster}", {series_name} - {ep_name}\n')
                f.write(f'{link}\n')

    commit_and_push(M3U_FILENAME)

if __name__ == "__main__":
    run_scraper()
