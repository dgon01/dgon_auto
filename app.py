// ==========================================
// [설정 영역] 시트 이름과 셀 주소를 본인 환경에 맞게 수정하세요.
// ==========================================
var CONF = {
  sheetName: {
    target: "이전영수증",      // 결과물이 출력될 영수증 시트
    source: "근저당권설정"     // 데이터를 가져올 원본 시트
  },
  cell: {
    // [이전영수증] 시트의 셀 위치
    rateOutput: "B27",       // 할인율 표시 셀
    dateOutput: "C27",       // 기준일 표시 셀
    addressOutput: "B7",     // 물건지가 표시될 셀 (영수증의 '물건지' 란)
    bondMaxOutput: "Q5",     // 채권최고액 표시 셀 (예시 위치)
    
    // [근저당권설정] 시트의 데이터 위치 (※ 사용하시는 엑셀 양식에 맞춰 수정 필요)
    sourceAddress: "C5",     // 근저당권설정 탭에서 '주소(물건지)'가 있는 셀
    sourceBondMax: "D5"      // 근저당권설정 탭에서 '채권최고액'이 있는 셀
  }
};

// ==========================================
// [메인 함수] 이 함수를 실행하거나 버튼에 연결하세요.
// ==========================================
function updateReceiptData() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var targetSheet = ss.getSheetByName(CONF.sheetName.target);
  var sourceSheet = ss.getSheetByName(CONF.sheetName.source);

  if (!targetSheet || !sourceSheet) {
    SpreadsheetApp.getUi().alert("시트 이름을 확인해주세요.\n(설정된 이름: " + CONF.sheetName.target + ", " + CONF.sheetName.source + ")");
    return;
  }

  // 1. 채권할인율 업데이트
  updateBondRate(targetSheet);

  // 2. [근저당권설정] 탭에서 데이터 가져오기
  var address = sourceSheet.getRange(CONF.cell.sourceAddress).getValue(); // 주소 가져오기
  var bondMax = sourceSheet.getRange(CONF.cell.sourceBondMax).getValue(); // 채권액 가져오기

  // 3. [이전영수증] 탭에 데이터 입력 (물건지 등)
  targetSheet.getRange(CONF.cell.addressOutput).setValue(address); // 물건지 입력
  
  // 4. 금액 데이터 입력 및 포맷팅 (#,##0)
  var bondRange = targetSheet.getRange(CONF.cell.bondMaxOutput);
  bondRange.setValue(bondMax).setNumberFormat("#,##0"); // 1000단위 콤마 적용

  // (추가) 영수증 내 금액란 전체 포맷팅이 필요하다면 아래와 같이 범위로 지정 가능
  // targetSheet.getRange("O5:O21").setNumberFormat("#,##0"); 
}

// ==========================================
// [기능 함수] 채권할인율 가져오기 (제공해주신 코드 보완)
// ==========================================
function updateBondRate(sheet) {
  try {
    var url = "https://lawss.co.kr/lawpro/homepage/siga/auto_siga_kjaa.php";
    var response = UrlFetchApp.fetch(url, {'muteHttpExceptions': true});
    var content = response.getContentText("EUC-KR");

    // 정규식으로 할인율 추출
    var regex = /오늘 채권할인율\s*=\s*([\d\.]+) %/;
    var match = content.match(regex);
    
    if (match && match[1]) {
      var rate = match[1];
      var today = new Date();
      var formattedDate = Utilities.formatDate(today, "GMT+9", "yyyy-MM-dd");
      
      // 값 입력
      sheet.getRange(CONF.cell.rateOutput).setValue(rate + "%");
      sheet.getRange(CONF.cell.dateOutput).setValue(formattedDate);
      
      // 로그 출력 (디버깅용)
      Logger.log("할인율 갱신 완료: " + rate + "% (" + formattedDate + ")");
    } else {
      Logger.log("패턴 매칭 실패: 사이트 구조가 변경되었을 수 있습니다.");
      // 실패 시 사용자에게 알림을 띄우고 싶다면 아래 주석 해제
      // SpreadsheetApp.getUi().alert("채권할인율을 불러오지 못했습니다.");
    }
  } catch (e) {
    Logger.log("통신 에러: " + e.toString());
  }
}