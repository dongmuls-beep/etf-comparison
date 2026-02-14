# ETF비교사이트 프로젝트 구조 문서

작성일: 2026-02-14  
분석 범위: `c:\Users\dongm\OneDrive\Antigravity\ETF비교사이트`  
원칙: 기존 파일은 수정하지 않고, 구조 분석 결과만 문서화

## 1) 프로젝트 한 줄 요약
정적 웹사이트(`index.html` + `style.css` + `script.js`)가 `data.json`을 읽어 ETF 실부담비용 테이블을 제공하고, Python ETL(`etl_process.py`)이 KOFIA/GAS 데이터를 수집·가공해 `data.json`을 갱신하는 구조입니다.

## 2) 루트 구조
```text
ETF비교사이트/
├─ .github/
│  └─ workflows/
│     └─ daily_update.yml
├─ .venv/
├─ .gitignore
├─ CNAME
├─ data.json
├─ deployment_guide.md
├─ etl_process.py
├─ gas_script_v2.js
├─ google_sheets_setup.md
├─ index.html
├─ requirements.txt
├─ robots.txt
├─ script.js
├─ sitemap.xml
├─ style.css
├─ translations.js
└─ 사이트계획서.md
```

## 3) 파일별 역할
| 파일 | 역할 | 비고 |
|---|---|---|
| `index.html` | 화면 마크업, SEO 메타, 해시 라우팅용 섹션 정의 | `home/pension/isa/fomo/guide` 5개 뷰 |
| `style.css` | 전체 UI 스타일, 반응형, 배경 애니메이션 | Glass 스타일 기반 |
| `script.js` | 언어 초기화, 데이터 로드, 탭/테이블 렌더링, 해시 라우팅 | 데이터 소스: `./data.json` |
| `translations.js` | 다국어 사전 | `ko/vi/zh/en/ja/th/tl/km` |
| `data.json` | 프론트가 직접 읽는 정적 데이터 | 현재 59개 레코드 |
| `etl_process.py` | KOFIA 엑셀 수집 + 매칭/계산 + `data.json` 저장(+ GAS POST) | Selenium 기반 |
| `.github/workflows/daily_update.yml` | 일일 ETL 자동 실행 워크플로우 | UTC 00:00(한국 09:00) |
| `gas_script_v2.js` | Google Apps Script(Web App) API(GET/POST) | 관리 시트/결과 시트 연동 |
| `requirements.txt` | ETL Python 의존성 목록 | pandas, selenium 등 |
| `deployment_guide.md` | 배포/운영 가이드 문서 | GitHub Pages/Adsense 중심 |
| `google_sheets_setup.md` | Google Sheets + GAS 세팅 가이드 | 시트 구성 및 배포 절차 |
| `CNAME` | 커스텀 도메인 설정 | `etfsave.life` |
| `robots.txt` | 크롤러 정책 | Sitemap 링크 포함 |
| `sitemap.xml` | 검색엔진 sitemap | 루트 URL 1개 등록 |
| `사이트계획서.md` | 서비스 기획 문서 | 초기 설계 메모 성격 |

## 4) 데이터 흐름(운영 관점)
1. GitHub Actions(`daily_update.yml`)가 일정 또는 수동으로 실행됨.
2. `etl_process.py`가 KOFIA 페이지에서 엑셀을 Selenium으로 다운로드.
3. GAS `getItems`를 통해 관리 대상 종목 목록 조회(실패 시 mock fallback).
4. 엑셀 데이터를 종목 표준코드 기준으로 매칭하고 실부담비용 계산.
5. 결과를 `data.json`으로 저장하고, 필요 시 GAS로 POST 전송.
6. 프론트(`script.js`)가 `./data.json`을 fetch하여 탭/테이블 렌더링.

## 5) 프론트 동작 흐름
1. `DOMContentLoaded`에서 `initLanguage()`, `fetchData()`, `initNavigation()`, `handleRouting()` 실행.
2. 해시 라우팅으로 `#home`, `#pension`, `#isa`, `#fomo`, `#guide` 섹션 전환.
3. 언어 선택값을 `localStorage(site_language)`에 저장/복원.
4. `data.json`을 받아 카테고리 탭 생성 후 실부담비용 오름차순 정렬 렌더링.
5. 종목코드 클릭 시 클립보드 복사.

## 6) 데이터 스키마(`data.json`)
주요 키:
- `구분`
- `종목코드`
- `종목명`
- `총보수`
- `기타비용`
- `매매중개수수료`
- `실부담비용`

샘플 형태:
```json
{
  "구분": "S&P500",
  "종목코드": "360200",
  "종목명": "ACE 미국S&P500",
  "총보수": 0.0047,
  "기타비용": 0.06,
  "매매중개수수료": 0.0312,
  "실부담비용": 0.0959
}
```

## 7) 자동화/인프라 포인트
- 배포 형태: 정적 호스팅(GitHub Pages 기준)
- 자동 업데이트: GitHub Actions + `git-auto-commit-action`로 `data.json` 커밋
- 외부 연동:
  - KOFIA 공시 페이지(엑셀 소스)
  - Google Apps Script Web App(GET/POST API)
  - Naver Finance 링크(종목 상세 이동)

## 8) 참고 문서
- `deployment_guide.md`
- `google_sheets_setup.md`
- `사이트계획서.md`
