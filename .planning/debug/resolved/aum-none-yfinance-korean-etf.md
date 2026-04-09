---
status: resolved
trigger: "yfinance로 한국 ETF AUM 조회 시 AUM=None 반환"
created: 2026-04-09T00:00:00+09:00
updated: 2026-04-09T00:15:00+09:00
---

## Current Focus

hypothesis: CONFIRMED AND FIXED
test: 로컬에서 fetch_market_data_batch(['293180','360200','069500','0026S0','360750']) 실행 검증 완료
expecting: GitHub Actions에서 python etl_process.py 실행 시 AUM 값이 None이 아닌 실제 억원 값으로 출력되어야 함
next_action: 사용자가 GitHub Actions 또는 로컬에서 etl_process.py 실행하여 AUM 값 확인

## Symptoms

expected: fetch_market_data_batch()가 한국 ETF 종목코드별로 AUM(억원 단위 순자산) 값을 반환해야 함
actual: AUM=None 반환됨. 거래량(volume)은 정상 조회됨
errors: 에러 없이 None 반환. sharesOutstanding, impliedSharesOutstanding, totalAssets, marketCap, fast_info.market_cap 모두 None
reproduction: python etl_process.py 실행 → "293180: AUM=None억, 거래량=72089" 형태로 출력됨
started: pykrx에서 yfinance로 교체 후 발생 (GitHub Actions에서 KRX 차단으로 인해 교체)

## Eliminated

(없음)

## Evidence

- timestamp: 2026-04-09T00:00:00+09:00
  checked: etl_process.py fetch_market_data_batch (line 304-355)
  found: |
    - ticker.history(period="5d") → 정상 (Volume, Close 있음)
    - info.get("sharesOutstanding") → None
    - info.get("impliedSharesOutstanding") → None
    - info.get("totalAssets") → None
    - info.get("marketCap") → None
    - ticker.fast_info.market_cap → None (최근 추가된 fallback)
    - close 가격은 hist["Close"]에서 정상 획득 가능
  implication: |
    yfinance가 .KS ETF에 대해 주식수/시가총액 메타데이터를 제공하지 않음.
    그러나 close 가격(종가)과 volume은 제공함.
    AUM 계산에 필요한 상장주식수(shares outstanding)를 다른 방법으로 구해야 함.

- timestamp: 2026-04-09T00:05:00+09:00
  checked: Yahoo Finance quoteSummary API v10 (query1.finance.yahoo.com) for 360200.KS
  found: |
    - defaultKeyStatistics: 모두 빈값
    - summaryDetail.sharesOutstanding: None
    - summaryDetail.marketCap: {}
    - summaryDetail.totalAssets: {}
    - topHoldings/fundPerformance 모듈: 404 "No fundamentals data found for symbol: 360200.KS"
    - v8 chart API meta: marketCap=None, sharesOutstanding=None
  implication: |
    Yahoo Finance 서버가 한국 KSE 상장 ETF에 대해 fundamentals 데이터를
    아예 제공하지 않음. 이는 yfinance 라이브러리 문제가 아니라 Yahoo Finance
    데이터 커버리지 문제임. 모든 shares/marketCap 기반 접근은 근본적으로 실패함.

- timestamp: 2026-04-09T00:08:00+09:00
  checked: NAVER Finance ETF 리스트 API (finance.naver.com/api/sise/etfItemList.nhn)
  found: |
    - HTTP 200, 1088개 ETF 전체 목록 반환
    - 각 항목: itemcode, nowVal(현재가), nav, quant(거래량), marketSum(시가총액 억원)
    - 293180(HANARO 200): marketSum=4794, quant=86673
    - 360200(ACE S&P500): marketSum=33926, quant=173167
    - 별도 인증/crumb 불필요, requests만으로 접근 가능
  implication: |
    NAVER Finance API가 단일 요청으로 모든 한국 ETF의 AUM(marketSum, 억원 단위)과
    거래량(quant)을 반환함. yfinance 대신 이 API를 사용하면 근본적으로 문제 해결.
    GitHub Actions 환경에서도 NAVER Finance는 접근 가능(KRX와 달리 차단되지 않음).

## Resolution

root_cause: |
  Yahoo Finance(yfinance 백엔드)는 한국 KSE 상장 ETF(.KS)에 대해 fundamentals 데이터
  (sharesOutstanding, marketCap, totalAssets 등)를 제공하지 않음.
  Yahoo Finance v10 quoteSummary API가 "No fundamentals data found for symbol" 오류를
  반환하는 것으로 확인됨. 이는 yfinance 라이브러리 버그가 아니라 Yahoo Finance의
  한국 ETF 데이터 커버리지 한계임.
fix: |
  fetch_market_data_batch()를 NAVER Finance ETF 리스트 API 기반으로 교체.
  https://finance.naver.com/api/sise/etfItemList.nhn 에서 단일 요청으로
  전체 ETF 목록(marketSum=억원, quant=거래량)을 받아와 코드별로 매핑.
  yfinance 의존성 제거.
verification: |
  사용자가 실제 환경에서 확인:
  293180: AUM=4797억, 거래량=87586
  360200: AUM=33919억, 거래량=174227
  069500: AUM=198003억, 거래량=9541642
  AUM이 None이 아닌 실제 억원 단위 값으로 정상 반환됨.
files_changed: [etl_process.py]
