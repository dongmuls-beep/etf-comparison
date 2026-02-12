
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
        // 파이썬이 보낸 JSON 데이터 받기
        var payload = JSON.parse(e.postData.contents);

        // [NEW] 만약 종목관리 업데이트 요청이라면
        if (payload.action === "updateManage" && payload.data) {
            return updateManageSheet(payload.data);
        }

        // [기존] 단순 배열이면 수수료결과 업데이트 (하위 호환성 유지)
        var dataToUpdate = payload;
        // 만약 { "data": [...] } 형태로 왔다면 data 추출
        if (payload.data && Array.isArray(payload.data) && !payload.action) {
            dataToUpdate = payload.data;
        }

        return updateResultSheet(dataToUpdate);

    } catch (error) {
        return ContentService.createTextOutput("Error: " + error.toString());
    }
}

// 수수료 결과 시트 업데이트 (기존 로직)
function updateResultSheet(rawData) {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(RESULT_SHEET_NAME);
    if (!sheet) return ContentService.createTextOutput("Error: Sheet not found");

    sheet.clear();

    if (rawData.length > 0) {
        var headers = Object.keys(rawData[0]);
        sheet.appendRow(headers);

        var rows = rawData.map(function (item) {
            return headers.map(function (header) { return item[header]; });
        });

        sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
    }
    return ContentService.createTextOutput("Success Result Update");
}

// [NEW] 종목관리 시트 업데이트 (표준코드, 펀드명)
function updateManageSheet(updates) {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(MANAGE_SHEET_NAME);
    if (!sheet) return ContentService.createTextOutput("Error: Manage Sheet not found");

    // 현재 시트 데이터 가져오기 (헤더 제외)
    var dataRange = sheet.getDataRange();
    var values = dataRange.getValues(); // 전체 데이터
    var headers = values[0];

    // 종목코드 열 인덱스 찾기 (B열: 인덱스 1)
    var codeIndex = 1;
    // 표준코드 열 인덱스 (D열: 인덱스 3)
    var stdCodeIndex = 3;
    // 펀드명 열 인덱스 (E열: 인덱스 4)
    var fundNameIndex = 4;

    // 업데이트를 위한 맵핑 (Code -> {std, name})
    var updateMap = {};
    updates.forEach(function (item) {
        updateMap[String(item.code).trim()] = item;
    });

    // 행마다 돌면서 종목코드가 일치하면 업데이트
    // 1부터 시작 (헤더 건너뛰기)
    for (var i = 1; i < values.length; i++) {
        var rowCode = String(values[i][codeIndex]).trim();

        if (updateMap[rowCode]) {
            // 해당 행의 D, E열 업데이트
            // setValue는 느리므로 배열을 업데이트하고 나중에 한 번에 쓰는 게 좋지만
            // 데이터 양이 적어서 개별 업데이트도 괜찮음. 여기선 배열 수정 후 setValues 사용.
            if (updateMap[rowCode].std_code) values[i][stdCodeIndex] = updateMap[rowCode].std_code;
            if (updateMap[rowCode].fund_name) values[i][fundNameIndex] = updateMap[rowCode].fund_name;
        }
    }

    // 변경된 전체 데이터를 다시 씀 (효율적)
    // 주의: 사용자 서식 등이 깨질 수 있으므로 값만 업데이트
    // 전체 범위를 덮어쓰기
    sheet.getRange(1, 1, values.length, values[0].length).setValues(values);

    return ContentService.createTextOutput("Success Manage Update: " + updates.length + " items processed.");
}

// 헬퍼 함수: 시트 데이터를 JSON으로 변환
function getSheetDataJSON(sheetName) {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
    var data = sheet.getDataRange().getValues();

    if (data.length === 0) return ContentService.createTextOutput(JSON.stringify([]));

    var headers = data[0];
    var rows = data.slice(1);
    var result = rows.map(function (row) {
        var obj = {};
        headers.forEach(function (header, index) {
            obj[header] = row[index];
        });
        return obj;
    });

    return ContentService.createTextOutput(JSON.stringify(result))
        .setMimeType(ContentService.MimeType.JSON);
}
