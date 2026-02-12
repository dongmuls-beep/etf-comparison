# 구글 시트 & 구글 앱스 스크립트(GAS) 설정 가이드

## 1. 구글 시트 만들기
1.  새 구글 스프레드시트를 하나 만드세요.
2.  파일 이름을 **"ETF 비교 데이터"** (또는 원하시는 대로)로 변경하세요.
3.  첫 번째 시트(탭) 이름을 **"종목관리"**로 변경하세요.
    -   **A열**: 구분 (예: 국내주식형)
    -   **B열**: 종목코드 (예: 360750)
    -   **C열**: 종목명 (예: TIGER 미국S&P500)
4.  새 시트(탭)를 하나 더 만들고 이름을 **"수수료결과"**로 변경하세요.
    -   이 탭은 비워두세요. 파이썬 로봇이 여기에 데이터를 채워줄 겁니다.

## 2. 구글 앱스 스크립트(GAS) 설정 - 통합형 (읽기/쓰기)
이 스크립트는 두 가지 역할을 합니다:
1.  웹사이트가 보여줄 데이터를 JSON으로 제공 (**GET**)
2.  파이썬 로봇이 보낸 데이터를 받아서 시트에 저장 (**POST**)

이 방법을 쓰면 **복잡한 구글 클라우드(GCP) 설정이나 서비스 계정이 필요 없습니다.**

1.  구글 시트 메뉴에서 **확장 프로그램 > Apps Script**를 클릭하세요.
2.  `Code.gs` 파일 내용을 아래 코드로 완전히 교체하세요.

```javascript
// 시트 이름 설정
var RESULT_SHEET_NAME = "수수료결과";
var MANAGE_SHEET_NAME = "종목관리";

// 1. 웹사이트에서 데이터 요청할 때 (GET)
function doGet(e) {
  var action = e.parameter.action;
  
  if (action == "getItems") {
    // 종목관리 탭의 데이터를 파이썬에게 줄 때
    return getSheetDataJSON(MANAGE_SHEET_NAME);
  } else {
    // 수수료결과 탭의 데이터를 웹사이트에 줄 때 (기본)
    return getSheetDataJSON(RESULT_SHEET_NAME);
  }
}

// 2. 파이썬이 데이터 업데이트할 때 (POST)
function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(RESULT_SHEET_NAME);
    if (!sheet) return ContentService.createTextOutput("Error: Sheet not found");

    // 파이썬이 보낸 JSON 데이터 받기
    var rawData = JSON.parse(e.postData.contents);
    
    // 기존 데이터 지우고 새로 쓰기
    sheet.clear();
    
    if (rawData.length > 0) {
      // 헤더 추가
      var headers = Object.keys(rawData[0]);
      sheet.appendRow(headers);
      
      // 데이터 추가
      var rows = rawData.map(function(item) {
        return headers.map(function(header) { return item[header]; });
      });
      
      // 한 번에 쓰기 (속도 최적화)
      sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
    }
    
    return ContentService.createTextOutput("Success");
  } catch (error) {
    return ContentService.createTextOutput("Error: " + error.toString());
  }
}

// 헬퍼 함수: 시트 데이터를 JSON으로 변환
function getSheetDataJSON(sheetName) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  var data = sheet.getDataRange().getValues();
  
  if (data.length === 0) return ContentService.createTextOutput(JSON.stringify([]));

  var headers = data[0];
  var rows = data.slice(1);
  var result = rows.map(function(row) {
    var obj = {};
    headers.forEach(function(header, index) {
      obj[header] = row[index];
    });
    return obj;
  });

  return ContentService.createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}
```

3.  오른쪽 위의 **배포(Deploy)** 버튼 > **새 배포(New deployment)**를 클릭하세요.
4.  **유형 선택** 톱니바퀴 > **웹 앱(Web app)**을 선택하세요.
5.  **설명**: "ETF 통합 API".
6.  **다음 사용자 권한으로 실행**: **나(Me)** (본인 이메일).
7.  **액세스 권한이 있는 사용자**: **모든 사용자(Anyone)**. (**중요!**)
8.  **배포** 버튼 클릭.
9.  **웹 앱 URL**을 복사해서 메모장에 저장해두세요. 이 주소 하나로 파이썬과 웹사이트 모두 연결됩니다!
