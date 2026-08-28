import streamlit as st
import pandas as pd
from datetime import date

# ============================================
# 페이지 설정
# ============================================

st.set_page_config(
    page_title="서울 기온 랭킹",
    page_icon="🌡️",
    layout="centered"
)

# ============================================
# 데이터 불러오기
# ============================================

@st.cache_data
def load_data():

    # 반드시 seoul.csv 사용
    df = pd.read_csv("seoul.csv")

    # 날짜 앞에 포함되어 있는 탭/공백 제거
    df["날짜"] = (
        df["날짜"]
        .astype(str)
        .str.strip()
    )

    # 날짜 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"],
        errors="coerce"
    )

    # 숫자형 변환
    for column in ["평균기온", "최저기온", "최고기온"]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # 날짜 또는 평균기온이 없는 행 제거
    df = df.dropna(
        subset=["날짜", "평균기온"]
    ).copy()

    # 연 / 월 / 일을 추가
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일"] = df["날짜"].dt.day

    return df


df = load_data()

# ============================================
# 제목
# ============================================

st.title("🌡️ 서울 기온 랭킹")

st.write("선택한 기간은 역대 몇 번째로 더웠을까요?")

st.write("")

# ============================================
# 데이터 기간 표시
# ============================================

min_date = df["날짜"].min().date()
max_date = df["날짜"].max().date()

st.caption(
    f"서울 기상 관측 데이터 · "
    f"{min_date.strftime('%Y.%m.%d')} ~ "
    f"{max_date.strftime('%Y.%m.%d')}"
)

st.divider()

# ============================================
# 날짜 선택
# ============================================

st.subheader("📅 비교할 기간을 선택하세요")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "시작 날짜",
        value=date(2024, 7, 1),
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD"
    )

with col2:
    end_date = st.date_input(
        "종료 날짜",
        value=date(2024, 7, 7),
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD"
    )

# ============================================
# 날짜 오류 확인
# ============================================

if start_date > end_date:

    st.error(
        "⚠️ 종료 날짜는 시작 날짜보다 빠를 수 없습니다."
    )

    st.stop()

# ============================================
# 선택한 기간
# ============================================

period_days = (
    end_date - start_date
).days + 1

selected_start = pd.Timestamp(start_date)
selected_end = pd.Timestamp(end_date)

selected = df[
    (df["날짜"] >= selected_start)
    &
    (df["날짜"] <= selected_end)
].copy()

if selected.empty:

    st.error(
        "선택한 기간에 기온 데이터가 없습니다."
    )

    st.stop()

# ============================================
# 선택한 기간의 평균기온
# ============================================

selected_average = selected["평균기온"].mean()

# ============================================
# 역대 동일 기간 비교
#
# 예:
# 2024-07-01 ~ 2024-07-07
#
# → 1908년 7/1~7/7
# → 1909년 7/1~7/7
# → ...
# → 2024년 7/1~7/7
#
# 과 비교
# ============================================

start_month = start_date.month
start_day = start_date.day

end_month = end_date.month
end_day = end_date.day

# 연도를 넘어가는 기간인지 확인
cross_year = (
    (start_month, start_day)
    >
    (end_month, end_day)
)

years = sorted(
    df["연도"].dropna().unique()
)

historical = []

for year in years:

    year = int(year)

    # 해당 연도의 시작 날짜
    try:
        period_start = pd.Timestamp(
            year=year,
            month=start_month,
            day=start_day
        )
    except ValueError:
        continue

    # 12월 → 1월처럼 연도가 넘어가는 경우
    if cross_year:
        period_end_year = year + 1
    else:
        period_end_year = year

    try:
        period_end = pd.Timestamp(
            year=period_end_year,
            month=end_month,
            day=end_day
        )
    except ValueError:
        continue

    # 해당 기간 데이터
    period = df[
        (df["날짜"] >= period_start)
        &
        (df["날짜"] <= period_end)
    ]

    # 날짜가 모두 존재하는 연도만 비교
    if len(period) == period_days:

        average_temperature = (
            period["평균기온"].mean()
        )

        historical.append(
            {
                "연도": year,
                "평균기온": average_temperature
            }
        )

# 데이터프레임 생성
history = pd.DataFrame(historical)

if history.empty:

    st.error(
        "비교할 수 있는 역대 데이터가 없습니다."
    )

    st.stop()

# ============================================
# 순위 계산
# ============================================

history = history.sort_values(
    "평균기온",
    ascending=False
).reset_index(drop=True)

history["순위"] = (
    history["평균기온"]
    .rank(
        method="min",
        ascending=False
    )
    .astype(int)
)

# 선택한 연도의 순위
selected_year = start_date.year

same_year = history[
    history["연도"] == selected_year
]

if not same_year.empty:

    rank = int(
        same_year.iloc[0]["순위"]
    )

else:

    # 선택한 기간이 비교 데이터에 없을 경우
    rank = (
        history["평균기온"]
        .gt(selected_average)
        .sum()
        + 1
    )

total = len(history)

# ============================================
# 순위에 따른 문구
# ============================================

if rank == 1:

    message = "🔥 역대 가장 더운 기간입니다!"

elif rank <= max(1, int(total * 0.05)):

    message = "🔥 역대 최상위권의 더운 기간입니다."

elif rank <= max(1, int(total * 0.20)):

    message = "☀️ 상당히 더운 기간에 속합니다."

elif rank <= max(1, int(total * 0.50)):

    message = "🌤️ 비교적 따뜻한 기간입니다."

elif rank <= max(1, int(total * 0.80)):

    message = "🌥️ 비교적 선선한 기간입니다."

else:

    message = "❄️ 역대 기준으로 상당히 선선한 기간입니다."

# ============================================
# 메인 결과 카드
# ============================================

st.markdown(
    f"""
    <div style="
        margin-top:25px;
        margin-bottom:25px;
        padding:35px 20px;
        border-radius:22px;
        background:linear-gradient(
            135deg,
            #f7fbff,
            #eef5ff
        );
        border:1px solid #e4edf7;
        text-align:center;
    ">

        <div style="
            color:#777;
            font-size:15px;
            margin-bottom:10px;
        ">
            {start_date.strftime('%Y.%m.%d')}
            &nbsp;~&nbsp;
            {end_date.strftime('%Y.%m.%d')}
        </div>

        <div style="
            font-size:18px;
            color:#444;
        ">
            역대 같은 기간 중
        </div>

        <div style="
            font-size:64px;
            font-weight:800;
            margin:5px 0;
        ">
            {rank}위
        </div>

        <div style="
            font-size:17px;
            color:#666;
        ">
            더운 기간 기준 · 총 {total}개 기간 비교
        </div>

        <div style="
            font-size:20px;
            font-weight:600;
            margin-top:18px;
        ">
            {message}
        </div>

    </div>
    """,
    unsafe_allow_html=True
)

# ============================================
# 숫자 카드
# ============================================

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "평균기온",
        f"{selected_average:.1f} °C"
    )

with col2:

    st.metric(
        "기간",
        f"{period_days}일"
    )

with col3:

    percentile = (
        rank / total
    ) * 100

    st.metric(
        "상위",
        f"{percentile:.1f}%"
    )

# ============================================
# 선택 기간의 실제 데이터
# ============================================

st.divider()

st.subheader("🌡️ 선택한 기간")

metric1, metric2, metric3 = st.columns(3)

with metric1:

    st.metric(
        "평균기온",
        f"{selected['평균기온'].mean():.1f} °C"
    )

with metric2:

    st.metric(
        "최고기온",
        f"{selected['최고기온'].max():.1f} °C"
    )

with metric3:

    st.metric(
        "최저기온",
        f"{selected['최저기온'].min():.1f} °C"
    )

# ============================================
# 역대 순위 TOP 10
# ============================================

st.divider()

st.subheader("🏆 역대 더운 기간 TOP 10")

top10 = history.head(10).copy()

top10["평균기온"] = (
    top10["평균기온"]
    .round(1)
)

top10 = top10[
    ["순위", "연도", "평균기온"]
]

top10 = top10.rename(
    columns={
        "순위": "순위",
        "연도": "연도",
        "평균기온": "평균기온 (°C)"
    }
)

st.dataframe(
    top10,
    use_container_width=True,
    hide_index=True
)

# ============================================
# 전체 역대 데이터
# ============================================

with st.expander("📊 전체 역대 순위 보기"):

    all_history = history.copy()

    all_history["평균기온"] = (
        all_history["평균기온"]
        .round(1)
    )

    all_history = all_history[
        ["순위", "연도", "평균기온"]
    ]

    all_history = all_history.rename(
        columns={
            "평균기온": "평균기온 (°C)"
        }
    )

    st.dataframe(
        all_history,
        use_container_width=True,
        hide_index=True
    )

# ============================================
# 데이터 설명
# ============================================

st.divider()

st.caption(
    "📌 순위는 선택한 날짜 범위와 동일한 월·일 범위를 "
    "역대 각 연도와 비교하여 계산합니다."
)

st.caption(
    "📌 평균기온이 높을수록 더운 기간 순위가 높습니다."
)

st.caption(
    "📌 선택 기간의 날짜가 완전히 존재하지 않는 연도는 "
    "비교에서 제외합니다."
)
