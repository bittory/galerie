#!/usr/bin/env python3
"""
GALERIE — 명화 이미지 다운로드 스크립트 v3
==========================================
- HTML 파일에서 URL 직접 파싱 (오탈자 원천 불가)
- Wikimedia 429 차단 대응: Referer 헤더 + 배치 대기 + 자동 재시도
- 이어서 다운로드 지원 (재실행 시 기존 파일 건너뜀)

사용법:
  masterpiece-wallpaper-app.html 과 같은 폴더에서:
  python download_artworks.py
"""

import os, re, time, sys, random
import urllib.request, urllib.error

# ── 설정 ─────────────────────────────────────────────────────────────
HTML_FILE   = "masterpiece-wallpaper-app.html"
OUTPUT_DIR  = "images"
FULL_DIR    = os.path.join(OUTPUT_DIR, "full")
THUMB_DIR   = os.path.join(OUTPUT_DIR, "thumb")

DELAY_MIN   = 3.0    # 요청 간 최소 딜레이(초)
DELAY_MAX   = 5.5    # 요청 간 최대 딜레이(초)
TIMEOUT     = 40     # 다운로드 타임아웃(초)
RETRY       = 3      # 실패 시 재시도 횟수
BATCH_SIZE  = 8      # 배치 크기 (N개마다 휴식)
BATCH_REST  = 20     # 배치 후 휴식(초)
BLOCK_WAIT  = 90     # 429 차단 시 대기(초)

# Wikimedia 차단 방지 핵심: 브라우저처럼 보이는 헤더
HEADERS_WIKIMEDIA = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'image',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'cross-site',
}

# Met Museum: 봇 차단 없음 → 간단한 헤더
HEADERS_MET = {
    'User-Agent': 'GALERIE-App/3.0 (bittory.github.io/galerie)',
    'Accept': 'image/jpeg,image/*,*/*',
}

def get_referer(url):
    """URL에서 Wikimedia Commons 페이지 Referer 생성"""
    m = re.search(r'/commons/(?:thumb/)?([a-f0-9]/[a-f0-9]{2})/([^/]+)(?:/[^/]+)?$', url)
    if m:
        filename = m.group(2)
        return f"https://commons.wikimedia.org/wiki/File:{filename}"
    return "https://commons.wikimedia.org/"

def get_headers(url):
    if 'metmuseum.org' in url:
        return HEADERS_MET
    headers = dict(HEADERS_WIKIMEDIA)
    headers['Referer'] = get_referer(url)
    return headers

def parse_artworks(html_path):
    if not os.path.exists(html_path):
        print(f"❌ {html_path} 없음. 현재 폴더: {os.getcwd()}")
        sys.exit(1)
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r'\{\s*id:(\d+),\s*title:"([^"]+)"[^}]+url:"([^"]+)"[^}]+thumb:"([^"]+)"[^}]*\}'
    artworks = []
    for id_, title, url, thumb in re.findall(pattern, content, re.DOTALL):
        u, t = url.strip(), thumb.strip()
        if u.startswith('images/') or u.startswith('./images/'):
            continue
        artworks.append({'id': int(id_), 'title': title, 'url': u, 'thumb': t})
    return artworks

def download_image(url, filepath, retry=RETRY):
    headers = get_headers(url)
    for attempt in range(retry + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                ct = resp.headers.get('Content-Type', '')
                if 'text/html' in ct:
                    raise ValueError("HTML 응답 (차단)")
                data = resp.read()
                if len(data) < 2000:
                    raise ValueError(f"응답 너무 작음 {len(data)}B")
                with open(filepath, 'wb') as f:
                    f.write(data)
                return 'ok', len(data)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return '429', str(e)
            if e.code == 404:
                return '404', f"HTTP 404: Not Found"
            if attempt < retry:
                wait = 3 + attempt * 2
                print(f"      HTTP {e.code} → {wait}s 후 재시도...")
                time.sleep(wait)
            else:
                return 'err', f"HTTP {e.code}: {e.reason}"
        except Exception as e:
            err = str(e)[:60]
            if attempt < retry:
                time.sleep(2)
            else:
                return 'err', err
    return 'err', "최대 재시도 초과"

def main():
    print(f"\n{'='*64}")
    print(f"  GALERIE 이미지 다운로드 v3")
    print(f"  Wikimedia 429 대응: Referer + 딜레이 {DELAY_MIN}~{DELAY_MAX}초 + 배치 휴식")
    print(f"{'='*64}")

    print(f"\n📖 {HTML_FILE} 파싱 중...")
    artworks = parse_artworks(HTML_FILE)
    total = len(artworks)
    if total == 0:
        print("  다운로드할 항목 없음 (이미 로컬 경로 적용됨)")
        return
    print(f"  대상: {total}개\n")

    os.makedirs(FULL_DIR, exist_ok=True)
    os.makedirs(THUMB_DIR, exist_ok=True)

    ok_full = ok_thumb = skip_full = skip_thumb = 0
    failed = []
    batch_count = 0

    for i, art in enumerate(artworks, 1):
        id_, title = art['id'], art['title']
        fp = os.path.join(FULL_DIR,  f"{id_:03d}_full.jpg")
        tp = os.path.join(THUMB_DIR, f"{id_:03d}_thumb.jpg")
        src = "MET" if 'metmuseum.org' in art['url'] else "WMD"

        print(f"[{i:3d}/{total}] [{src}] {title[:32]}")

        # ── Full ──
        if os.path.exists(fp) and os.path.getsize(fp) > 2000:
            print(f"  ✓ full  ({os.path.getsize(fp)//1024}KB 기존)")
            ok_full += 1; skip_full += 1
        else:
            status, info = download_image(art['url'], fp)
            if status == 'ok':
                print(f"  ✅ full  {info//1024}KB")
                ok_full += 1
            elif status == '429':
                print(f"  🚫 429 차단 — {BLOCK_WAIT}초 대기 후 재시도...")
                if os.path.exists(fp): os.remove(fp)
                time.sleep(BLOCK_WAIT)
                status2, info2 = download_image(art['url'], fp)
                if status2 == 'ok':
                    print(f"  ✅ full  재시도 성공 {info2//1024}KB")
                    ok_full += 1
                else:
                    print(f"  ❌ full  재시도 실패: {info2}")
                    failed.append((id_, title, 'full', info2))
                    if os.path.exists(fp): os.remove(fp)
            else:
                print(f"  ❌ full  {info}")
                failed.append((id_, title, 'full', info))
                if os.path.exists(fp): os.remove(fp)

        # ── Thumb ──
        time.sleep(random.uniform(0.8, 1.5))

        if os.path.exists(tp) and os.path.getsize(tp) > 2000:
            print(f"  ✓ thumb ({os.path.getsize(tp)//1024}KB 기존)")
            ok_thumb += 1; skip_thumb += 1
        else:
            status, info = download_image(art['thumb'], tp)
            if status == 'ok':
                print(f"  ✅ thumb {info//1024}KB")
                ok_thumb += 1
            elif status == '429':
                print(f"  🚫 429 차단 — {BLOCK_WAIT}초 대기 후 재시도...")
                if os.path.exists(tp): os.remove(tp)
                time.sleep(BLOCK_WAIT)
                status2, info2 = download_image(art['thumb'], tp)
                if status2 == 'ok':
                    print(f"  ✅ thumb 재시도 성공 {info2//1024}KB")
                    ok_thumb += 1
                else:
                    print(f"  ❌ thumb 재시도 실패: {info2}")
                    failed.append((id_, title, 'thumb', info2))
                    if os.path.exists(tp): os.remove(tp)
            else:
                print(f"  ❌ thumb {info}")
                failed.append((id_, title, 'thumb', info))
                if os.path.exists(tp): os.remove(tp)

        # ── 배치 휴식 ──
        batch_count += 1
        if i < total:
            if batch_count >= BATCH_SIZE:
                print(f"\n  ⏸  {BATCH_REST}초 배치 휴식 중...\n")
                time.sleep(BATCH_REST)
                batch_count = 0
            else:
                delay = random.uniform(DELAY_MIN, DELAY_MAX)
                time.sleep(delay)

    # ── 결과 ──
    print(f"\n{'='*64}")
    print(f"  full  완료: {ok_full}/{total}  (신규 {ok_full-skip_full}, 기존 {skip_full})")
    print(f"  thumb 완료: {ok_thumb}/{total}  (신규 {ok_thumb-skip_thumb}, 기존 {skip_thumb})")

    if failed:
        print(f"\n  ❌ 실패 {len(failed)}건:")
        for id_, title, typ, err in failed:
            print(f"     id:{id_:3d} [{typ}] {title[:24]} — {err[:40]}")
        with open("failed_list.txt", "w", encoding="utf-8") as f:
            for id_, title, typ, err in failed:
                f.write(f"{id_}\t{title}\t{typ}\t{err}\n")
        print(f"\n  failed_list.txt 저장 → 재실행하면 이어서 진행")
    else:
        print(f"\n  🎉 전체 완료!")
        if os.path.exists("failed_list.txt"):
            os.remove("failed_list.txt")
        print("  다음: python replace_urls.py")

    print(f"{'='*64}\n")

if __name__ == "__main__":
    main()
