import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정 및 디자인 (전문적인 교사용 대시보드 톤앤매너)
st.set_page_config(
    page_title="수업 활동 점검 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사용자 정의 CSS (깔끔한 폰트 및 스타일링)
st.markdown("""
    <style>
    .main-title { font-size: 28px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .sub-title { font-size: 14px; color: #6B7280; margin-bottom: 25px; }
    .metric-box { padding: 15px; background-color: #F3F4F6; border-radius: 8px; }
    </style>
    """, unsafe_index=True)

# 2. 사이드바 - 파일 업로드 및 설정
with st.sidebar:
    st.markdown("## 📥 데이터 업로드")
    uploaded_file = st.file_uploader("학생 활동 결과 CSV 파일을 업로드하세요.", type=["csv"])
    
    st.markdown("---")
    st.markdown("## 🔒 개인정보 보호 설정")
    mask_student_name = st.checkbox("학생 이름 숨기기 (학번만 표시)", value=False)
    
    st.markdown("---")
    st.info("💡 **안전 원칙**: 본 앱은 로컬 환경에서 실행되거나 서버에 데이터를 저장하지 않으므로 학생 개인정보가 외부로 유출되지 않습니다.")

# 3. 메인 화면 타이틀
st.markdown('<p class="main-title">📊 수업 활동 점검 대시보드</p>', unsafe_index=True)
st.markdown('<p class="sub-title">학생들의 모둠별 참여도와 미제출 현황을 한눈에 파악하고 회의용 요약을 생성합니다.</p>', unsafe_index=True)

# 4. 데이터 로드 및 처리
if uploaded_file is not None:
    # 데이터 읽기 (인코딩 문제는 한국어 환경을 고려해 cp949/utf-8 호환성 확보)
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding='cp949')
        
    # 필수 컬럼 존재 여부 확인 및 예시 매핑 (반, 모둠, 학번, 이름, 점수, 제출여부)
    # 실제 데이터 구조에 맞게 컬럼명을 유연하게 변경할 수 있도록 처리하는 것이 좋습니다.
    required_cols = ['반', '모둠', '학번', '이름', '점수', '제출여부']
    
    # 셈플 검증 (사용자 편의를 위해 컬럼명이 다르면 매핑 가이드 제공)
    if not all(col in df.columns for col in required_cols):
        st.error(f"CSV 파일에 다음 컬럼이 포함되어 있어야 합니다: {', '.join(required_cols)}")
        st.info("💡 팁: 컬럼명을 '반', '모둠', '학번', '이름', '점수', '제출여부'로 맞춰주세요.")
    else:
        # 개인정보 보호 처리
        if mask_student_name:
            df['이름'] = df['학번'].astype(str) + " (학생)"

        # --- 필터 영역 ---
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            class_options = ["전체"] + sorted(df['반'].unique().tolist())
            selected_class = st.selectbox("🏫 반 선택", class_options)
        with col_f2:
            group_options = ["전체"] + sorted(df['모둠'].unique().tolist())
            selected_group = st.selectbox("👥 모둠 선택", group_options)
            
        # 데이터 필터링 적용
        filtered_df = df.copy()
        if selected_class != "전체":
            filtered_df = filtered_df[filtered_df['반'] == selected_class]
        if selected_group != "전체":
            filtered_df = filtered_df[filtered_df['모둠'] == selected_group]

        # --- 핵심 지표 (Metrics) ---
        total_students = len(filtered_df)
        submitted_students = len(filtered_df[filtered_df['제출여부'] == '제출'])
        submission_rate = (submitted_students / total_students * 100) if total_students > 0 else 0
        avg_score = filtered_df[filtered_df['제출여부'] == '제출']['점수'].mean() if submitted_students > 0 else 0
        unsubmitted_count = total_students - submitted_students

        st.markdown("### 📈 주요 현황")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총원", f"{total_students}명")
        m2.metric("제출률", f"{submission_rate:.1f}%")
        m3.metric("평균 점수 (제출자 기준)", f"{avg_score:.1f}점")
        m4.metric("미제출 학생 수", f"{unsubmitted_count}명", delta=f"-{unsubmitted_count}" if unsubmitted_count > 0 else "0", delta_color="inverse")

        st.markdown("---")

        # --- 시각화 및 명단 분할 ---
        col_chart, col_list = st.columns([3, 2])
        
        with col_chart:
            st.markdown("### 📊 모둠별 평균 점수 및 제출 건수")
            # 모둠별 통계 데이터 생성
            group_stats = filtered_df.groupby('모둠').agg(
                평균점수=('점수', 'mean'),
                제출자수=('제출여부', lambda x: (x == '제출').sum())
            ).reset_index()
            
            # Plotly 막대그래프 (교사용 톤앤매너: 파란색 계열)
            fig = px.bar(group_stats, x='모둠', y='평균점수', 
                         title='모둠별 평균 점수 현황',
                         labels={'평균점수': '평균 점수 (점)'},
                         color_discrete_sequence=['#1E3A8A'])
            fig.update_layout(plot_bgcolor="white", margin=dict(t=40, b=40, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

        with col_list:
            st.markdown("### ⚠️ 미제출 및 보완 필요 대상")
            unsubmitted_list = filtered_df[filtered_df['제출여부'] == '미제출'][['반', '모둠', '학번', '이름']]
            
            # 보완 필요 기준 (예: 점수 60점 미만인 제출자)
            review_needed_list = filtered_df[(filtered_df['제출여부'] == '제출') & (filtered_df['점수'] < 60)][['반', '모둠', '학번', '이름', '점수']]
            
            st.markdown("**🚨 미제출 학생 명단**")
            if not unsubmitted_list.empty:
                st.dataframe(unsubmitted_list, use_container_width=True, hide_index=True)
            else:
                st.success("모든 학생이 제출했습니다! 🎉")
                
            st.markdown("**🟠 피드백 필요 학생 명단 (60점 미만)**")
            if not review_needed_list.empty:
                st.dataframe(review_needed_list, use_container_width=True, hide_index=True)
            else:
                st.info("보완이 필요한 학생이 없습니다.")

        st.markdown("---")

        # --- 회의용 요약 생성 (핵심 기능 및 사용자 여정 반영) ---
        st.markdown("### 📝 학년부/교과협의회 회의용 요약 브리핑")
        
        # 간단한 자동 요약 텍스트 생성
        summary_text = f"""[수업 활동 결과 요약 브리핑]
- 확인 대상: 반({selected_class}), 모둠({selected_group})
- 전체 제출률: {submission_rate:.1f}% ({total_students}명 중 {submitted_students}명 제출)
- 제출자 평균 점수: {avg_score:.1f}점
- 미제출 학생: {unsubmitted_count}명 ({', '.join(unsubmitted_list['이름'].tolist()) if unsubmitted_count > 0 else '없음'})
- 피드백 필요 대상: {len(review_needed_list)}명 ({', '.join(review_needed_list['이름'].tolist()) if not review_needed_list.empty else '없음'})
- 특이사항: 모둠별 최고 평균 점수는 {group_stats['평균점수'].max():.1f}점이며, 최저 평균 점수는 {group_stats['평균점수'].min():.1f}점입니다.
"""
        st.text_area("아래 내용을 복사하여 회의록이나 주간 보고에 활용하세요.", value=summary_text, height=180)
        
        # 향후 추가 기능 맛보기: 다운로드 버튼 구현
        st.download_button(
            label="💾 회의용 요약 텍스트 다운로드",
            data=summary_text,
            file_name=f"수업활동_요약_{selected_class}.txt",
            mime="text/plain"
        )

else:
    # 파일이 업로드되지 않았을 때 보여줄 가이드 UI
    st.info("👈 왼쪽 사이드바에서 학생 활동 결과 CSV 파일을 업로드해주세요.")
    
    # 교사들의 빠른 테스트를 위한 샘플 데이터 다운로드 기능 제공
    st.markdown("### 📄 테스트용 샘플 CSV 구조 예시")
    sample_data = pd.DataFrame({
        "반": ["1반", "1반", "1반", "2반", "2반", "2반"],
        "모둠": ["1모둠", "1모둠", "2모둠", "1모둠", "1모둠", "2모둠"],
        "학번": [10101, 10102, 10103, 10201, 10202, 10203],
        "이름": ["김철수", "이영희", "박민수", "최수진", "정우성", "한지민"],
        "점수": [85, 45, 0, 90, 95, 0],
        "제출여부": ["제출", "제출", "미제출", "제출", "제출", "미제출"]
    })
    st.dataframe(sample_data)
    
    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8-sig') # 엑셀 깨짐 방지용 utf-8-sig
        
    csv_sample = convert_df(sample_data)
    st.download_button(
        label="📥 샘플 CSV 다운로드 받기",
        data=csv_sample,
        file_name="sample_student_activity.csv",
        mime="text/csv",
    )
