#!/usr/bin/env python3
"""
GALERIE — 명화 이미지 다운로드 스크립트 v2
==========================================
HTML 파일에서 URL을 직접 파싱 → 수동 오탈자 원천 불가능

사용법:
  1. 이 파일과 masterpiece-wallpaper-app.html을 같은 폴더에 저장
  2. python download_artworks.py
  3. images/full/ 와 images/thumb/ 에 저장됨
  4. 실패 항목은 failed_list.txt 저장 → 재실행 시 자동으로 이어서 진행
"""

import os, re, time, sys
import urllib.request
import urllib.error

# ── 설정 ─────────────────────────────────────────────────────────────
HTML_FILE  = "masterpiece-wallpaper-app.html"
OUTPUT_DIR = "images"
FULL_DIR   = os.path.join(OUTPUT_DIR, "full")
THUMB_DIR  = os.path.join(OUTPUT_DIR, "thumb")
DELAY      = 1.2
TIMEOUT    = 30
RETRY      = 2

HEADERS = {
    'User-Agent': 'GALERIE-App/2.0 (bittory.github.io/galerie; educational artwork display)',
    'Accept': 'image/webp,image/jpeg,image/*,*/*',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
}

def parse_artworks_from_html(html_path):
    if not os.path.exists(html_path):
        print(f"ERROR: {html_path} 를 찾을 수 없습니다.")
        print(f"현재 폴더: {os.getcwd()}")
        sys.exit(1)
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r'\{\s*id:(\d+),\s*title:"([^"]+)"[^}]+url:"([^"]+)"[^}]+thumb:"([^"]+)"[^}]*\}'
    matches = re.findall(pattern, content, re.DOTALL)
    artworks = []
    for id_, title, url, thumb in matches:
        if url.startswith('images/') or url.startswith('./images/'):
            continue
        artworks.append({'id': int(id_), 'title': title, 'url': url.strip(), 'thumb': thumb.strip()})
    return artworks

def make_filename(id_, kind):
    return f"{id_:03d}_{kind}.jpg"

def download_image(url, filepath):
    for attempt in range(RETRY + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                ct = resp.headers.get('Content-Type', '')
                if 'text/html' in ct:
                    raise ValueError(f"HTML 응답 (차단됨)")
                data = resp.read()
                if len(data) < 2000:
                    raise ValueError(f"응답 너무 작음 ({len(data)} bytes)")
                with open(filepath, 'wb') as f:
                    f.write(data)
                return True, len(data)
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}: {e.reason}"
            if e.code == 404:
                return False, err
            if attempt < RETRY:
                print(f"    [{attempt+1}/{RETRY}] 재시도...")
                time.sleep(2)
            else:
                return False, err
        except Exception as e:
            err = str(e)[:80]
            if attempt < RETRY:
                print(f"    [{attempt+1}/{RETRY}] 재시도... ({err})")
                time.sleep(2)
            else:
                return False, err
    return False, "최대 재시도 초과"

def main():
    print(f"\n{'='*62}")
    print(f"  GALERIE 이미지 다운로드 v2 (HTML 직접 파싱)")
    print(f"{'='*62}")
    print(f"\n{HTML_FILE} 파싱 중...")
    artworks = parse_artworks_from_html(HTML_FILE)
    total = len(artworks)
    print(f"  다운로드 대상: {total}개 작품\n")
    if total == 0:
        print("다운로드할 항목 없음 (이미 로컬 경로로 교체됨)")
        return
    os.makedirs(FULL_DIR,  exist_ok=True)
    os.makedirs(THUMB_DIR, exist_ok=True)
    print(f"저장 위치: {os.path.abspath(OUTPUT_DIR)}\n")
    success_full = success_thumb = skip_full = skip_thumb = 0
    failed = []
    for i, art in enumerate(artworks, 1):
        id_ = art['id']
        full_path  = os.path.join(FULL_DIR,  make_filename(id_, 'full'))
        thumb_path = os.path.join(THUMB_DIR, make_filename(id_, 'thumb'))
        print(f"[{i:3d}/{total}] {art['title'][:35]}")
        # Full
        if os.path.exists(full_path):
            print(f"  already: full ({os.path.getsize(full_path)//1024}KB)")
            success_full += 1; skip_full += 1
        else:
            ok, info = download_image(art['url'], full_path)
            if ok:
                print(f"  OK full  {info//1024}KB")
                success_full += 1
            else:
                print(f"  FAIL full  {info}")
                failed.append((id_, art['title'], 'full', info, art['url']))
                if os.path.exists(full_path): os.remove(full_path)
        # Thumb
        if os.path.exists(thumb_path):
            print(f"  already: thumb ({os.path.getsize(thumb_path)//1024}KB)")
            success_thumb += 1; skip_thumb += 1
        else:
            time.sleep(0.3)
            ok, info = download_image(art['thumb'], thumb_path)
            if ok:
                print(f"  OK thumb {info//1024}KB")
                success_thumb += 1
            else:
                print(f"  FAIL thumb {info}")
                failed.append((id_, art['title'], 'thumb', info, art['thumb']))
                if os.path.exists(thumb_path): os.remove(thumb_path)
        if i < total:
            time.sleep(DELAY)
    print(f"\n{'='*62}")
    print(f"  full  성공: {success_full}/{total} (신규 {success_full-skip_full}개)")
    print(f"  thumb 성공: {success_thumb}/{total} (신규 {success_thumb-skip_thumb}개)")
    if failed:
        print(f"  실패: {len(failed)}건")
        for id_, title, typ, err, url in failed[:15]:
            print(f"    id:{id_:3d} [{typ}] {title[:25]} -- {err[:45]}")
        with open("failed_list.txt", "w", encoding="utf-8") as f:
            for item in failed:
                f.write(f"{item[0]}\t{item[1]}\t{item[2]}\t{item[3]}\n")
        print(f"\n  failed_list.txt 저장 -- 재실행하면 이어서 진행")
    else:
        print(f"  모든 이미지 다운로드 완료!")
        if os.path.exists("failed_list.txt"): os.remove("failed_list.txt")
        print("\n다음 단계: python replace_urls.py")
    print(f"{'='*62}\n")

if __name__ == "__main__":
    main()
