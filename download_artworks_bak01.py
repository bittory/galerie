#!/usr/bin/env python3
"""
GALERIE — 명화 이미지 일괄 다운로드 스크립트
=============================================
실행: python download_artworks.py
결과: images/full/ 와 images/thumb/ 폴더에 저장
"""

import os, re, time, sys
import urllib.request
import urllib.error

# ── 설정 ─────────────────────────────────────────────────────────────
OUTPUT_DIR   = "images"
FULL_DIR     = os.path.join(OUTPUT_DIR, "full")
THUMB_DIR    = os.path.join(OUTPUT_DIR, "thumb")
DELAY        = 1.0   # 요청 사이 딜레이 (초) — 서버 부하 방지
TIMEOUT      = 30    # 다운로드 타임아웃 (초)
RETRY        = 2     # 실패 시 재시도 횟수

# HTTP 헤더 — Wikimedia Hotlink 차단 우회
HEADERS = {
    'User-Agent': 'GALERIE-App/1.0 (https://bittory.github.io/galerie/; educational/non-commercial)',
    'Referer': '',   # no-referrer
}

# ── 전체 작품 데이터 ──────────────────────────────────────────────────
# 형식: (id, title, full_url, thumb_url, category, source)
ARTWORKS = [
    # ── 반 고흐 ──────────────────────────────────────────────────────
    (1,  "별이 빛나는 밤",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/1280px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/400px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
     "인상주의", "Wikimedia PD"),
    (2,  "해바라기",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Vincent_van_Gogh_-_Sunflowers_-_VGM_F458.jpg/1280px-Vincent_van_Gogh_-_Sunflowers_-_VGM_F458.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Vincent_van_Gogh_-_Sunflowers_-_VGM_F458.jpg/400px-Vincent_van_Gogh_-_Sunflowers_-_VGM_F458.jpg",
     "인상주의", "Wikimedia PD"),
    (3,  "론 강의 별밤",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Starry_Night_Over_the_Rhone.jpg/1280px-Starry_Night_Over_the_Rhone.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Starry_Night_Over_the_Rhone.jpg/400px-Starry_Night_Over_the_Rhone.jpg",
     "인상주의", "Wikimedia PD"),
    (4,  "아를의 침실",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Van_Gogh_-_Bedroom_in_Arles_-_Letter_Sketch_October_1888.jpg/1280px-Van_Gogh_-_Bedroom_in_Arles_-_Letter_Sketch_October_1888.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Van_Gogh_-_Bedroom_in_Arles_-_Letter_Sketch_October_1888.jpg/400px-Van_Gogh_-_Bedroom_in_Arles_-_Letter_Sketch_October_1888.jpg",
     "인상주의", "Wikimedia PD"),
    (5,  "아이리스",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Irises-Vincent_van_Gogh.jpg/1280px-Irises-Vincent_van_Gogh.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Irises-Vincent_van_Gogh.jpg/400px-Irises-Vincent_van_Gogh.jpg",
     "인상주의", "Wikimedia PD"),
    (6,  "밀짚모자를 쓴 자화상",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Self-portrait_with_Straw_Hat_-_Metropolitan_Museum_of_Art.jpg/1280px-Self-portrait_with_Straw_Hat_-_Metropolitan_Museum_of_Art.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Self-portrait_with_Straw_Hat_-_Metropolitan_Museum_of_Art.jpg/400px-Self-portrait_with_Straw_Hat_-_Metropolitan_Museum_of_Art.jpg",
     "인상주의", "Wikimedia PD"),
    (7,  "씨 뿌리는 사람",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Van_Gogh_-_Der_S%C3%A4mann.jpeg/1280px-Van_Gogh_-_Der_S%C3%A4mann.jpeg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Van_Gogh_-_Der_S%C3%A4mann.jpeg/400px-Van_Gogh_-_Der_S%C3%A4mann.jpeg",
     "인상주의", "Wikimedia PD"),
    (8,  "밤의 카페",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Van_Gogh_-_The_Night_Cafe_-_Yale_University_Art_Gallery.jpg/1280px-Van_Gogh_-_The_Night_Cafe_-_Yale_University_Art_Gallery.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Van_Gogh_-_The_Night_Cafe_-_Yale_University_Art_Gallery.jpg/400px-Van_Gogh_-_The_Night_Cafe_-_Yale_University_Art_Gallery.jpg",
     "인상주의", "Wikimedia PD"),
    # ── 모네 ────────────────────────────────────────────────────────
    (9,  "수련",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Claude_Monet_-_Water_Lilies_-_1906%2C_Ryerson.jpg/1280px-Claude_Monet_-_Water_Lilies_-_1906%2C_Ryerson.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Claude_Monet_-_Water_Lilies_-_1906%2C_Ryerson.jpg/400px-Claude_Monet_-_Water_Lilies_-_1906%2C_Ryerson.jpg",
     "인상주의", "Wikimedia PD"),
    (10, "인상, 해돋이",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Monet_-_Impression%2C_Sunrise.jpg/1280px-Monet_-_Impression%2C_Sunrise.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Monet_-_Impression%2C_Sunrise.jpg/400px-Monet_-_Impression%2C_Sunrise.jpg",
     "인상주의", "Wikimedia PD"),
    (11, "루앙 대성당",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Claude_Monet_-_Rouen_Cathedral%2C_Facade_and_Tour_d%27Albane_%28Morning_Effect%29.jpg/800px-Claude_Monet_-_Rouen_Cathedral%2C_Facade_and_Tour_d%27Albane_%28Morning_Effect%29.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Claude_Monet_-_Rouen_Cathedral%2C_Facade_and_Tour_d%27Albane_%28Morning_Effect%29.jpg/400px-Claude_Monet_-_Rouen_Cathedral%2C_Facade_and_Tour_d%27Albane_%28Morning_Effect%29.jpg",
     "인상주의", "Wikimedia PD"),
    (12, "건초더미",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Claude_Monet%2C_Meules%2C_1890%2C_Museum_of_Fine_Arts%2C_Boston.jpg/1280px-Claude_Monet%2C_Meules%2C_1890%2C_Museum_of_Fine_Arts%2C_Boston.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Claude_Monet%2C_Meules%2C_1890%2C_Museum_of_Fine_Arts%2C_Boston.jpg/400px-Claude_Monet%2C_Meules%2C_1890%2C_Museum_of_Fine_Arts%2C_Boston.jpg",
     "인상주의", "Wikimedia PD"),
    (13, "일본풍 다리",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Claude_Monet_-_The_Japanese_Footbridge_-_Google_Art_Project.jpg/1280px-Claude_Monet_-_The_Japanese_Footbridge_-_Google_Art_Project.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Claude_Monet_-_The_Japanese_Footbridge_-_Google_Art_Project.jpg/400px-Claude_Monet_-_The_Japanese_Footbridge_-_Google_Art_Project.jpg",
     "인상주의", "Wikimedia PD"),
    (14, "라 그르누이에르",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Claude_Monet_-_La_Grenouill%C3%A8re.jpg/1280px-Claude_Monet_-_La_Grenouill%C3%A8re.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Claude_Monet_-_La_Grenouill%C3%A8re.jpg/400px-Claude_Monet_-_La_Grenouill%C3%A8re.jpg",
     "인상주의", "Wikimedia PD"),
    # ── 르네상스 ─────────────────────────────────────────────────────
    (15, "모나리자",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/800px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/400px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg",
     "르네상스", "Wikimedia PD"),
    (16, "최후의 만찬",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/%22The_Last_Supper%22_by_Leonardo_da_Vinci.jpg/1280px-%22The_Last_Supper%22_by_Leonardo_da_Vinci.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/%22The_Last_Supper%22_by_Leonardo_da_Vinci.jpg/400px-%22The_Last_Supper%22_by_Leonardo_da_Vinci.jpg",
     "르네상스", "Wikimedia PD"),
    (17, "시스티나 성모",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Raphael_-_Sistine_Madonna.jpg/800px-Raphael_-_Sistine_Madonna.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Raphael_-_Sistine_Madonna.jpg/400px-Raphael_-_Sistine_Madonna.jpg",
     "르네상스", "Wikimedia PD"),
    (18, "아테네 학당",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/%22The_School_of_Athens%22_by_Raffaello_Sanzio_da_Urbino.jpg/1280px-%22The_School_of_Athens%22_by_Raffaello_Sanzio_da_Urbino.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/%22The_School_of_Athens%22_by_Raffaello_Sanzio_da_Urbino.jpg/400px-%22The_School_of_Athens%22_by_Raffaello_Sanzio_da_Urbino.jpg",
     "르네상스", "Wikimedia PD"),
    (19, "비너스의 탄생",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Sandro_Botticelli_-_La_nascita_di_Venere_-_Google_Art_Project_-_edited.jpg/1280px-Sandro_Botticelli_-_La_nascita_di_Venere_-_Google_Art_Project_-_edited.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Sandro_Botticelli_-_La_nascita_di_Venere_-_Google_Art_Project_-_edited.jpg/400px-Sandro_Botticelli_-_La_nascita_di_Venere_-_Google_Art_Project_-_edited.jpg",
     "르네상스", "Wikimedia PD"),
    (20, "봄 (프리마베라)",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Botticelli-primavera.jpg/1280px-Botticelli-primavera.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Botticelli-primavera.jpg/400px-Botticelli-primavera.jpg",
     "르네상스", "Wikimedia PD"),
    (21, "천지창조",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Michelangelo_-_Creation_of_Adam_%28cropped%29.jpg/1280px-Michelangelo_-_Creation_of_Adam_%28cropped%29.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Michelangelo_-_Creation_of_Adam_%28cropped%29.jpg/400px-Michelangelo_-_Creation_of_Adam_%28cropped%29.jpg",
     "르네상스", "Wikimedia PD"),
    (22, "성 게오르기우스와 용",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Raffaello_-_San_Giorgio_e_il_drago.jpg/900px-Raffaello_-_San_Giorgio_e_il_drago.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Raffaello_-_San_Giorgio_e_il_drago.jpg/400px-Raffaello_-_San_Giorgio_e_il_drago.jpg",
     "르네상스", "Wikimedia PD"),
    (23, "수태고지",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Fra_Angelico_-_The_Annunciation_-_WGA00594.jpg/1280px-Fra_Angelico_-_The_Annunciation_-_WGA00594.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Fra_Angelico_-_The_Annunciation_-_WGA00594.jpg/400px-Fra_Angelico_-_The_Annunciation_-_WGA00594.jpg",
     "르네상스", "Wikimedia PD"),
    # ── 바로크 ──────────────────────────────────────────────────────
    (24, "진주 귀걸이를 한 소녀",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/1665_Girl_with_a_Pearl_Earring.jpg/800px-1665_Girl_with_a_Pearl_Earring.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/1665_Girl_with_a_Pearl_Earring.jpg/400px-1665_Girl_with_a_Pearl_Earring.jpg",
     "바로크", "Wikimedia PD"),
    (25, "야경",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Rembrandt_van_Rijn_-_De_Nachtwacht.jpg/1280px-Rembrandt_van_Rijn_-_De_Nachtwacht.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Rembrandt_van_Rijn_-_De_Nachtwacht.jpg/400px-Rembrandt_van_Rijn_-_De_Nachtwacht.jpg",
     "바로크", "Wikimedia PD"),
    (26, "자화상 (렘브란트)",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Rembrandt_van_Rijn_-_Self-Portrait_-_Google_Art_Project.jpg/900px-Rembrandt_van_Rijn_-_Self-Portrait_-_Google_Art_Project.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Rembrandt_van_Rijn_-_Self-Portrait_-_Google_Art_Project.jpg/400px-Rembrandt_van_Rijn_-_Self-Portrait_-_Google_Art_Project.jpg",
     "바로크", "Wikimedia PD"),
    (27, "우유 따르는 여인",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Johannes_Vermeer_-_Het_melkmeisje_-_Google_Art_Project.jpg/900px-Johannes_Vermeer_-_Het_melkmeisje_-_Google_Art_Project.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Johannes_Vermeer_-_Het_melkmeisje_-_Google_Art_Project.jpg/400px-Johannes_Vermeer_-_Het_melkmeisje_-_Google_Art_Project.jpg",
     "바로크", "Wikimedia PD"),
    (28, "다윗 (카라바조)",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/CaravaggioMedusa.jpg/900px-CaravaggioMedusa.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/CaravaggioMedusa.jpg/400px-CaravaggioMedusa.jpg",
     "바로크", "Wikimedia PD"),
    (29, "성 마태오의 소명",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/The_Calling_of_Saint_Matthew-Caravaggo_%281599-1600%29.jpg/1280px-The_Calling_of_Saint_Matthew-Caravaggo_%281599-1600%29.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/The_Calling_of_Saint_Matthew-Caravaggo_%281599-1600%29.jpg/400px-The_Calling_of_Saint_Matthew-Caravaggo_%281599-1600%29.jpg",
     "바로크", "Wikimedia PD"),
    (30, "다윗과 골리앗",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Caravaggio_-_David_con_la_testa_di_Golia.jpg/900px-Caravaggio_-_David_con_la_testa_di_Golia.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Caravaggio_-_David_con_la_testa_di_Golia.jpg/400px-Caravaggio_-_David_con_la_testa_di_Golia.jpg",
     "바로크", "Wikimedia PD"),
    (31, "유딧과 홀로페르네스",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Artemisia_Gentileschi_-_Jael_and_Sisera_-_WGA8551.jpg/900px-Artemisia_Gentileschi_-_Jael_and_Sisera_-_WGA8551.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Artemisia_Gentileschi_-_Jael_and_Sisera_-_WGA8551.jpg/400px-Artemisia_Gentileschi_-_Jael_and_Sisera_-_WGA8551.jpg",
     "바로크", "Wikimedia PD"),
    (32, "동방 박사의 경배",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Peter_Paul_Rubens_-_Adoration_of_the_Magi_-_Google_Art_Project.jpg/1280px-Peter_Paul_Rubens_-_Adoration_of_the_Magi_-_Google_Art_Project.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Peter_Paul_Rubens_-_Adoration_of_the_Magi_-_Google_Art_Project.jpg/400px-Peter_Paul_Rubens_-_Adoration_of_the_Magi_-_Google_Art_Project.jpg",
     "바로크", "Wikimedia PD"),
    # ── 낭만주의 ─────────────────────────────────────────────────────
    (33, "자유의 여신",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Eug%C3%A8ne_Delacroix_-_La_libert%C3%A9_guidant_le_peuple.jpg/1280px-Eug%C3%A8ne_Delacroix_-_La_libert%C3%A9_guidant_le_peuple.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Eug%C3%A8ne_Delacroix_-_La_libert%C3%A9_guidant_le_peuple.jpg/400px-Eug%C3%A8ne_Delacroix_-_La_libert%C3%A9_guidant_le_peuple.jpg",
     "낭만주의", "Wikimedia PD"),
    (34, "키오스 섬의 학살",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Eug%C3%A8ne_Delacroix_-_Le_Massacre_de_Scio.jpg/900px-Eug%C3%A8ne_Delacroix_-_Le_Massacre_de_Scio.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Eug%C3%A8ne_Delacroix_-_Le_Massacre_de_Scio.jpg/400px-Eug%C3%A8ne_Delacroix_-_Le_Massacre_de_Scio.jpg",
     "낭만주의", "Wikimedia PD"),
    (35, "나폴레옹의 대관식",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Jacques-Louis_David%2C_The_Coronation_of_Napoleon_edit.jpg/1280px-Jacques-Louis_David%2C_The_Coronation_of_Napoleon_edit.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Jacques-Louis_David%2C_The_Coronation_of_Napoleon_edit.jpg/400px-Jacques-Louis_David%2C_The_Coronation_of_Napoleon_edit.jpg",
     "낭만주의", "Wikimedia PD"),
    (36, "건초 마차",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/John_Constable_-_The_Hay_Wain_%281821%29.jpg/1280px-John_Constable_-_The_Hay_Wain_%281821%29.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/John_Constable_-_The_Hay_Wain_%281821%29.jpg/400px-John_Constable_-_The_Hay_Wain_%281821%29.jpg",
     "낭만주의", "Wikimedia PD"),
    (37, "비, 증기, 속도",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Turner_-_Rain%2C_Steam_and_Speed_-_National_Gallery_file.jpg/1280px-Turner_-_Rain%2C_Steam_and_Speed_-_National_Gallery_file.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Turner_-_Rain%2C_Steam_and_Speed_-_National_Gallery_file.jpg/400px-Turner_-_Rain%2C_Steam_and_Speed_-_National_Gallery_file.jpg",
     "낭만주의", "Wikimedia PD"),
    (38, "노예선",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Joseph_Mallord_William_Turner_-_Slave_Ship_%28Slavers_Throwing_Overboard_the_Dead_and_Dying%2C_Typhoon_Coming_On%29_-_Google_Art_Project.jpg/1150px-Joseph_Mallord_William_Turner_-_Slave_Ship_%28Slavers_Throwing_Overboard_the_Dead_and_Dying%2C_Typhoon_Coming_On%29_-_Google_Art_Project.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Joseph_Mallord_William_Turner_-_Slave_Ship_%28Slavers_Throwing_Overboard_the_Dead_and_Dying%2C_Typhoon_Coming_On%29_-_Google_Art_Project.jpg/400px-Joseph_Mallord_William_Turner_-_Slave_Ship.jpg",
     "낭만주의", "Wikimedia PD"),
    # ── 상징주의/표현주의 ────────────────────────────────────────────
    (39, "키스 (클림트)",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/The_Kiss_-_Gustav_Klimt_-_Google_Cultural_Institute.jpg/1280px-The_Kiss_-_Gustav_Klimt_-_Google_Cultural_Institute.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/The_Kiss_-_Gustav_Klimt_-_Google_Cultural_Institute.jpg/400px-The_Kiss_-_Gustav_Klimt_-_Google_Cultural_Institute.jpg",
     "현대미술", "Wikimedia PD"),
    (40, "절규",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Edvard_Munch%2C_1893%2C_The_Scream%2C_oil%2C_tempera_and_pastel_on_cardboard%2C_91_x_73_cm%2C_National_Gallery_of_Norway.jpg/800px-Edvard_Munch%2C_1893%2C_The_Scream.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Edvard_Munch%2C_1893%2C_The_Scream%2C_oil%2C_tempera_and_pastel_on_cardboard%2C_91_x_73_cm%2C_National_Gallery_of_Norway.jpg/400px-Edvard_Munch.jpg",
     "현대미술", "Wikimedia PD"),
    # ── 인상주의 기타 ────────────────────────────────────────────────
    (41, "무희 (발레)",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Edgar_Degas_-_Dancer_with_Bouquet_of_Flowers_%28Star_of_the_Ballet%29_0691.jpg/900px-Edgar_Degas_-_Dancer_with_Bouquet_of_Flowers_%28Star_of_the_Ballet%29_0691.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Edgar_Degas_-_Dancer_with_Bouquet_of_Flowers_%28Star_of_the_Ballet%29_0691.jpg/400px-Edgar_Degas_-_Dancer_with_Bouquet_of_Flowers_%28Star_of_the_Ballet%29_0691.jpg",
     "인상주의", "Wikimedia PD"),
    (42, "발레 수업",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Degas_-_The_Ballet_Class.jpg/1230px-Degas_-_The_Ballet_Class.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Degas_-_The_Ballet_Class.jpg/400px-Degas_-_The_Ballet_Class.jpg",
     "인상주의", "Wikimedia PD"),
    (43, "청색 댄서들",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Edgar_Degas_-_Blue_Dancers.jpg/900px-Edgar_Degas_-_Blue_Dancers.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Edgar_Degas_-_Blue_Dancers.jpg/400px-Edgar_Degas_-_Blue_Dancers.jpg",
     "인상주의", "Wikimedia PD"),
    (44, "물랭 드 라 갈레트",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Pierre-Auguste_Renoir%2C_Le_Moulin_de_la_Galette.jpg/1280px-Pierre-Auguste_Renoir%2C_Le_Moulin_de_la_Galette.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Pierre-Auguste_Renoir%2C_Le_Moulin_de_la_Galette.jpg/400px-Pierre-Auguste_Renoir%2C_Le_Moulin_de_la_Galette.jpg",
     "인상주의", "Wikimedia PD"),
    (45, "목욕하는 여인들",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Pierre-Auguste_Renoir%2C_Les_Grandes_Baigneuses.jpg/1280px-Pierre-Auguste_Renoir%2C_Les_Grandes_Baigneuses.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Pierre-Auguste_Renoir%2C_Les_Grandes_Baigneuses.jpg/400px-Pierre-Auguste_Renoir%2C_Les_Grandes_Baigneuses.jpg",
     "인상주의", "Wikimedia PD"),
    (46, "풀밭 위의 점심",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Edouard_Manet_-_Le_D%C3%A9jeuner_sur_l%27herbe.jpg/1280px-Edouard_Manet_-_Le_D%C3%A9jeuner_sur_l%27herbe.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Edouard_Manet_-_Le_D%C3%A9jeuner_sur_l%27herbe.jpg/400px-Edouard_Manet_-_Le_D%C3%A9jeuner_sur_l%27herbe.jpg",
     "인상주의", "Wikimedia PD"),
    # ── 후기 인상주의 ────────────────────────────────────────────────
    (47, "사과와 오렌지",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Paul_C%C3%A9zanne_-_Apples_and_Oranges_-_Google_Art_Project.jpg/1205px-Paul_C%C3%A9zanne_-_Apples_and_Oranges_-_Google_Art_Project.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Paul_C%C3%A9zanne_-_Apples_and_Oranges_-_Google_Art_Project.jpg/400px-Paul_C%C3%A9zanne_-_Apples_and_Oranges_-_Google_Art_Project.jpg",
     "인상주의", "Wikimedia PD"),
    (48, "카드 놀이하는 사람들",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Paul_C%C3%A9zanne_-_The_Card_Players_-_Google_Art_Project.jpg/1280px-Paul_C%C3%A9zanne_-_The_Card_Players_-_Google_Art_Project.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Paul_C%C3%A9zanne_-_The_Card_Players_-_Google_Art_Project.jpg/400px-Paul_C%C3%A9zanne_-_The_Card_Players_-_Google_Art_Project.jpg",
     "인상주의", "Wikimedia PD"),
    (49, "타히티 여인들",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Paul_Gauguin_-_Two_Women_%28On_the_Beach%29.jpg/1280px-Paul_Gauguin_-_Two_Women_%28On_the_Beach%29.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Paul_Gauguin_-_Two_Women_%28On_the_Beach%29.jpg/400px-Paul_Gauguin_-_Two_Women_%28On_the_Beach%29.jpg",
     "인상주의", "Wikimedia PD"),
    (50, "우리는 어디서 왔는가",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Paul_Gauguin_-_D%27ou_venons-nous.jpg/1280px-Paul_Gauguin_-_D%27ou_venons-nous.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Paul_Gauguin_-_D%27ou_venons-nous.jpg/400px-Paul_Gauguin_-_D%27ou_venons-nous.jpg",
     "인상주의", "Wikimedia PD"),
]

# ── 다운로드 함수 ─────────────────────────────────────────────────────
def download_image(url, filepath, label=""):
    for attempt in range(RETRY + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
                if len(data) < 1000:
                    raise ValueError(f"응답 너무 작음: {len(data)} bytes")
                with open(filepath, 'wb') as f:
                    f.write(data)
                return True, len(data)
        except Exception as e:
            if attempt < RETRY:
                print(f"    재시도 {attempt+1}/{RETRY}...")
                time.sleep(2)
            else:
                return False, str(e)
    return False, "최대 재시도 초과"

# ── 메인 실행 ─────────────────────────────────────────────────────────
def main():
    # 폴더 생성
    os.makedirs(FULL_DIR,  exist_ok=True)
    os.makedirs(THUMB_DIR, exist_ok=True)

    total = len(ARTWORKS)
    success_full  = 0
    success_thumb = 0
    failed = []

    print(f"\n{'='*60}")
    print(f"  GALERIE 이미지 다운로드 시작 — 총 {total}개 작품")
    print(f"  저장 위치: {os.path.abspath(OUTPUT_DIR)}")
    print(f"{'='*60}\n")

    for i, (id_, title, full_url, thumb_url, cat, source) in enumerate(ARTWORKS, 1):
        base = f"{id_:03d}"
        full_path  = os.path.join(FULL_DIR,  f"{base}_full.jpg")
        thumb_path = os.path.join(THUMB_DIR, f"{base}_thumb.jpg")

        print(f"[{i:3d}/{total}] {title} ({source})")

        # Full 이미지
        if os.path.exists(full_path):
            print(f"  ✓ full  이미 존재 — 건너뜀")
            success_full += 1
        else:
            ok, info = download_image(full_url, full_path, f"full_{base}")
            if ok:
                print(f"  ✅ full  {info//1024}KB")
                success_full += 1
            else:
                print(f"  ❌ full  실패: {info}")
                failed.append((id_, title, 'full', str(info)))

        # Thumb 이미지
        if os.path.exists(thumb_path):
            print(f"  ✓ thumb 이미 존재 — 건너뜀")
            success_thumb += 1
        else:
            time.sleep(0.3)
            ok, info = download_image(thumb_url, thumb_path, f"thumb_{base}")
            if ok:
                print(f"  ✅ thumb {info//1024}KB")
                success_thumb += 1
            else:
                print(f"  ❌ thumb 실패: {info}")
                failed.append((id_, title, 'thumb', str(info)))

        time.sleep(DELAY)

    # 결과 요약
    print(f"\n{'='*60}")
    print(f"  완료: full {success_full}/{total} · thumb {success_thumb}/{total}")
    if failed:
        print(f"\n  실패 목록 ({len(failed)}건):")
        for id_, title, typ, err in failed:
            print(f"    id:{id_} [{typ}] {title} — {err[:60]}")
        print(f"\n  failed_list.txt 에 저장됨")
        with open("failed_list.txt", "w", encoding="utf-8") as f:
            for item in failed:
                f.write(f"{item[0]}\t{item[1]}\t{item[2]}\t{item[3]}\n")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
