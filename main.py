```python
import streamlit as st
import pandas as pd
from datetime import date

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="서울 기온 랭킹",
    page_icon="🌡️",
    layout="centered"
)

# --------------------------------------------------
# 데이터 불러오기
# 반드시 seoul.csv 사용
# --------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("seoul.csv")

    # 날짜 앞에 있을 수 있는 탭/공백 제거
    df["날짜"] = (
        df["날짜"]
        .astype(str)
        .str.strip()
    )

    df["날짜"] = pd.to_datetime(
        df["날짜"],
        errors="coerce"
    )

    # 필요한 컬럼만 사용
    df = df.dropna(
        subset=["날짜", "평균기온"]
    ).copy()

    # 날짜에서 월/일 추출
    df["월"] = df["날짜"].dt.month
    df["일"] = df["날짜"].dt.day

    return df


df = load_data()

# --------------------------------------------------
# 제목
# --------------------------------------------------
st.markdown(
    """
    <div style="
        text-align:center;
        padding: 10px 0 5px 0;
    ">
        <div style="
            font-size: 3rem;
            line-height: 1;
        ">🌡️</div>

        <h1 style="
            margin-bottom: 0;
            font-size: 2.2rem;
        ">
            서울 기온 랭킹
        </h1>

        <p style="
            color: #777;
            font-size: 1.05rem;
            margin-top: 8px;
        ">
            원하는 기간을 선택하면<br>
            역대 같은 기간 중 얼마나 더웠거나 추웠는지 알려드려요.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# --------------------------------------------------
# 날짜 선택
# --------------------------------------------------
st.markdown("### 📅 기간을 선택하세요")

col1, col2 = st.columns(2)

min_date = df["날짜"].min().date()
max_date = df["날짜"].max().date()

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

# --------------------------------------------------
# 날짜 검증
# --------------------------------------------------
if start_date > end_date:
    st.error("⚠️ 종료 날짜는 시작 날짜보다 빠를 수 없습니다.")
    st.stop()

# 선택 기간의 길이
period_length = (end_date - start_date).days + 1

# --------------------------------------------------
# 선택한 기간의 실제 평균기온 계산
# --------------------------------------------------
selected_mask = (
    (df["날짜"] >= pd.Timestamp(start_date)) &
    (df["날짜"] <= pd.Timestamp(end_date))
)

selected_data = df.loc[selected_mask].copy()

if selected_data.empty:
    st.warning("선택한 기간에 데이터가 없습니다.")
    st.stop()

selected_mean = selected_data["평균기온"].mean()

# --------------------------------------------------
# 역대 '동일 월/일 구간' 생성
#
# 예:
# 7/1 ~ 7/7 선택
# → 과거 모든 연도의 7/1 ~ 7/7 평균기온 계산
# --------------------------------------------------
start_month = start_date.month
start_day = start_date.day

end_month = end_date.month
end_day = end_date.day

# 선택 기간의 월/일을 기준으로 각 연도의 동일 기간을 비교
# 12월 → 1월처럼 연도를 넘어가는 기간도 처리
cross_year = (
    (start_month, start_day) > (end_month, end_day)
)

years = sorted(df["날짜"].dt.year.unique())

historical_periods = []

for year in years:

    # 시작일
    try:
        period_start = pd.Timestamp(
            year=year,
            month=start_month,
            day=start_day
        )
    except ValueError:
        continue

    # 종료일
    end_year = year + 1 if cross_year else year

    try:
        period_end = pd.Timestamp(
            year=end_year,
            month=end_month,
            day=end_day
        )
    except ValueError:
        continue

    # 해당 연도 기간 데이터
    mask = (
        (df["날짜"] >= period_start) &
        (df["날짜"] <= period_end)
    )

    period_data = df.loc[mask]

    # 선택 기간과 동일한 날짜 수가 확보된 경우만 비교
    if len(period_data) == period_length:

        period_mean = period_data["평균기온"].mean()

        historical_periods.append({
            "연도": year,
            "평균기온": period_mean
        })

historical = pd.DataFrame(historical_periods)

if historical.empty:
    st.warning("비교할 역대 데이터가 충분하지 않습니다.")
    st.stop()

# --------------------------------------------------
# 순위 계산
#
# 평균기온이 높을수록 '더운 기간' 기준으로 1위
# --------------------------------------------------
historical = historical.sort_values(
    "평균기온",
    ascending=False
).reset_index(drop=True)

# 공동 순위 적용
historical["순위"] = (
    historical["평균기온"]
    .rank(method="min", ascending=False)
    .astype(int)
)

# 선택한 기간이 포함된 연도 찾기
selected_year = start_date.year

current_rows = historical[
    historical["연도"] == selected_year
]

# 선택 기간과 같은 연도의 데이터가 있으면 사용
if not current_rows.empty:
    current_rank = int(current_rows.iloc[0]["순위"])
else:
    # 현재 기간이 비교 대상에 없으면
    # 가장 가까운 실제 계산값을 별도로 계산
    current_rank = (
        historical["평균기온"]
        .gt(selected_mean)
        .sum() + 1
    )

total_years = len(historical)

# --------------------------------------------------
# 분위 계산
# --------------------------------------------------
percentile = (
    (total_years - current_rank)
    / total_years
) * 100

# --------------------------------------------------
# 메인 결과
# --------------------------------------------------
st.markdown("### 🔎 분석 결과")

st.markdown(
    f"""
    <div style="
        background: linear-gradient(
            135deg,
            #f8fbff 0%,
            #eef6ff 100%
        );
        border-radius: 20px;
        padding: 30px 20px;
        text-align: center;
        border: 1px solid #e5edf7;
        margin: 15px 0 20px 0;
    ">

        <div style="
            color:#6b7280;
            font-size:0.95rem;
            margin-bottom:8px;
        ">
            {start_date.strftime("%Y.%m.%d")}
            ~
            {end_date.strftime("%Y.%m.%d")}
        </div>

        <div style="
            font-size:1.05rem;
            color:#374151;
            margin-bottom:5px;
        ">
            역대 같은 기간 중
        </div>

        <div style="
            font-size:3.6rem;
            font-weight:800;
            line-height:1.15;
            margin:5px 0;
        ">
            {current_rank:,}위
        </div>

        <div style="
            font-size:1rem;
            color:#6b7280;
        ">
            더운 기간 기준 · 총 {total_years:,}개 기간 비교
        </div>

    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# 핵심 지표
# --------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "평균기온",
        f"{selected_mean:.1f} °C"
    )

with c2:
    st.metric(
        "비교 연도",
        f"{total_years:,}년"
    )

with c3:
    st.metric(
        "상위",
        f"{percentile:.1f}%"
    )

# --------------------------------------------------
# 한줄 해석
# --------------------------------------------------
if current_rank <= max(1, int(total_years * 0.05)):
    message = "🔥 역대급으로 더운 기간에 속합니다."
elif current_rank <= max(1, int(total_years * 0.20)):
    message = "☀️ 상당히 더운 기간에 속합니다."
elif current_rank <= max(1, int(total_years * 0.50)):
    message = "🌤️ 평년보다 비교적 따뜻한 기간입니다."
elif current_rank <= max(1, int(total_years * 0.80)):
    message = "🌥️ 비교적 선선한 편입니다."
else:
    message = "❄️ 역대 기준으로 상당히 선선한 기간입니다."

st.info(message)

# --------------------------------------------------
# 상세 정보
# --------------------------------------------------
with st.expander("📊 역대 비교 데이터 보기"):

    display_df = historical.copy()

    display_df["평균기온"] = (
        display_df["평균기온"]
        .round(1)
    )

    display_df = display_df[
        ["순위", "연도", "평균기온"]
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

# --------------------------------------------------
# 안내
# --------------------------------------------------
st.caption(
    "※ 평균기온을 기준으로 같은 달·일 범위의 역대 기간과 비교합니다. "
    "데이터가 완전하지 않은 연도는 비교에서 제외됩니다."
)
```
