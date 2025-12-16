# =============================================================================
# Tab 4: 말소 문서 작성
# =============================================================================
with tab4:
    # 헤더
    col_header = st.columns([5, 1, 1])
    with col_header[0]:
        st.markdown("### 🗑️ 말소 문서 작성")
    with col_header[1]:
        if st.button("📥 1탭 가져오기", type="secondary", use_container_width=True, key="sync_tab4"):
            # 1탭 데이터 동기화
            contract_type = st.session_state.get('contract_type', '개인')
            
            # 3자담보면 소유자만, 아니면 채무자
            if contract_type == "3자담보":
                st.session_state['malso_holder_name'] = st.session_state.get('t1_owner_name', '')
                st.session_state['malso_holder_addr'] = st.session_state.get('t1_owner_addr', '')
            else:
                st.session_state['malso_holder_name'] = st.session_state.get('t1_debtor_name', '')
                st.session_state['malso_holder_addr'] = st.session_state.get('t1_debtor_addr', '')
            
            # 부동산 표시
            st.session_state['malso_estate_detail'] = st.session_state.get('estate_text', '')
            
            st.success("✅ 1탭 정보를 불러왔습니다!")
            st.rerun()
    with col_header[2]:
        if st.button("🔄 초기화", type="secondary", use_container_width=True, key="reset_tab4"):
            st.session_state['malso_type'] = "근저당권"
            st.session_state['malso_obligor_corp'] = ''
            st.session_state['malso_obligor_rep'] = ''
            st.session_state['malso_obligor_id'] = ''
            st.session_state['malso_obligor_addr'] = ''
            st.session_state['malso_holder_name'] = ''
            st.session_state['malso_holder_addr'] = ''
            st.session_state['malso_cause_date'] = datetime.now().date()
            st.session_state['malso_estate_detail'] = ''
            st.session_state['malso_cancel_text'] = ''
            st.session_state['malso_from_branch'] = ''
            st.session_state['malso_to_branch'] = ''
            st.success("✅ 초기화되었습니다!")
            st.rerun()
    
    st.markdown("---")
    
    # 1. 말소 유형 선택 (좌우 꽉 차게)
    st.markdown("#### 📋 말소 유형 선택")
    
    if 'malso_type' not in st.session_state:
        st.session_state['malso_type'] = "근저당권"
    
    malso_type_cols = st.columns(3)
    with malso_type_cols[0]:
        if st.button("근저당권", 
                     type="primary" if st.session_state['malso_type']=="근저당권" else "secondary",
                     use_container_width=True,
                     key="btn_malso_type_1"):
            st.session_state['malso_type'] = "근저당권"
            st.rerun()
    with malso_type_cols[1]:
        if st.button("질권",
                     type="primary" if st.session_state['malso_type']=="질권" else "secondary",
                     use_container_width=True,
                     key="btn_malso_type_2"):
            st.session_state['malso_type'] = "질권"
            st.rerun()
    with malso_type_cols[2]:
        if st.button("전세권",
                     type="primary" if st.session_state['malso_type']=="전세권" else "secondary",
                     use_container_width=True,
                     key="btn_malso_type_3"):
            st.session_state['malso_type'] = "전세권"
            st.rerun()
    
    st.info(f"✅ 선택된 유형: **{st.session_state['malso_type']}말소**")
    st.markdown("---")
    
    # 2. 입력 정보
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        st.markdown("#### 1️⃣ 등기의무자 (권리자)")
        with st.container(border=True):
            st.text_input("법인명", key="malso_obligor_corp", placeholder="주식회사티플레인대부")
            st.text_input("대표이사", key="malso_obligor_rep", placeholder="윤웅원")
            st.text_input("법인등록번호", key="malso_obligor_id", placeholder="110111-7350161")
            st.text_area("주소", key="malso_obligor_addr", height=80,
                        placeholder="서울특별시 마포구 삼개로 16, 2신관 1층 103호")
    
    with col_input2:
        st.markdown("#### 2️⃣ 등기권리자 (의무자)")
        with st.container(border=True):
            st.text_input("성명", key="malso_holder_name", placeholder="홍길동")
            st.text_area("주소", key="malso_holder_addr", height=100,
                        placeholder="서울특별시 송파구...")
    
    st.markdown("---")
    
    # 3. 등기원인 및 부동산 정보
    col_info = st.columns(2)
    with col_info[0]:
        st.markdown("#### 3️⃣ 등기원인과 그 년월일")
        if 'malso_cause_date' not in st.session_state:
            st.session_state['malso_cause_date'] = datetime.now().date()
        st.date_input("등기원인일", value=st.session_state['malso_cause_date'], key="malso_cause_date")
        st.text_input("등기원인", value="해지", key="malso_cause")
    
    with col_info[1]:
        st.markdown("#### 4️⃣ 등기목적")
        malso_purpose = f"{st.session_state['malso_type']}말소"
        st.text_input("등기목적", value=malso_purpose, disabled=True)
    
    st.markdown("#### 5️⃣ 부동산의 표시")
    with st.container(border=True):
        st.text_area(
            "부동산 상세 (등기부등본에서 복사)",
            key="malso_estate_detail",
            height=200,
            placeholder="1동의 건물의 표시\n서울특별시 송파구 문정동 150\n..."
        )
    
    st.markdown("#### 6️⃣ 말소할 등기")
    st.text_input(
        "말소할 등기 (접수번호 등)",
        key="malso_cancel_text",
        placeholder="2025년09월30일 접수 제5201489호(으)로 경료한 근저당권설정"
    )
    
    st.markdown("---")
    
    # 4. 이관 정보
    st.markdown("#### 🏦 이관 정보 (이관증명서용)")
    col_transfer = st.columns(2)
    with col_transfer[0]:
        st.text_input("이관 전", key="malso_from_branch", placeholder="취급지점명")
    with col_transfer[1]:
        st.text_input("이관 후", key="malso_to_branch", placeholder="본점")
    
    st.markdown("---")
    
    # 5. 대리인 정보
    st.markdown("#### 👤 대리인 정보")
    col_agent = st.columns(3)
    with col_agent[0]:
        st.text_input("법무법인명", key="malso_agent_corp", value="법무법인 시화")
    with col_agent[1]:
        st.text_input("담당변호사", key="malso_agent_name", value="최장섭")
    with col_agent[2]:
        st.text_input("전화번호", key="malso_agent_phone", value="02-522-4100")
    
    st.text_input("대리인 주소", key="malso_agent_addr",
                 value="서울특별시 서초구 법원로3길6-9, 301호(서초동,법조빌딩)")
    
    st.markdown("---")
    
    # 6. PDF 생성 버튼 (4종)
    st.markdown("### 📥 문서 생성")
    
    col_pdf = st.columns(4)
    with col_pdf[0]:
        if st.button("📄 자필서명정보", use_container_width=True, key="pdf_signature"):
            st.info("💡 자필서명정보 PDF 생성 기능은 추후 구현 예정입니다.")
    with col_pdf[1]:
        if st.button("📄 위임장", use_container_width=True, key="pdf_power"):
            st.info("💡 위임장 PDF 생성 기능은 추후 구현 예정입니다.")
    with col_pdf[2]:
        if st.button("📄 해지증서", use_container_width=True, key="pdf_termination"):
            st.info("💡 해지증서 PDF 생성 기능은 추후 구현 예정입니다.")
    with col_pdf[3]:
        if st.button("📄 이관증명서", use_container_width=True, key="pdf_transfer"):
            st.info("💡 이관증명서 PDF 생성 기능은 추후 구현 예정입니다.")
    
    # 안내 메시지
    st.info("💡 **사용 방법**: '📥 1탭 가져오기' 버튼을 눌러 소유자 정보와 부동산 표시를 자동으로 불러올 수 있습니다.")

# 하단 푸터
st.markdown("---")
st.markdown("""<div style='text-align: center; color: #6c757d; padding: 20px; background-color: white; border-radius: 10px; border: 2px solid #e1e8ed;'>
    <p style='margin: 0; font-size: 1rem; color: #00428B;'><strong>DG-Form 등기온 전자설정 자동화 시스템 | 법무법인 시화</strong></p>
    <p style='margin: 5px 0 0 0; font-size: 0.85rem; color: #6c757d;'>부동산 등기는 등기온</p></div>""", unsafe_allow_html=True)