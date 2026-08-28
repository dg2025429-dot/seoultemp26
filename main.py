```text
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="서울 기온 랭킹",
    page_icon="🌡️",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv("seoul.csv")

    df.columns = df.columns.astype(str).str.strip()

    df["날짜"] = (
        df["날짜"]
        .astype(str)
        .str.strip()
    )

    df["날짜"] = pd.to_datetime(
        df["날짜"],
        errors="coerce"
    )

    for column in ["평균기온", "최저기온", "최고기온"]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    df = df.dropna(
        subset=["날짜", "평균기온"]
    ).copy()

    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일"] = df["날짜"].dt.day

    return df


# 데이터 불러오기
try:
    df = load_data()
except Exception as e:
    st.error("seoul.csv 파일을 읽을 수 없습니다.")
    st.error(str(e))
    st.stop()


# 필수 컬럼 확인
required_columns = [
    "날짜",
    "평균기온"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    st.error(
        "seoul.csv에 필요한 컬럼이 없습니다: "
        + ", ".join(missing_columns)
    )
    st.stop()


# 제목
st.title("🌡️ 서울 기온 랭킹")

st.write(
    "원하는 기간을 선택하면 "
    "서울의 역대 같은 기간과 비교해 "
    "얼마나 더웠거나 추웠는지 확인할 수 있습니다."
)

min_date = df["날짜"].min().date()
max_date = df["날짜"].max().date()

st.caption(
    "데이터 기간: "
    + min_date.strftime("%Y.%m.%d")
    + " ~ "
    + max_date.strftime("%Y.%m.%d")
)

st.divider()


# 날짜 선택
st.subheader("📅 비교할 기간")

col1, col2, col3 = st.columns(3)

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

with col3:
    ranking_type = st.selectbox(
        "순위 기준",
        [
            "더운 순위",
            "추운 순위"
        ]
    )


# 날짜 확인
if start_date > end_date:
    st.error(
        "⚠️ 종료 날짜는 시작 날짜보다 빠를 수 없습니다."
    )
    st.stop()


period_days = (
    end_date - start_date
).days + 1


# 선택한 기간
selected = df[
    (df["날짜"] >= pd.Timestamp(start_date))
    &
    (df["날짜"] <= pd.Timestamp(end_date))
].copy()


if selected.empty:
    st.warning(
        "선택한 기간에 데이터가 없습니다."
    )
    st.stop()


# 선택 기간 통계
average_temperature = selected["평균기온"].mean()

if "최고기온" in selected.columns:
    highest_temperature = selected["최고기온"].max()
else:
    highest_temperature = None

if "최저기온" in selected.columns:
    lowest_temperature = selected["최저기온"].min()
else:
    lowest_temperature = None


# 역대 동일 기간 계산
start_month = start_date.month
start_day = start_date.day

end_month = end_date.month
end_day = end_date.day

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
    ]

    if len(period) == period_days:

        historical.append(
            {
                "연도": year,
                "평균기온": period["평균기온"].mean()
            }
        )


history = pd.DataFrame(historical)


if history.empty:
    st.error(
        "비교할 수 있는 역대 데이터가 없습니다."
    )
    st.stop()


# 더운 순위
hot_history = history.sort_values(
    "평균기온",
    ascending=False
).reset_index(drop=True)

hot_history["순위"] = range(
    1,
    len(hot_history) + 1
)


# 추운 순위
cold_history = history.sort_values(
    "평균기온",
    ascending=True
).reset_index(drop=True)

cold_history["순위"] = range(
    1,
    len(cold_history) + 1
)


# 현재 선택 기간 순위
selected_year = start_date.year

if ranking_type == "더운 순위":

    ranking_data = hot_history

else:

    ranking_data = cold_history


same_year = ranking_data[
    ranking_data["연도"] == selected_year
]


if not same_year.empty:

    rank = int(
        same_year.iloc[0]["순위"]
    )

else:

    if ranking_type == "더운 순위":

        rank = (
            ranking_data["평균기온"]
            .gt(average_temperature)
            .sum()
            + 1
        )

    else:

        rank = (
            ranking_data["평균기온"]
            .lt(average_temperature)
            .sum()
            + 1
        )


total_periods = len(ranking_data)


# 순위 분위
rank_percent = (
    rank / total_periods
) * 100


# 역대 평균
historical_average = history["평균기온"].mean()

difference = (
    average_temperature
    - historical_average
)


# 결과 문구
if ranking_type == "더운 순위":

    if rank == 1:
        message = "🔥 역대 가장 더운 기간입니다!"

    elif rank <= max(1, int(total_periods * 0.05)):
        message = "🔥 역대 최상위권의 더운 기간입니다."

    elif rank <= max(1, int(total_periods * 0.20)):
        message = "☀️ 상당히 더운 기간에 속합니다."

    elif rank <= max(1, int(total_periods * 0.50)):
        message = "🌤️ 비교적 따뜻한 기간입니다."

    else:
        message = "🌥️ 비교적 선선한 기간입니다."

else:

    if rank == 1:
        message = "🥶 역대 가장 추운 기간입니다!"

    elif rank <= max(1, int(total_periods * 0.05)):
        message = "🥶 역대 최상위권의 추운 기간입니다."

    elif rank <= max(1, int(total_periods * 0.20)):
        message = "❄️ 상당히 추운 기간에 속합니다."

    elif rank <= max(1, int(total_periods * 0.50)):
        message = "🌥️ 비교적 선선한 기간입니다."

    else:
        message = "☀️ 비교적 따뜻한 기간입니다."


# 결과
st.divider()

st.subheader("🏆 분석 결과")

st.write(
    start_date.strftime("%Y.%m.%d")
    + " ~ "
    + end_date.strftime("%Y.%m.%d")
)

if ranking_type == "더운 순위":

    st.metric(
        "🔥 역대 더운 기간 순위",
        str(rank) + "위",
        "총 " + str(total_periods) + "개 기간"
    )

else:

    st.metric(
        "🥶 역대 추운 기간 순위",
        str(rank) + "위",
        "총 " + str(total_periods) + "개 기간"
    )

st.success(message)


# 주요 기온
st.subheader("🌡️ 선택 기간 기온")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "평균기온",
        f"{average_temperature:.1f} °C"
    )

with col2:
    if highest_temperature is not None:
        st.metric(
            "최고기온",
            f"{highest_temperature:.1f} °C"
        )
    else:
        st.metric(
            "최고기온",
            "-"
        )

with col3:
    if lowest_temperature is not None:
        st.metric(
            "최저기온",
            f"{lowest_temperature:.1f} °C"
        )
    else:
        st.metric(
            "최저기온",
            "-"
        )

with col4:
    st.metric(
        "역대 상위",
        f"{rank_percent:.1f}%"
    )


# 평년 비교
st.divider()

st.subheader("📌 역대 평균과 비교")

if difference > 0:

    st.info(
        f"선택한 기간은 역대 같은 기간 평균보다 "
        f"{difference:.1f}°C 높았습니다. ☀️"
    )

elif difference < 0:

    st.info(
        f"선택한 기간은 역대 같은 기간 평균보다 "
        f"{abs(difference):.1f}°C 낮았습니다. ❄️"
    )

else:

    st.info(
        "선택한 기간은 역대 같은 기간 평균과 거의 같습니다."
    )


# 일별 그래프
st.divider()

st.subheader("📈 선택 기간의 일별 평균기온")

chart_data = selected[
    ["날짜", "평균기온"]
].copy()

chart_data = chart_data.set_index("날짜")

st.line_chart(
    chart_data,
    y="평균기온"
)


# 기간 내 기온 분석
st.subheader("📊 기간 내 기온 분석")

daily_average = (
    selected["평균기온"].mean()
)

hot_days = (
    selected["평균기온"]
    > daily_average
).sum()

cold_days = (
    selected["평균기온"]
    < daily_average
).sum()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "기간 평균",
        f"{daily_average:.1f} °C"
    )

with col2:
    st.metric(
        "기간 평균보다 더운 날",
        f"{hot_days}일"
    )

with col3:
    st.metric(
        "기간 평균보다 추운 날",
        f"{cold_days}일"
    )


# TOP 10
st.divider()

if ranking_type == "더운 순위":

    st.subheader("🔥 역대 더운 기간 TOP 10")

    top10 = hot_history.head(10).copy()

else:

    st.subheader("🥶 역대 추운 기간 TOP 10")

    top10 = cold_history.head(10).copy()


top10["평균기온"] = (
    top10["평균기온"]
    .round(1)
)

top10 = top10[
    [
        "순위",
        "연도",
        "평균기온"
    ]
]

top10 = top10.rename(
    columns={
        "평균기온": "평균기온 (°C)"
    }
)

st.dataframe(
    top10,
    use_container_width=True,
    hide_index=True
)


# 비슷한 기간
st.divider()

st.subheader("🔍 기온이 비슷했던 역대 기간")

similar = history.copy()

similar["차이"] = (
    similar["평균기온"]
    - average_temperature
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


# 전체 순위
with st.expander("📊 전체 역대 순위 보기"):

    all_history = ranking_data.copy()

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


# 안내
st.divider()

st.caption(
    "평균기온을 기준으로 역대 동일 기간과 비교합니다."
)

st.caption(
    "비교 기간의 모든 날짜 데이터가 존재하는 연도만 순위에 포함됩니다."
)
```
