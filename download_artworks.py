#!/usr/bin/env python3
"""
GALERIE — 명화 이미지 다운로드 스크립트 v4 (API 기반)
======================================================
변경사항:
  - Wikimedia CDN 직접접근(upload.wikimedia.org) 완전 폐기
  - MediaWiki API로 파일명 → 정확한 URL 조회 후 다운로드
  - Met Museum API로 objectID → 정확한 이미지 URL 조회 후 다운로드
  - URL을 추측하거나 수동 입력하지 않음 (오류 원천 차단)

사용법:
  masterpiece-wallpaper-app.html 과 같은 폴더에서:
  python download_artworks.py
"""

import os, re, time, json, random, sys
import urllib.request, urllib.error, urllib.parse

# ── 설정 ─────────────────────────────────────────────────────────────
HTML_FILE  = "masterpiece-wallpaper-app.html"
OUTPUT_DIR = "images"
FULL_DIR   = os.path.join(OUTPUT_DIR, "full")
THUMB_DIR  = os.path.join(OUTPUT_DIR, "thumb")

FULL_WIDTH  = 1280   # full 이미지 최대 너비(px)
THUMB_WIDTH = 400    # thumb 이미지 너비(px)
TIMEOUT     = 40
API_DELAY   = 1.5    # API 호출 간격(초)
IMG_DELAY_MIN = 2.0  # 이미지 다운로드 간격 최소(초)
IMG_DELAY_MAX = 4.0  # 이미지 다운로드 간격 최대(초)
BATCH_SIZE  = 10     # 배치 크기
BATCH_REST  = 25     # 배치 후 휴식(초)

# ── Met Museum 검증된 Object ID 매핑 ─────────────────────────────────
# 공식 Met Collection API (collectionapi.metmuseum.org) 기반
# 형식: art_id → met_object_id
MET_OBJECT_IDS = {
    6:   436532,  # Van Gogh, Self-Portrait with Straw Hat
    14:  437127,  # Monet, La Grenouillère
    97:  39770,   # Qingming scroll (Along the River)
    101: 54941,   # Korean folk painting - magpie tiger
    103: 54943,   # Korean folk painting - tigers under pine
    104: 54942,   # Korean folk painting - magpie tiger 2
    106: 54939,   # Korean folk painting - tiger family
    107: 54940,   # Korean folk painting - tiger worship
    118: 453026,  # Iznik plate
    119: 464380,  # Byzantine icon Virgin and Child
    120: 37781,   # Khmer head of deity
    121: 459095,  # Degas, The Millinery Shop
}

# ── 헤더 설정 ─────────────────────────────────────────────────────────
HEADERS_API = {
    'User-Agent': 'GALERIE-App/4.0 (bittory.github.io/galerie; artwork display app; contact bittory@github)',
    'Accept': 'application/json',
}
HEADERS_IMG = {
    'User-Agent': 'GALERIE-App/4.0 (bittory.github.io/galerie; artwork display app)',
    'Accept': 'image/jpeg,image/png,image/*,*/*',
}

# ── HTML 파싱 ──────────────────────────────────────────────────────────
def parse_artworks(html_path):
    if not os.path.exists(html_path):
        print(f"ERROR: {html_path} 없음. 현재 폴더: {os.getcwd()}")
        sys.exit(1)
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r'\{\s*id:(\d+),\s*title:"([^"]+)"[^}]+artist:"([^"]+)"[^}]+url:"([^"]+)"[^}]+thumb:"([^"]+)"'
    artworks = []
    for id_, title, artist, url, thumb in re.findall(pattern, content, re.DOTALL):
        u = url.strip()
        if u.startswith('images/') or u.startswith('./images/'):
            continue  # 이미 로컬 경로로 교체된 항목 스킵
        artworks.append({
            'id': int(id_), 'title': title, 'artist': artist,
            'url': u, 'thumb': thumb.strip()
        })
    return artworks

# ── Wikimedia 파일명 추출 ──────────────────────────────────────────────
def extract_wiki_filename(url):
    """Wikimedia CDN URL에서 파일명 추출"""
    # thumb 경로: /commons/thumb/a/ab/FILENAME.jpg/1280px-FILENAME.jpg
    # 원본 경로: /commons/a/ab/FILENAME.jpg
    m = re.search(
        r'/commons/(?:thumb/)?[a-f0-9]/[a-f0-9]{2}/([^/]+\.(?:jpg|jpeg|png|JPG|PNG))',
        url, re.IGNORECASE
    )
    return urllib.parse.unquote(m.group(1)) if m else None

# ── Wikimedia API로 이미지 URL 조회 ────────────────────────────────────
def get_wikimedia_url(filename, width):
    """
    MediaWiki API (공식 승인 방법)로 정확한 이미지 URL 조회
    https://www.mediawiki.org/wiki/API:Imageinfo
    """
    api_url = (
        "https://commons.wikimedia.org/w/api.php"
        f"?action=query"
        f"&titles=File:{urllib.parse.quote(filename)}"
        f"&prop=imageinfo"
        f"&iiprop=url"
        f"&iiurlwidth={width}"
        f"&format=json"
        f"&origin=*"
    )
    try:
        req = urllib.request.Request(api_url, headers=HEADERS_API)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            ii = page.get('imageinfo', [])
            if ii:
                url = ii[0].get('thumburl') or ii[0].get('url')
                if url:
                    return url, None
        return None, "API 응답에 URL 없음"
    except urllib.error.HTTPError as e:
        return None, f"API HTTP {e.code}"
    except Exception as e:
        return None, str(e)[:60]

# ── Met Museum API로 이미지 URL 조회 ────────────────────────────────────
def get_met_url(object_id):
    """
    Met Museum Open Access API (공식)로 이미지 URL 조회
    https://metmuseum.github.io/
    """
    api_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}"
    try:
        req = urllib.request.Request(api_url, headers=HEADERS_API)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        full  = data.get('primaryImage', '')
        thumb = data.get('primaryImageSmall', '')
        if not full:
            return None, None, "primaryImage 없음"
        return full, thumb or full, None
    except urllib.error.HTTPError as e:
        return None, None, f"API HTTP {e.code}"
    except Exception as e:
        return None, None, str(e)[:60]

# ── 이미지 다운로드 ────────────────────────────────────────────────────
def download(url, filepath):
    try:
        req = urllib.request.Request(url, headers=HEADERS_IMG)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            ct = resp.headers.get('Content-Type', '')
            if 'text/html' in ct:
                return False, "HTML 응답 (차단)"
            data = resp.read()
            if len(data) < 2000:
                return False, f"응답 너무 작음 ({len(data)}B)"
            with open(filepath, 'wb') as f:
                f.write(data)
            return True, len(data)
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)[:60]

# ── 메인 ──────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*64}")
    print(f"  GALERIE 이미지 다운로드 v4 — API 기반 (URL 추측 없음)")
    print(f"  Wikimedia: MediaWiki API | Met Museum: Collection API")
    print(f"{'='*64}")

    artworks = parse_artworks(HTML_FILE)
    total = len(artworks)
    if total == 0:
        print("\n  다운로드할 항목 없음 (이미 로컬 경로 적용됨)")
        return
    print(f"\n  대상: {total}개 작품\n")

    os.makedirs(FULL_DIR,  exist_ok=True)
    os.makedirs(THUMB_DIR, exist_ok=True)

    ok_full = ok_thumb = skip_f = skip_t = 0
    failed = []
    batch = 0

    for i, art in enumerate(artworks, 1):
        id_    = art['id']
        title  = art['title']
        fp     = os.path.join(FULL_DIR,  f"{id_:03d}_full.jpg")
        tp     = os.path.join(THUMB_DIR, f"{id_:03d}_thumb.jpg")
        is_met = 'metmuseum' in art['url']
        src    = "MET" if is_met else "WMD"

        print(f"[{i:3d}/{total}] [{src}] {title[:34]}")

        need_full  = not (os.path.exists(fp) and os.path.getsize(fp) > 2000)
        need_thumb = not (os.path.exists(tp) and os.path.getsize(tp) > 2000)

        if not need_full:
            print(f"  ✓ full  ({os.path.getsize(fp)//1024}KB 기존)")
            ok_full += 1; skip_f += 1
        if not need_thumb:
            print(f"  ✓ thumb ({os.path.getsize(tp)//1024}KB 기존)")
            ok_thumb += 1; skip_t += 1

        if not need_full and not need_thumb:
            continue

        # ── URL 조회 ──
        full_url = thumb_url = None

        if is_met:
            # Met Museum 공식 API
            obj_id = MET_OBJECT_IDS.get(id_)
            if obj_id:
                full_url, thumb_url, err = get_met_url(obj_id)
                if err:
                    print(f"  ⚠ Met API 오류 (objectID:{obj_id}): {err}")
                else:
                    print(f"  🔍 Met API → objectID:{obj_id}")
            else:
                print(f"  ⚠ Met objectID 미등록 (id:{id_})")
                failed.append((id_, title, 'full+thumb', 'Met objectID 미등록'))
                continue
        else:
            # Wikimedia MediaWiki API
            filename = extract_wiki_filename(art['url'])
            if not filename:
                print(f"  ⚠ 파일명 추출 실패: {art['url'][-50:]}")
                failed.append((id_, title, 'full+thumb', '파일명 추출 실패'))
                continue

            print(f"  🔍 Wiki API → {filename[:50]}")
            time.sleep(API_DELAY)

            if need_full:
                full_url, err = get_wikimedia_url(filename, FULL_WIDTH)
                if err:
                    print(f"  ⚠ API 오류(full): {err}")

            if need_thumb:
                thumb_url, err = get_wikimedia_url(filename, THUMB_WIDTH)
                if err:
                    print(f"  ⚠ API 오류(thumb): {err}")

        # ── 다운로드 ──
        if need_full:
            if full_url:
                ok, info = download(full_url, fp)
                if ok:
                    print(f"  ✅ full  {info//1024}KB")
                    ok_full += 1
                else:
                    print(f"  ❌ full  {info}")
                    failed.append((id_, title, 'full', info))
                    if os.path.exists(fp): os.remove(fp)
                time.sleep(random.uniform(IMG_DELAY_MIN, IMG_DELAY_MAX))
            else:
                failed.append((id_, title, 'full', 'API URL 없음'))

        if need_thumb:
            if thumb_url:
                ok, info = download(thumb_url, tp)
                if ok:
                    print(f"  ✅ thumb {info//1024}KB")
                    ok_thumb += 1
                else:
                    print(f"  ❌ thumb {info}")
                    failed.append((id_, title, 'thumb', info))
                    if os.path.exists(tp): os.remove(tp)
                time.sleep(random.uniform(IMG_DELAY_MIN, IMG_DELAY_MAX))
            else:
                failed.append((id_, title, 'thumb', 'API URL 없음'))

        # 배치 휴식
        batch += 1
        if batch >= BATCH_SIZE and i < total:
            print(f"\n  ⏸  배치 휴식 {BATCH_REST}초...\n")
            time.sleep(BATCH_REST)
            batch = 0

    # ── 결과 ──
    print(f"\n{'='*64}")
    print(f"  full  완료: {ok_full}/{total}  (신규 {ok_full-skip_f}, 기존 {skip_f})")
    print(f"  thumb 완료: {ok_thumb}/{total}  (신규 {ok_thumb-skip_t}, 기존 {skip_t})")

    if failed:
        print(f"\n  ❌ 실패: {len(failed)}건")
        for id_, title, typ, err in failed[:15]:
            print(f"     id:{id_:3d} [{typ}] {title[:24]} — {err[:40]}")
        with open("failed_list.txt", "w", encoding="utf-8") as f:
            for row in failed:
                f.write('\t'.join(str(x) for x in row) + '\n')
        print(f"\n  재실행하면 기존 파일은 건너뛰고 실패분만 재시도합니다.")
    else:
        print(f"\n  🎉 전체 완료! 다음: python replace_urls.py")
        if os.path.exists("failed_list.txt"): os.remove("failed_list.txt")

    print(f"{'='*64}\n")

if __name__ == "__main__":
    main()
