```python
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="서울 기온 랭킹",
    page_icon="🌡️",
    layout="wide"
)


# ---------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------

@st.cache_data
def load_data():

    df = pd.read_csv("seoul.csv")

    # 컬럼명 정리
    df.columns = df.columns.astype(str).str.strip()

    # 날짜 앞의 탭과 공백 제거
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

    # 기온 숫자 변환
    for col in ["평균기온", "최저기온", "최고기온"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # 날짜와 평균기온이 없는 행 제거
    df = df.dropna(
        subset=["날짜", "평균기온"]
    ).copy()

    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일"] = df["날짜"].dt.day

    return df


try:
    df = load_data()

except Exception as e:

    st.error("seoul.csv를 불러오지 못했습니다.")
    st.write("main.py와 seoul.csv가 같은 폴더에 있는지 확인하세요.")
    st.write(e)
    st.stop()


# ---------------------------------------------------------
# 제목
# ---------------------------------------------------------

st.title("🌡️ 서울 기온 랭킹")

st.write(
    "원하는 날짜를 선택하면 서울의 역대 같은 기간과 비교해 "
    "얼마나 더웠거나 추웠는지 알려드립니다."
)

st.caption(
    "서울 기상 관측 데이터 | "
    + df["날짜"].min().strftime("%Y.%m.%d")
    + " ~ "
    + df["날짜"].max().strftime("%Y.%m.%d")
)

st.divider()


# ---------------------------------------------------------
# 날짜 선택
# ---------------------------------------------------------

st.subheader("📅 비교할 기간")

min_date = df["날짜"].min().date()
max_date = df["날짜"].max().date()

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


if start_date > end_date:

    st.error("종료 날짜는 시작 날짜보다 빠를 수 없습니다.")

    st.stop()


# ---------------------------------------------------------
# 선택 기간
# ---------------------------------------------------------

period_days = (
    end_date - start_date
).days + 1

selected = df[
    (df["날짜"] >= pd.Timestamp(start_date))
    &
    (df["날짜"] <= pd.Timestamp(end_date))
].copy()


if selected.empty:

    st.warning("선택한 기간의 데이터가 없습니다.")

    st.stop()


# ---------------------------------------------------------
# 선택 기간 기온
# ---------------------------------------------------------

selected_average = selected["평균기온"].mean()

selected_high = None
selected_low = None

if "최고기온" in selected.columns:
    selected_high = selected["최고기온"].max()

if "최저기온" in selected.columns:
    selected_low = selected["최저기온"].min()


# ---------------------------------------------------------
# 역대 동일 기간 계산
# ---------------------------------------------------------

start_month = start_date.month
start_day = start_date.day

end_month = end_date.month
end_day = end_date.day

# 12월~1월처럼 연도를 넘어가는 기간도 처리
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

    try:

        period_start = pd.Timestamp(
            year=year,
            month=start_month,
            day=start_day
        )

    except ValueError:

        continue


    if cross_year:

        end_year = year + 1

    else:

        end_year = year


    try:

        period_end = pd.Timestamp(
            year=end_year,
            month=end_month,
            day=end_day
        )

    except ValueError:

        continue


    period = df[
        (df["날짜"] >= period_start)
        &
        (df["날짜"] <= period_end)
    ].copy()


    # 기간의 모든 날짜가 있는 연도만 사용
    if len(period) == period_days:

        historical.append(
            {
                "연도": year,
                "평균기온": period["평균기온"].mean()
            }
        )


history = pd.DataFrame(historical)


if history.empty:

    st.error("비교할 수 있는 역대 데이터가 없습니다.")

    st.stop()


# ---------------------------------------------------------
# 더운 순위
# ---------------------------------------------------------

hot_history = history.sort_values(
    "평균기온",
    ascending=False
).reset_index(drop=True)

hot_history["순위"] = range(
    1,
    len(hot_history) + 1
)


# ---------------------------------------------------------
# 추운 순위
# ---------------------------------------------------------

cold_history = history.sort_values(
    "평균기온",
    ascending=True
).reset_index(drop=True)

cold_history["순위"] = range(
    1,
    len(cold_history) + 1
)


# ---------------------------------------------------------
# 선택 기간의 더운 순위
# ---------------------------------------------------------

selected_year = start_date.year

hot_same_year = hot_history[
    hot_history["연도"] == selected_year
]


if not hot_same_year.empty:

    hot_rank = int(
        hot_same_year.iloc[0]["순위"]
    )

else:

    hot_rank = (
        hot_history["평균기온"]
        .gt(selected_average)
        .sum()
        + 1
    )


# ---------------------------------------------------------
# 선택 기간의 추운 순위
# ---------------------------------------------------------

cold_same_year = cold_history[
    cold_history["연도"] == selected_year
]


if not cold_same_year.empty:

    cold_rank = int(
        cold_same_year.iloc[0]["순위"]
    )

else:

    cold_rank = (
        cold_history["평균기온"]
        .lt(selected_average)
        .sum()
        + 1
    )


total_periods = len(history)


# ---------------------------------------------------------
# 역대 평균과 비교
# ---------------------------------------------------------

historical_average = history["평균기온"].mean()

difference = (
    selected_average
    - historical_average
)


# ---------------------------------------------------------
# 화면 결과
# ---------------------------------------------------------

st.divider()

st.subheader("🏆 분석 결과")

st.write(
    start_date.strftime("%Y.%m.%d")
    + " ~ "
    + end_date.strftime("%Y.%m.%d")
    + " · "
    + str(period_days)
    + "일"
)


# ---------------------------------------------------------
# 순위 카드
# ---------------------------------------------------------

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "🔥 역대 더운 순위",
        str(hot_rank) + "위",
        "총 " + str(total_periods) + "개 기간"
    )


with col2:

    st.metric(
        "❄️ 역대 추운 순위",
        str(cold_rank) + "위",
        "총 " + str(total_periods) + "개 기간"
    )


# ---------------------------------------------------------
# 한줄 평가
# ---------------------------------------------------------

if hot_rank <= max(1, int(total_periods * 0.1)):

    st.success(
        "🔥 역대 기준으로 매우 더운 기간입니다."
    )

elif hot_rank <= max(1, int(total_periods * 0.3)):

    st.info(
        "☀️ 역대 기준으로 따뜻한 편입니다."
    )

elif cold_rank <= max(1, int(total_periods * 0.1)):

    st.info(
        "🥶 역대 기준으로 매우 추운 기간입니다."
    )

elif cold_rank <= max(1, int(total_periods * 0.3)):

    st.info(
        "❄️ 역대 기준으로 추운 편입니다."
    )

else:

    st.info(
        "🌤️ 역대 평균에 가까운 기온입니다."
    )


# ---------------------------------------------------------
# 기온 정보
# ---------------------------------------------------------

st.subheader("🌡️ 선택 기간의 기온")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "평균기온",
        f"{selected_average:.1f} °C"
    )


with col2:

    if selected_high is not None:

        st.metric(
            "최고기온",
            f"{selected_high:.1f} °C"
        )

    else:

        st.metric(
            "최고기온",
            "-"
        )


with col3:

    if selected_low is not None:

        st.metric(
            "최저기온",
            f"{selected_low:.1f} °C"
        )

    else:

        st.metric(
            "최저기온",
            "-"
        )


with col4:

    hot_percent = (
        hot_rank / total_periods
    ) * 100

    st.metric(
        "더운 기간 상위",
        f"{hot_percent:.1f}%"
    )


# ---------------------------------------------------------
# 역대 평균과 비교
# ---------------------------------------------------------

st.divider()

st.subheader("📌 역대 평균과 비교")

if difference > 0:

    st.write(
        f"선택한 기간의 평균기온은 "
        f"역대 같은 기간 평균보다 "
        f"**{difference:.1f}°C 높았습니다.** ☀️"
    )

elif difference < 0:

    st.write(
        f"선택한 기간의 평균기온은 "
        f"역대 같은 기간 평균보다 "
        f"**{abs(difference):.1f}°C 낮았습니다.** ❄️"
    )

else:

    st.write(
        "선택한 기간의 평균기온은 "
        "역대 같은 기간 평균과 거의 같습니다."
    )


# ---------------------------------------------------------
# 일별 기온 그래프
# ---------------------------------------------------------

st.divider()

st.subheader("📈 선택 기간의 일별 평균기온")

chart_data = selected[
    ["날짜", "평균기온"]
].copy()

chart_data = chart_data.set_index("날짜")

st.line_chart(
    chart_data
)


# ---------------------------------------------------------
# 기간 내 기온 분석
# ---------------------------------------------------------

st.subheader("📊 기간 내 기온 분석")

hot_days = (
    selected["평균기온"]
    > selected_average
).sum()

cold_days = (
    selected["평균기온"]
    < selected_average
).sum()

same_days = (
    selected["평균기온"]
    == selected_average
).sum()


col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "평균보다 더운 날",
        str(hot_days) + "일"
    )

with col2:

    st.metric(
        "평균보다 추운 날",
        str(cold_days) + "일"
    )

with col3:

    st.metric(
        "평균과 비슷한 날",
        str(same_days) + "일"
    )


# ---------------------------------------------------------
# 역대 TOP 10
# ---------------------------------------------------------

st.divider()

st.subheader("🔥 역대 가장 더웠던 기간 TOP 10")

top10_hot = hot_history.head(10).copy()

top10_hot["평균기온"] = (
    top10_hot["평균기온"]
    .round(1)
)

top10_hot = top10_hot[
    [
        "순위",
        "연도",
        "평균기온"
    ]
]

top10_hot = top10_hot.rename(
    columns={
        "평균기온": "평균기온 (°C)"
    }
)

st.dataframe(
    top10_hot,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# 역대 추운 기간 TOP 10
# ---------------------------------------------------------

st.subheader("❄️ 역대 가장 추웠던 기간 TOP 10")

top10_cold = cold_history.head(10).copy()

top10_cold["평균기온"] = (
    top10_cold["평균기온"]
    .round(1)
)

top10_cold = top10_cold[
    [
        "순위",
        "연도",
        "평균기온"
    ]
]

top10_cold = top10_cold.rename(
    columns={
        "평균기온": "평균기온 (°C)"
    }
)

st.dataframe(
    top10_cold,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# 가장 비슷했던 역대 기간
# ---------------------------------------------------------

st.divider()

st.subheader("🔍 지금과 기온이 가장 비슷했던 역대 기간")

similar = history.copy()

similar["차이"] = (
    similar["평균기온"]
    - selected_average
).abs()

similar = similar.sort_values(
    "차이"
).head(5)

similar["평균기온"] = (
    similar["평균기온"]
    .round(1)
)

similar["차이"] = (
    similar["차이"]
    .round(1)
)

similar = similar[
    [
        "연도",
        "평균기온",
        "차이"
    ]
]

similar = similar.rename(
    columns={
        "평균기온": "평균기온 (°C)",
        "차이": "현재와의 차이 (°C)"
    }
)

st.dataframe(
    similar,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# 전체 역대 데이터
# ---------------------------------------------------------

with st.expander("📊 전체 역대 순위 보기"):

    all_history = hot_history.copy()

    all_history["평균기온"] = (
        all_history["평균기온"]
        .round(1)
    )

    all_history = all_history[
        [
            "순위",
            "연도",
            "평균기온"
        ]
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


# ---------------------------------------------------------
# 하단 안내
# ---------------------------------------------------------

st.divider()

st.caption(
    "선택한 날짜 범위와 동일한 월·일 범위를 역대 각 연도와 비교합니다."
)

st.caption(
    "비교 기간의 모든 날짜 데이터가 존재하는 연도만 순위 계산에 포함합니다."
)
```
