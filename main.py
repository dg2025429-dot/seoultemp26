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
    df["날짜"] = df["날짜"].astype(str).str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    for col in ["평균기온", "최저기온", "최고기온"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["날짜", "평균기온"]).copy()
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일"] = df["날짜"].dt.day
    return df

try:
    df = load_data()
except Exception as e:
    st.error("seoul.csv를 읽을 수 없습니다.")
    st.write(e)
    st.stop()

required = ["날짜", "평균기온"]
missing = [c for c in required if c not in df.columns]

if missing:
    st.error("seoul.csv에 필요한 컬럼이 없습니다: " + ", ".join(missing))
    st.stop()

st.title("🌡️ 서울 기온 랭킹")
st.write("선택한 기간이 서울의 역대 같은 기간 중 얼마나 더웠거나 추웠는지 확인해보세요.")

min_date = df["날짜"].min().date()
max_date = df["날짜"].max().date()

st.caption(
    f"데이터 기간: {min_date.strftime('%Y.%m.%d')} ~ {max_date.strftime('%Y.%m.%d')}"
)

st.divider()

st.subheader("📅 비교할 기간")

c1, c2 = st.columns(2)

with c1:
    start_date = st.date_input(
        "시작 날짜",
        value=date(2024, 7, 1),
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD"
    )

with c2:
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

period_days = (end_date - start_date).days + 1

selected = df[
    (df["날짜"] >= pd.Timestamp(start_date)) &
    (df["날짜"] <= pd.Timestamp(end_date))
].copy()

if selected.empty:
    st.warning("선택한 기간의 데이터가 없습니다.")
    st.stop()

selected_avg = selected["평균기온"].mean()
selected_high = selected["최고기온"].max() if "최고기온" in selected else None
selected_low = selected["최저기온"].min() if "최저기온" in selected else None

start_month, start_day = start_date.month, start_date.day
end_month, end_day = end_date.month, end_date.day

cross_year = (start_month, start_day) > (end_month, end_day)

historical = []

for year in sorted(df["연도"].dropna().unique()):
    year = int(year)

    try:
        period_start = pd.Timestamp(year=year, month=start_month, day=start_day)
        end_year = year + 1 if cross_year else year
        period_end = pd.Timestamp(year=end_year, month=end_month, day=end_day)
    except ValueError:
        continue

    period = df[
        (df["날짜"] >= period_start) &
        (df["날짜"] <= period_end)
    ]

    if len(period) == period_days:
        historical.append({
            "연도": year,
            "평균기온": period["평균기온"].mean()
        })

history = pd.DataFrame(historical)

if history.empty:
    st.error("비교할 수 있는 역대 데이터가 없습니다.")
    st.stop()

hot = history.sort_values("평균기온", ascending=False).reset_index(drop=True)
cold = history.sort_values("평균기온", ascending=True).reset_index(drop=True)

hot["순위"] = range(1, len(hot) + 1)
cold["순위"] = range(1, len(cold) + 1)

year = start_date.year

hot_match = hot[hot["연도"] == year]
cold_match = cold[cold["연도"] == year]

if not hot_match.empty:
    hot_rank = int(hot_match.iloc[0]["순위"])
else:
    hot_rank = int(hot["평균기온"].gt(selected_avg).sum() + 1)

if not cold_match.empty:
    cold_rank = int(cold_match.iloc[0]["순위"])
else:
    cold_rank = int(cold["평균기온"].lt(selected_avg).sum() + 1)

total = len(history)

hot_percent = hot_rank / total * 100
cold_percent = cold_rank / total * 100

historical_avg = history["평균기온"].mean()
difference = selected_avg - historical_avg

st.divider()
st.subheader("🏆 분석 결과")

st.write(
    f"**{start_date.strftime('%Y.%m.%d')} ~ {end_date.strftime('%Y.%m.%d')}** · "
    f"{period_days}일"
)

r1, r2 = st.columns(2)

with r1:
    st.metric(
        "🔥 역대 더운 순위",
        f"{hot_rank}위",
        f"총 {total}개 기간"
    )

with r2:
    st.metric(
        "❄️ 역대 추운 순위",
        f"{cold_rank}위",
        f"총 {total}개 기간"
    )

if hot_rank <= max(1, int(total * 0.1)):
    st.success("🔥 역대 기준으로 매우 더운 기간입니다.")
elif hot_rank <= max(1, int(total * 0.3)):
    st.info("☀️ 역대 기준으로 따뜻한 편입니다.")
elif cold_rank <= max(1, int(total * 0.1)):
    st.info("🥶 역대 기준으로 매우 추운 기간입니다.")
elif cold_rank <= max(1, int(total * 0.3)):
    st.info("❄️ 역대 기준으로 추운 편입니다.")
else:
    st.info("🌤️ 역대 평균에 가까운 기온입니다.")

st.subheader("🌡️ 선택 기간 기온")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("평균기온", f"{selected_avg:.1f} °C")

with m2:
    st.metric("최고기온", f"{selected_high:.1f} °C" if selected_high is not None else "-")

with m3:
    st.metric("최저기온", f"{selected_low:.1f} °C" if selected_low is not None else "-")

with m4:
    st.metric("더운 기간 상위", f"{hot_percent:.1f}%")

st.divider()
st.subheader("📌 역대 평균과 비교")

if difference > 0:
    st.write(f"역대 같은 기간 평균보다 **{difference:.1f}°C 높았습니다.** ☀️")
elif difference < 0:
    st.write(f"역대 같은 기간 평균보다 **{abs(difference):.1f}°C 낮았습니다.** ❄️")
else:
    st.write("역대 같은 기간 평균과 거의 같습니다.")

st.divider()
st.subheader("📈 선택 기간의 일별 평균기온")

chart = selected[["날짜", "평균기온"]].set_index("날짜")
st.line_chart(chart)

st.subheader("📊 기간 내 기온")

hot_days = int((selected["평균기온"] > selected_avg).sum())
cold_days = int((selected["평균기온"] < selected_avg).sum())

d1, d2, d3 = st.columns(3)

with d1:
    st.metric("평균보다 더운 날", f"{hot_days}일")

with d2:
    st.metric("평균보다 추운 날", f"{cold_days}일")

with d3:
    st.metric("관측 일수", f"{len(selected)}일")

st.divider()
st.subheader("🔥 역대 가장 더웠던 기간 TOP 10")

top_hot = hot.head(10).copy()
top_hot["평균기온"] = top_hot["평균기온"].round(1)
top_hot = top_hot[["순위", "연도", "평균기온"]]
top_hot = top_hot.rename(columns={"평균기온": "평균기온 (°C)"})

st.dataframe(
    top_hot,
    use_container_width=True,
    hide_index=True
)

st.subheader("❄️ 역대 가장 추웠던 기간 TOP 10")

top_cold = cold.head(10).copy()
top_cold["평균기온"] = top_cold["평균기온"].round(1)
top_cold = top_cold[["순위", "연도", "평균기온"]]
top_cold = top_cold.rename(columns={"평균기온": "평균기온 (°C)"})

st.dataframe(
    top_cold,
    use_container_width=True,
    hide_index=True
)

st.divider()
st.subheader("🔍 기온이 가장 비슷했던 역대 기간")

similar = history.copy()
similar["차이"] = (similar["평균기온"] - selected_avg).abs()
similar = similar.sort_values("차이").head(5)

similar["평균기온"] = similar["평균기온"].round(1)
similar["차이"] = similar["차이"].round(1)

similar = similar[["연도", "평균기온", "차이"]]
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

with st.expander("📊 전체 역대 순위 보기"):

    all_data = hot.copy()
    all_data["평균기온"] = all_data["평균기온"].round(1)
    all_data = all_data[["순위", "연도", "평균기온"]]
    all_data = all_data.rename(
        columns={"평균기온": "평균기온 (°C)"}
    )

    st.dataframe(
        all_data,
        use_container_width=True,
        hide_index=True
    )

st.divider()

st.caption(
    "선택한 날짜 범위와 동일한 월·일 범위를 역대 각 연도와 비교합니다."
)

st.caption(
    "비교 기간의 모든 날짜 데이터가 존재하는 연도만 순위 계산에 포함됩니다."
)
