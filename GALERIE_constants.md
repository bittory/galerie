# GALERIE 앱 — 프로젝트 상수 및 규칙

> ⚠️ **Claude 자동 적용 규칙**: masterpiece-wallpaper-app.html 및 galerie 관련 파일 생성·수정 시
> 아래 상수들을 항상 자동으로 반영할 것. `YOUR_APP_ID_HERE` 등의 플레이스홀더를 절대 사용하지 말 것.

---

## 🔑 등록된 API 키 및 ID

| 항목 | 값 | 설명 |
|------|-----|------|
| **Google Cast App ID** | `83B532DF` | cast.google.com 등록 완료, $5 지불 |
| Cast Receiver URL | `https://bittory.github.io/galerie/galerie-cast-receiver.html` | GitHub Pages 배포 |
| GitHub 저장소 | `bittory/galerie` | Public |
| GitHub Pages URL | `https://bittory.github.io/galerie/` | |

---

## 📋 코드 반영 규칙

### Cast SDK 초기화 — 항상 이 형태로 작성
```javascript
const GALERIE_APP_ID = '83B532DF'; // Google Cast SDK App ID (cast.google.com 등록)

cast.framework.CastContext.getInstance().setOptions({
  receiverApplicationId: GALERIE_APP_ID,
  autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED,
});
```

### ❌ 절대 사용 금지
```javascript
// 아래처럼 플레이스홀더를 사용하면 안 됨
const GALERIE_APP_ID = 'YOUR_APP_ID_HERE';  // ❌ 금지
const GALERIE_APP_ID = 'REPLACE_ME';         // ❌ 금지
```

---

## 🖼 이미지 소스 우선순위

1. **Met Museum CC0** — `images.metmuseum.org/CRDImages/...` (CORS 없음, 최우선)
2. **Art Institute Chicago CC0** — `api.artic.edu/iiif/2/...`
3. **Cleveland Museum CC0** — `openaccess-api.clevelandart.org/...`
4. **Wikimedia Commons PD** — `upload.wikimedia.org/wikipedia/commons/...` (referrer 정책 필요)
5. **국립중앙박물관** — 공공누리 제1유형, 출처 표기 필수

### Wikimedia 사용 시 필수 메타태그
```html
<meta name="referrer" content="no-referrer">
```

---

## 🎨 UI 상수

| 항목 | 값 |
|------|-----|
| 기본 폰트 | `'Malgun Gothic', '맑은 고딕', sans-serif` |
| 카드 border-radius | `22px` |
| 모달 border-radius | `28px` |
| 컨트롤 버튼 border-radius | `16px` |

---

## 🚫 저작권 제거 목록

아래 작품은 저작권 문제로 DB에 포함 금지:

| 작가 | 이유 | 만료 시점 |
|------|------|----------|
| 파블로 피카소 | 저작권 보호 중 | 2043년 |
| 앙리 마티스 | 재단 분쟁 우려 (회색지대) | 2024년 원칙상 만료, 불확실 |
| 살바도르 달리 | 저작권 보호 중 | 2039년 |

---

## 💰 후원 링크

| 플랫폼 | URL | 비고 |
|--------|-----|------|
| Ko-fi | `https://ko-fi.com/` | ← 실제 계정명으로 교체 필요 |
| 카카오페이 | `https://qr.kakaopay.com/Ej9Eq4BRN` | ✅ 등록 완료 |

---

_최종 업데이트: 2026-03-25_
_담당: bittory (Tony)_
