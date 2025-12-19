from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from playwright.sync_api import sync_playwright
import time
import threading

app = FastAPI()

# 동시 실행 방지 Lock
wetax_lock = threading.Lock()

# 전역 page 객체 (세션 유지용)
global_page = None
session_thread = None

# 서버 시작 시 세션 유지 스레드 자동 시작
@app.on_event("startup")
def startup_event():
    global session_thread
    if session_thread is None or not session_thread.is_alive():
        session_thread = threading.Thread(target=keep_session_alive, daemon=True)
        session_thread.start()
        print("✅ 세션 자동 유지 활성화 (10분마다 새로고침)")

class CaseData(BaseModel):
    type: str
    taxpayer_type: str
    taxpayer_name: str
    resident_no_front: str
    resident_no_back: str
    phone: str
    address: str
    address_detail: str
    property_address: str
    property_detail: str
    tax_base: Optional[int] = None

class SubmitRequest(BaseModel):
    cases: List[CaseData]

cause_codes = {"설정": "0556", "변경": "9984", "말소": "9991"}

def keep_session_alive():
    """10분마다 새로고침 + 마우스 이동으로 세션 유지"""
    while True:
        time.sleep(600)  # 10분 (20분 타임아웃 전에 충분히 여유있게)
        try:
            # 작업 중이면 건너뛰기
            if wetax_lock.locked():
                print("⏳ 작업 중 - 세션 연장 건너뜀")
                continue
            
            # 매번 새로 연결해서 활동
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                page = browser.contexts[0].pages[0]
                
                # 마우스 이동 (활동 감지용)
                page.mouse.move(100, 100)
                time.sleep(0.5)
                page.mouse.move(200, 200)
                time.sleep(0.5)
                
                # 새로고침
                page.reload()
                time.sleep(2)
                
                print("✅ 세션 연장됨 (새로고침 + 활동)")
        except Exception as e:
            print(f"세션 연장 실패: {e}")

def search_address(frame, search_text, detail_text):
    """주소 검색 - 실패 시 False 반환"""
    try:
        frame.fill("#ibx_search", search_text)
        frame.click("#btnSearch")
        time.sleep(2)
        
        # 검색 결과 확인
        radio = frame.query_selector("input[type=radio]")
        if not radio:
            print(f"  ⚠️ 주소 검색 결과 없음: {search_text}")
            return False
        
        frame.evaluate("document.querySelector('input[type=radio]').checked=true")
        time.sleep(0.5)
        frame.fill("#etcAddr", detail_text)
        frame.click("#btnConfirm")
        time.sleep(1)
        return True
    except Exception as e:
        print(f"  ⚠️ 주소 검색 오류: {e}")
        return False

def process_cases(page, cases_data):
    results = []
    
    for case in cases_data:
        try:
            print(f"처리 중: {case['taxpayer_name']} ({case['type']})")
            
            page.click("text=위임")
            time.sleep(1)
            page.click("text=등록면허세(등록분)")
            time.sleep(2)
            
            try:
                page.click("text=닫기", timeout=3000)
                time.sleep(0.5)
            except:
                pass
            
            code = "01" if case["taxpayer_type"] == "01" else "02"
            page.select_option("#txpInfo_txpTypCd", code)
            time.sleep(2)
            
            if case["taxpayer_type"] == "01":
                page.fill("#txpInfo_txpNm", case["taxpayer_name"])
            
            page.fill("#txpInfo_tnenc1", case["resident_no_front"])
            page.fill("#txpInfo_tnenc2", case["resident_no_back"])
            page.fill("#txpInfo_telno", case["phone"])
            
            # 납세자 주소 검색
            page.click("#btnTxpAddr")
            time.sleep(2)
            page.wait_for_selector("iframe[name='cmnPopup_addr2']")
            time.sleep(1)
            frame = page.frame(name="cmnPopup_addr2")
            
            if not search_address(frame, case["address"], case["address_detail"]):
                try:
                    frame.click("text=닫기")
                except:
                    pass
                print(f"  ❌ 납세자 주소 검색 실패 - 스킵: {case['taxpayer_name']}")
                results.append({
                    "status": "실패", 
                    "name": case["taxpayer_name"], 
                    "error": f"납세자 주소 검색 실패: {case['address']}"
                })
                continue
            
            page.click("#btnTxpInfoConfirm")
            time.sleep(1)
            
            page.select_option("#sel_rgtxObjKndCd", "01")
            time.sleep(0.5)
            page.select_option("#sel_rgtxObjKndDtlCd", "0102")
            time.sleep(0.5)
            page.select_option("#sel_rgtxCsDtlCd", cause_codes.get(case["type"], "0556"))
            time.sleep(0.5)
            
            # 물건지 주소 검색
            page.click("#btn_addrSearch")
            time.sleep(2)
            page.wait_for_selector("iframe[name='cmnPopup_addr2']")
            time.sleep(1)
            frame = page.frame(name="cmnPopup_addr2")
            
            if not search_address(frame, case["property_address"], case["property_detail"]):
                try:
                    frame.click("text=닫기")
                except:
                    pass
                print(f"  ❌ 물건지 주소 검색 실패 - 스킵: {case['taxpayer_name']}")
                results.append({
                    "status": "실패", 
                    "name": case["taxpayer_name"], 
                    "error": f"물건지 주소 검색 실패: {case['property_address']}"
                })
                page.goto("https://www.wetax.go.kr")
                time.sleep(2)
                continue
            
            if case["type"] == "설정" and case.get("tax_base"):
                page.fill("#objInfo_txbAmt", str(case["tax_base"]))
                time.sleep(0.5)
            
            page.click("#btnReqCalc")
            time.sleep(2)
            
            page.set_input_files("input[type='file']", "blank.pdf")
            time.sleep(1)
            page.click("#btnAtchConfirm")
            time.sleep(2)
            
            page.click("#btn_next")
            time.sleep(3)
            
            print(f"✅ 완료: {case['taxpayer_name']}")
            results.append({"status": "성공", "name": case["taxpayer_name"]})
            
        except Exception as e:
            print(f"❌ 오류: {e}")
            results.append({"status": "실패", "name": case["taxpayer_name"], "error": str(e)})
            try:
                page.goto("https://www.wetax.go.kr")
                time.sleep(2)
            except:
                pass
    
    return results

@app.get("/")
def root():
    return {"status": "ok", "message": "Wetax Server Running"}

@app.post("/wetax/submit")
def submit(request: SubmitRequest):
    global global_page, session_thread
    
    if not wetax_lock.acquire(blocking=False):
        return {"error": "이미 처리 중인 작업이 있습니다. 잠시 후 다시 시도하세요."}
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            global_page = browser.contexts[0].pages[0]
            
            if session_thread is None or not session_thread.is_alive():
                session_thread = threading.Thread(target=keep_session_alive, daemon=True)
                session_thread.start()
                print("✅ 세션 자동 유지 활성화 (10분마다 새로고침)")
            
            cases_data = [c.model_dump() for c in request.cases]
            results = process_cases(global_page, cases_data)
            
            return {"results": results}
    finally:
        wetax_lock.release()

def run_server():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

if __name__ == "__main__":
    run_server()
