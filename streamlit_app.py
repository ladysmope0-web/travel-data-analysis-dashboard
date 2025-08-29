#######################
# Import libraries
# streamlit_app.py
# ----------------------------
import streamlit as st
import pandas as pd

# ------------------ 데이터 로딩 ------------------
# 엑셀 파일 경로 (같은 폴더에 둘 경우 파일명만 지정)
# streamlit_app.py
# -------------------------------------------------
# 2025 지역축제 대시보드 (깨끗한 최소 실행 버전)
# - df_reshaped / Sex 같은 이전 예제 흔적 전부 제거
# - 엑셀 경로 검증 + openpyxl 안내
# -------------------------------------------------
# streamlit_app.py — Minimal Clean Version (fixed)
# streamlit_app.py
# -------------------------------------------------
# 2025 지역축제 분석 대시보드 - 최종버전
# - 파일 경로 검증 + openpyxl 안내
# - 사이드바: 경로/연도/테마/지역/TopN
# - 컬럼1: 핵심 지표 + 테이블
# - 컬럼2: TopN 바차트 + 추세 자리
# - 컬럼3: 랭킹 테이블 + About
# -------------------------------------------------
# streamlit_app.py
# -------------------------------------------------
# 2025 지역축제 분석 대시보드 - 실행 OK 최종버전
# -------------------------------------------------
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

st.set_page_config(page_title="2025 지역축제 대시보드", page_icon="🎉", layout="wide")
st.title("🎉 2025 지역축제 분석 대시보드")

# ===== 설정/상수 =====
SEOUL_CAPITAL_AREA = {"서울", "경기", "인천"}  # 수도권 정의
THEME_TO_COLORSCALE = {
    "Plotly":  "plotly3",  # <— 중요: 'plotly'가 아니라 'plotly3'가 유효
    "Viridis": "viridis",
    "Cividis": "cividis",
    "Blues":   "blues",
    "Turbo":   "turbo",
}

# ===== 사이드바: 파일 경로 입력 =====
with st.sidebar:
    st.header("데이터 파일 설정")
    data_path = st.text_input(
        "엑셀(.xlsx) 파일 경로",
        value="2025년 지역축제 개최계획 현황(0321).xlsx",
        help="같은 폴더면 파일명만, 아니면 절대경로 입력 (예: /mnt/data/...)"
    )
    sheet_name = st.text_input("시트명", value="총괄")

# ===== 데이터 로딩 & 전처리 =====
df = None
p = Path(data_path)

if not p.exists():
    st.info("📄 파일을 찾을 수 없습니다. 사이드바에서 정확한 경로를 입력하세요.")
else:
    try:
        # 파일 구조 가정: skiprows=3 이후 0행=지역명, 1행=개수, 마지막 열(합계) 제외
        raw = pd.read_excel(p, sheet_name=sheet_name, engine="openpyxl", skiprows=3)
        regions = raw.iloc[0, 1:-1].tolist()
        counts  = pd.to_numeric(raw.iloc[1, 1:-1], errors="coerce").fillna(0).astype(int).tolist()
        df = pd.DataFrame({"지역": regions, "축제 개수": counts}).dropna().reset_index(drop=True)
        df["지역"] = df["지역"].astype(str).str.strip()
    except ImportError:
        st.error("`openpyxl`이 필요합니다. 터미널에서 `pip install openpyxl` 실행 후 다시 시도하세요.")
        st.stop()
    except Exception as e:
        st.error("데이터 로딩/전처리 중 오류가 발생했습니다. (시트 구조를 확인하세요)")
        st.exception(e)
        st.stop()

# ===== df 준비 후 UI =====
if df is not None and not df.empty:
    # 사이드바(분석 옵션)
    with st.sidebar:
        st.header("분석 설정")
        year = st.selectbox("연도", options=[2025], index=0)
        theme = st.selectbox("색상 테마", ["Plotly", "Viridis", "Cividis", "Blues", "Turbo"], index=0)
        colorscale = THEME_TO_COLORSCALE.get(theme, "plotly3")

        region_all = df["지역"].tolist()
        picked_regions = st.multiselect("지역 선택(복수)", options=region_all, default=region_all)
        top_k = st.slider(
            "Top N(랭킹)",
            min_value=5,
            max_value=min(10, len(region_all)),
            value=min(10, len(region_all)),
            step=1
        )

        st.markdown("---")
        st.write(f"**연도:** {year}  |  **선택 지역:** {len(picked_regions)}/{len(region_all)}")

    # 필터 적용
    df_f = df[df["지역"].isin(picked_regions)].copy().reset_index(drop=True)

    # ===== 레이아웃: 3컬럼 =====
    col1, col2, col3 = st.columns([1.0, 1.6, 1.2], gap="large")

    # -------- 컬럼1: 주요 지표 --------
    with col1:
        st.subheader("📊 주요 지표 요약")

        total_fests = int(df_f["축제 개수"].sum()) if not df_f.empty else 0
        max_row = df_f.loc[df_f["축제 개수"].idxmax()] if not df_f.empty else None
        min_row = df_f.loc[df_f["축제 개수"].idxmin()] if not df_f.empty else None

        # 수도권/비수도권 비율
        capital_total = int(df_f[df_f["지역"].isin(SEOUL_CAPITAL_AREA)]["축제 개수"].sum()) if not df_f.empty else 0
        non_capital_total = total_fests - capital_total if total_fests else 0
        capital_ratio = (capital_total / total_fests * 100) if total_fests else 0
        non_capital_ratio = 100 - capital_ratio if total_fests else 0

        m1, m2 = st.columns(2)
        with m1:
            st.metric("총 축제 수", f"{total_fests:,} 개" if total_fests else "—")
            if min_row is not None:
                st.metric("최소 개최 지역", f"{min_row['지역']}", delta=f"{int(min_row['축제 개수']):,} 개")
        with m2:
            if max_row is not None:
                st.metric("최다 개최 지역", f"{max_row['지역']}", delta=f"{int(max_row['축제 개수']):,} 개")

        st.markdown("### 수도권 vs 비수도권")
        r1, r2 = st.columns(2)
        with r1:
            st.metric("수도권 축제 비율", f"{capital_ratio:0.1f} %")
        with r2:
            st.metric("비수도권 축제 비율", f"{non_capital_ratio:0.1f} %")

        st.markdown("### 지역별 현황 (테이블)")
        table_df = df_f.copy()
        table_df["비율(%)"] = (table_df["축제 개수"] / total_fests * 100).round(1) if total_fests else 0
        st.dataframe(
            table_df.sort_values("축제 개수", ascending=False).reset_index(drop=True),
            use_container_width=True, height=420
        )

    # -------- 컬럼2: 시각화 --------
    with col2:
        st.subheader("🗺️ 지역별 축제 시각화")

        # Top N 바차트 (GeoJSON 없을 때 대체)
        top_df = df_f.sort_values("축제 개수", ascending=False).head(top_k)
        if top_df.empty:
            st.info("표시할 데이터가 없습니다. 사이드바 필터를 확인하세요.")
        else:
            fig_bar = px.bar(
                top_df,
                x="지역", y="축제 개수",
                color="축제 개수",
                title=f"Top {top_k} 지역 축제 수",
                color_continuous_scale=colorscale,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Choropleth 안내 (옵션)
        with st.expander("🌏 Choropleth 지도 안내 (옵션)"):
            st.write(
                "- 현재는 GeoJSON이 없어 바차트로 대체합니다.\n"
                "- **대한민국 시·도 GeoJSON** 경로/URL 제공 시 Choropleth 지도로 교체 가능.\n"
                "- 키 매칭: DataFrame의 `지역` ↔ GeoJSON의 도 단위 속성명"
            )

        st.markdown("### 📈 추세 자리(옵션)")
        st.info("연도별 데이터가 쌓이면 추세/히트맵을 이 영역에 추가합니다.")

    # -------- 컬럼3: 랭킹 & About --------
    with col3:
        st.subheader("🏆 지역 랭킹")
        rank_df = df_f.sort_values("축제 개수", ascending=False).reset_index(drop=True)
        rank_df.index = rank_df.index + 1
        st.dataframe(rank_df.head(top_k), use_container_width=True, height=360)

        st.markdown("---")
        st.subheader("ℹ️ About")
        st.markdown(
            """
            - **데이터 출처**: 지자체 응답 기반 2025년 지역축제 개최 계획(0321 기준)
            - **지표 설명**
              - *총 축제 수*: 현재 선택된 지역의 축제 개수 합계
              - *최다/최소 개최 지역*: 지역별 축제 개수 기준
              - *수도권 비율*: 서울·경기·인천 합계 / 전체 합계
            - **활용 예시**
              - 지역별 예산/마케팅 우선순위 설정
              - 상위 지역 벤치마킹, 비수도권 분포 점검
            """
        )

    st.caption("© 2025 지역축제 분석 대시보드")

else:
    st.info("왼쪽 사이드바에서 **정확한 파일 경로**를 입력하면 대시보드가 활성화됩니다.")
