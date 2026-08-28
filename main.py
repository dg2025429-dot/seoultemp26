```python
import streamlit as st
import pandas as pd
from datetime import date


# =========================================================
# 1. 페이지 설정
# =========================================================

st.set_page_config(
    page_title="서울 기온 랭킹",
    page_icon="🌡️",
    layout="wide"
)


# =========================================================
# 2. 데이터 불러오기
# =========================================================

@st.cache_data
def load_data():

    # 반드시 이 파일명을 사용
    df = pd.read_csv("seoul.csv")

    # 컬럼명 정리
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # 날짜 정리
    df["날짜"] = (
        df["날짜"]
        .astype(str)
        .str.strip()
    )

    df["날짜"] = pd.to_datetime(
        df["날짜"],
        errors="coerce"
    )

    # 기온 숫자 변환
    temperature_columns = [
        "평균기온",
        "최저기온",
        "최고기온"
    ]

    for column in temperature_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # 날짜 + 평균기온이 없는 데이터 제거
    df = df.dropna(
        subset=[
            "날짜",
            "평균기온"
        ]
    ).copy()

    # 날짜 정보
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일"] = df["날짜"].dt.day

    # 날짜 기준 정렬
    df = df.sort_values("날짜")

    return df


# =========================================================
# 3. 데이터 로드
# =========================================================

try:

    df = load_data()

except Exception as e:

    st.error("seoul.csv를 읽는 중 문제가 발생했습니다.")

    st.write(
        "main.py와 seoul.csv가 같은 폴더에 있는지 확인해주세요."
    )

    st.stop()


# =========================================================
# 4. 데이터 기본 검증
# =========================================================

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
        "필요한 컬럼이 없습니다: "
        + ", ".join(missing_columns)
    )

    st.stop()


# =========================================================
# 5. 헤더
# =========================================================

st.title("🌡️ 서울 기온 랭킹")

st.write(
    "원하는 기간을 선택하면, 서울의 역대 같은 기간과 비교해 "
    "얼마나 더웠거나 추웠는지 확인할 수 있습니다."
)

min_date = df["날짜"].min().date()
max_date = df["날짜"].max().date()

st.caption(
    f"서울 기상 관측 데이터 · "
    f"{min_date.strftime('%Y.%m.%d')} ~ "
    f"{max_date.strftime('%Y.%m.%d')}"
)


# =========================================================
# 6. 날짜 선택
# =========================================================

st.divider()

st.subheader("📅 비교할 기간")

col1, col2, col3 = st.columns([1, 1, 1])

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

    mode = st.selectbox(
        "무엇을 기준으로 볼까요?",
        [
            "더운 순위",
            "추운 순위"
        ]
    )


# =========================================================
# 7. 날짜 오류 확인
# =========================================================

if start_date > end_date:

    st.error(
        "⚠️ 종료 날짜는 시작 날짜보다 빠를 수 없습니다."
    )

    st.stop()


period_days = (
    end_date - start_date
).days + 1


# =========================================================
# 8. 선택한 기간 데이터
# =========================================================

selected = df[
    (df["날짜"] >= pd.Timestamp(start_date))
    &
    (df["날짜"] <= pd.Timestamp(end_date))
].copy()


if selected.empty:

    st.warning(
        "선택한 기간의 데이터가 없습니다."
    )

    st.stop()


# =========================================================
# 9. 선택 기간 통계
# =========================================================

selected_average = selected["평균기온"].mean()

selected_max = None
selected_min = None

if "최고기온" in selected.columns:

    selected_max = selected["최고기온"].max()

if "최저기온" in selected.columns:

    selected_min = selected["최저기온"].min()


# =========================================================
# 10. 역대 동일 기간 계산
# =========================================================

start_month = start_date.month
start_day = start_date.day

end_month = end_date.month
end_day = end_date.day


# 예: 12월 25일 ~ 1월 5일
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

    # 시작 날짜
    try:

        period_start = pd.Timestamp(
            year=year,
            month=start_month,
            day=start_day
        )

    except ValueError:

        continue


    # 종료 날짜
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


    # 선택 기간과 동일한 날짜 수가 있을 때만 비교
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
        "비교할 수 있는 역대 기간이 없습니다."
    )

    st.stop()


# =========================================================
# 11. 더운 순위 / 추운 순위
# =========================================================

hot_history = history.sort_values(
    "평균기온",
    ascending=False
).reset_index(drop=True)


cold_history = history.sort_values(
    "평균기온",
    ascending=True
).reset_index(drop=True)


hot_history["순위"] = range(
    1,
    len(hot_history) + 1
)


cold_history["순위"] = range(
    1,
    len(cold_history) + 1
)


# =========================================================
# 12. 현재 선택 기간의 순위
# =========================================================

selected_year = start_date.year


if mode == "더운 순위":

    target_history = hot_history

else:

    target_history = cold_history


same_year = target_history[
    target_history["연도"] == selected_year
]


if not same_year.empty:

    rank = int(
        same_year.iloc[0]["순위"]
    )

else:

    if mode == "더운 순위":

        rank = (
            target_history["평균기온"]
            .gt(selected_average)
            .sum()
            + 1
        )

    else:

        rank = (
            target_history["평균기온"]
            .lt(selected_average)
            .sum()
            + 1
        )


total_periods = len(target_history)


# =========================================================
# 13. 분위 계산
# =========================================================

top_percent = (
    rank / total_periods
) * 100


# =========================================================
# 14. 역대 평균과 비교
# =========================================================

historical_average = (
    history["평균기온"].mean()
)


temperature_difference = (
    selected_average
    - historical_average
)


# =========================================================
# 15. 결과 해석
# =========================================================

if mode == "더운 순위":

    if rank == 1:

        message = "🔥 역대 가장 더운 기간입니다!"

    elif rank <= max(
        1,
        int(total_periods * 0.05)
    ):

        message = "🔥 역대 최상위권의 더운 기간입니다."

    elif rank <= max(
        1,
        int(total_periods * 0.20)
    ):

        message = "☀️ 상당히 더운 기간에 속합니다."

    elif rank <= max(
        1,
        int(total_periods * 0.50)
    ):

        message = "🌤️ 평년보다 비교적 따뜻한 기간입니다."

    else:

        message = "🌥️ 역대 기준으로 비교적 선선한 기간입니다."

else:

    if rank == 1:

        message = "🥶 역대 가장 추운 기간입니다!"

    elif rank <= max(
        1,
        int(total_periods * 0.05)
    ):

        message = "🥶 역대 최상위권의 추운 기간입니다."

    elif rank <= max(
        1,
        int(total_periods * 0.20)
    ):

        message = "❄️ 상당히 추운 기간에 속합니다."

    elif rank <= max(
        1,
        int(total_periods * 0.50)
    ):

        message = "🌥️ 평년보다 비교적 선선한 기간입니다."

    else:

        message = "☀️ 역대 기준으로 비교적 따뜻한 기간입니다."


# =========================================================
# 16. 메인 결과
# =========================================================

st.divider()

st.subheader("🏆 분석 결과")

st.write(
    f"**{start_date.strftime('%Y.%m.%d')} "
    f"~ "
    f"{end_date.strftime('%Y.%m.%d')}**"
)

if mode == "더운 순위":

    st.metric(
        "🔥 역대 더운 기간 순위",
        f"{rank}위",
        f"총 {total_periods}개 기간"
    )

else:

    st.metric(
        "🥶 역대 추운 기간 순위",
        f"{rank}위",
        f"총 {total_periods}개 기간"
    )


st.success(message)


# =========================================================
# 17. 핵심 숫자
# =========================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "🌡️ 평균기온",
        f"{selected_average:.1f} °C"
    )


with col2:

    if selected_max is not None:

        st.metric(
            "☀️ 최고기온",
            f"{selected_max:.1f} °C"
        )

    else:

        st.metric(
            "☀️ 최고기온",
            "-"
        )


with col3:

    if selected_min is not None:

        st.metric(
            "❄️ 최저기온",
            f"{selected_min:.1f} °C"
        )

    else:

        st.metric(
            "❄️ 최저기온",
            "-"
        )


with col4:

    st.metric(
        "📊 역대 상위",
        f"{top_percent:.1f}%"
    )


# =========================================================
# 18. 평년과 비교
# =========================================================

st.divider()

st.subheader("📌 평년과 얼마나 달랐을까요?")

if temperature_difference > 0:

    st.write(
        f"선택한 기간의 평균기온은 "
        f"역대 비교기간 평균보다 "
        f"**{temperature_difference:.1f}°C 높았습니다.** ☀️"
    )

elif temperature_difference < 0:

    st.write(
        f"선택한 기간의 평균기온은 "
        f"역대 비교기간 평균보다 "
        f"**{abs(temperature_difference):.1f}°C 낮았습니다.** ❄️"
    )

else:

    st.write(
        "선택한 기간의 평균기온은 "
        "역대 비교기간 평균과 거의 같습니다."
    )


# =========================================================
# 19. 일별 기온 그래프
# =========================================================

st.divider()

st.subheader("📈 선택 기간의 일별 기온")

chart_data = selected[
    ["날짜", "평균기온"]
].copy()

chart_data = chart_data.set_index("날짜")

st.line_chart(
    chart_data,
    y="평균기온"
)


# =========================================================
# 20. 더운 날 / 추운 날 분석
# =========================================================

st.divider()

st.subheader("🌡️ 선택 기간 속 날씨")

daily_average = (
    selected["평균기온"]
    .mean()
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
        "평균보다 더운 날",
        f"{hot_days}일"
    )


with col3:

    st.metric(
        "평균보다 추운 날",
        f"{cold_days}일"
    )


# =========================================================
# 21. 역대 TOP 10
# =========================================================

st.divider()

if mode == "더운 순위":

    st.subheader("🔥 역대 가장 더웠던 기간 TOP 10")

    ranking_table = hot_history.head(10).copy()

else:

    st.subheader("🥶 역대 가장 추웠던 기간 TOP 10")

    ranking_table = cold_history.head(10).copy()


ranking_table["평균기온"] = (
    ranking_table["평균기온"]
    .round(1)
)


ranking_table = ranking_table[
    [
        "순위",
        "연도",
        "평균기온"
    ]
]


ranking_table = ranking_table.rename(
    columns={
        "평균기온": "평균기온 (°C)"
    }
)


st.dataframe(
    ranking_table,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 22. 선택 기간과 비슷했던 역대 연도
# =========================================================

st.divider()

st.subheader("🔍 비슷한 기온이었던 역대 기간")


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


# =========================================================
# 23. 전체 역대 순위
# =========================================================

st.divider()

with st.expander("📊 전체 역대 기간 보기"):

    all_history = target_history.copy()

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


# =========================================================
# 24. 데이터 안내
# =========================================================

st.divider()

st.caption(
    "📌 순위는 선택한 날짜 범위와 동일한 월·일 범위를 "
    "역대 각 연도와 비교하여 계산합니다."
)

st.caption(
    "📌 비교 기간의 모든 날짜 데이터가 존재하는 연도만 "
    "순위 계산에 포함됩니다."
)

st.caption(
    "📌 평균기온을 기준으로 더운 순위와 추운 순위를 계산합니다."
)
```
