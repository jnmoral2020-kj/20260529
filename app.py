import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(
    page_title="수업 활동 점검 대시보드",
    page_icon="📊",
    layout="wide"
)

# 2. CSS 스타일 적용 (오류 수정 완료)
st.markdown("""
    <style>
    .main-title { font-size: 28px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .sub-title { font-size: 14px; color: #6B7280; margin-bottom: 25px; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# 3. 사이드바 구성
with st.sidebar:
    st.header("📥 데이터 관리")
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])
    
    st.divider()
    st.header("🔒 개인정보 보호")
    mask_name = st.checkbox("학생 이름 숨기기", value=False)
    
    st.divider()
    st.info("이 대시보드는 데이터를 서버에 저장하지 않습니다.")

# 4. 메인 대시보드 화면
st.markdown('<p class="main-title">📊 수업 활동 점검 대시보드</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">학생 활동 데이터를 분석하여 미제출 현황과 요약을 제공합니다.</p>', unsafe_allow_html=True)

if uploaded_file:
    # 데이터 로드
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except:
        df = pd.read_csv(uploaded_file, encoding='cp949')

    # 필수 컬럼 체크
    required_cols = ['반', '모둠', '학번', '이름', '점수', '제출여부']
    if not all(col in df.columns for col in required_cols):
        st.error(f"컬럼명이 일치하지 않습니다. 필요 컬럼: {', '.join(required_cols)}")
    else:
        # 이름 마스킹 처리
        if mask_name:
            df['이름'] = df['학번'].astype(str).str[-2:] + "번 학생"

        # 필터 레이아웃
        col1, col2 = st.columns(2)
        with col1:
            sel_class = st.selectbox("🏫 반 선택", ["전체"] + sorted(df['반'].unique().tolist()))
        with col2:
            sel_group = st.selectbox("👥 모둠 선택", ["전체"] + sorted(df['모둠'].unique().tolist()))

        # 데이터 필터링
        view_df = df.copy()
        if sel_class != "전체":
            view_df = view_df[view_df['반'] == sel_class]
        if sel_group != "전체":
            view_df = view_df[view_df['모둠'] == sel_group]

        # 통계 계산
        total = len(view_df)
        submitted = len(view_df[view_df['제출여부'] == '제출'])
        rate = (submitted / total * 100) if total > 0 else 0
        avg = view_df[view_df['제출여부'] == '제출']['점수'].mean() if submitted > 0 else 0

        # 지표 표시
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("대상 인원", f"{total}명")
        m2.metric("제출률", f"{rate:.1f}%")
        m3.metric("평균 점수", f"{avg:.1f}점")
        m4.metric("미제출", f"{total - submitted}명")

        st.divider()

        # 차트 및 명단
        c1, c2 = st.columns([3, 2])
        
        with c1:
            st.subheader("모둠별 평균 점수")
            grp_data = view_df.groupby('모둠')['점수'].mean().reset_index()
            fig = px.bar(grp_data, x='모둠', y='점수', color_discrete_sequence=['#3B82F6'])
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("⚠️ 체크 대상")
            unsub = view_df[view_df['제출여부'] == '미제출'][['학번', '이름']]
            st.write("**미제출 학생**")
            st.dataframe(unsub, hide_index=True, use_container_width=True)
            
            low_score = view_df[(view_df['제출여부'] == '제출') & (view_df['점수'] < 60)][['이름', '점수']]
            st.write("**보완 필요 (60점 미만)**")
            st.dataframe(low_score, hide_index=True, use_container_width=True)

        st.divider()

        # 회의용 요약
        st.subheader("📝 회의용 브리핑 요약")
        summary = f"""[수업 활동 결과 보고]
- 대상: {sel_class} / {sel_group}
- 제출 현황: {total}명 중 {submitted}명 제출 ({rate:.1f}%)
- 주요 미제출자: {', '.join(unsub['이름'].tolist()) if not unsub.empty else '없음'}
- 피드백 대상: {len(low_score)}명
- 분석 결과: 제출자 평균 {avg:.1f}점으로 전반적 성취도 양호함."""
        
        st.text_area("회의록 복사용", value=summary, height=150)

else:
    st.warning("데이터가 없습니다. 샘플 파일을 참고하여 업로드해 주세요.")
    
    # 가이드용 샘플 데이터 제공
    sample = pd.DataFrame({
        "반": ["1반"]*3 + ["2반"]*3,
        "모둠": ["1모둠", "1모둠", "2모둠"]*2,
        "학번": [10101, 10102, 10103, 10201, 10202, 10203],
        "이름": ["학생A", "학생B", "학생C", "학생D", "학생E", "학생F"],
        "점수": [90, 50, 0, 85, 95, 0],
        "제출여부": ["제출", "제출", "미제출", "제출", "제출", "미제출"]
    })
    st.write("### 샘플 파일 예시 (CSV)")
    st.dataframe(sample)
