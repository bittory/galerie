#!/usr/bin/env python3
"""
GALERIE — HTML URL 로컬 경로 교체 스크립트
==========================================
download_artworks.py 실행 완료 후 이 스크립트 실행

실행: python replace_urls.py
결과: masterpiece-wallpaper-app.html 의 외부 URL → images/full/, images/thumb/ 로 교체
"""

import os, re, shutil

HTML_IN  = "www/index.html"          # 원본
HTML_OUT = "www/index.html"          # 덮어쓰기 (백업 자동 생성)
HTML_BAK = "www/index.html.bak"
FULL_DIR  = "www/images/full"
THUMB_DIR = "www/images/thumb"

def main():
    if not os.path.exists(HTML_IN):
        print(f"❌ {HTML_IN} 파일이 없습니다.")
        return

    # 백업 생성
    shutil.copy2(HTML_IN, HTML_BAK)
    print(f"✅ 백업 생성: {HTML_BAK}")

    with open(HTML_IN, 'r', encoding='utf-8') as f:
        content = f.read()

    # id별 로컬 파일 존재 확인
    full_files  = {}
    thumb_files = {}

    if os.path.exists(FULL_DIR):
        for fname in os.listdir(FULL_DIR):
            m = re.match(r'^(\d+)_full\.jpg$', fname)
            if m:
                full_files[int(m.group(1))] = f"images/full/{fname}"

    if os.path.exists(THUMB_DIR):
        for fname in os.listdir(THUMB_DIR):
            m = re.match(r'^(\d+)_thumb\.jpg$', fname)
            if m:
                thumb_files[int(m.group(1))] = f"images/thumb/{fname}"

    print(f"\nfull 이미지:  {len(full_files)}개 발견")
    print(f"thumb 이미지: {len(thumb_files)}개 발견")

    # 작품 블록 파싱 및 URL 교체
    replaced_full  = 0
    replaced_thumb = 0
    skipped = []

    def replace_artwork_urls(match):
        nonlocal replaced_full, replaced_thumb
        block = match.group(0)

        # id 추출
        id_m = re.search(r'\{ id:(\d+),', block)
        if not id_m:
            return block

        art_id = int(id_m.group(1))

        # url 교체
        if art_id in full_files:
            block = re.sub(
                r'url:"https://[^"]+"',
                f'url:"{full_files[art_id]}"',
                block, count=1
            )
            replaced_full += 1
        else:
            skipped.append((art_id, 'full'))

        # thumb 교체
        if art_id in thumb_files:
            block = re.sub(
                r'thumb:"https://[^"]+"',
                f'thumb:"{thumb_files[art_id]}"',
                block, count=1
            )
            replaced_thumb += 1
        else:
            skipped.append((art_id, 'thumb'))

        return block

    # 작품 블록 전체 교체
    new_content = re.sub(
        r'\{ id:\d+,.*?\}(?=\s*,?\s*(?://|$|\n\s*\{|\n\s*\]))',
        replace_artwork_urls,
        content,
        flags=re.DOTALL
    )

    with open(HTML_OUT, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"\n✅ URL 교체 완료:")
    print(f"  full  교체: {replaced_full}개")
    print(f"  thumb 교체: {replaced_thumb}개")

    if skipped:
        print(f"\n⚠ 로컬 파일 없어 교체 안 된 항목 ({len(skipped)}개):")
        for art_id, typ in skipped[:10]:
            print(f"  id:{art_id} [{typ}]")
        if len(skipped) > 10:
            print(f"  ... 외 {len(skipped)-10}개")

    print(f"\n저장 완료: {HTML_OUT}")
    print("복원 필요 시: cp www/index.html.bak www/index.html")

if __name__ == "__main__":
    main()
