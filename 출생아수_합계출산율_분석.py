from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "출생아수__합계출산율.xlsx"
OUTPUT_CSV = BASE_DIR / "출생아수_합계출산율_정제데이터.csv"
OUTPUT_REPORT = BASE_DIR / "출생아수_합계출산율_분석보고서.txt"
OUTPUT_CHART = BASE_DIR / "출생아수_연도별_라인그래프.png"


def clean_birth_data(file_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_excel(file_path, sheet_name="데이터", header=None)
    year_labels = raw.iloc[0, 1:].astype(str).str.extract(r"(\d{4})")[0]
    year_labels = pd.to_numeric(year_labels, errors="coerce")

    data = raw.iloc[1:].copy()
    data = data.rename(columns={0: "지표"})
    data = data[data["지표"].notna()].set_index("지표")
    data.columns = year_labels
    data = data.loc[:, data.columns.notna()]
    data = data.apply(pd.to_numeric, errors="coerce")
    data.index = data.index.astype(str).str.strip()

    long_data = data.reset_index().melt(
        id_vars="지표", var_name="연도", value_name="값"
    )
    long_data["연도"] = long_data["연도"].astype(int)
    long_data = long_data.dropna(subset=["값"]).sort_values(["연도", "지표"])
    return data, long_data


def make_birth_chart(data: pd.DataFrame, output_file: Path) -> None:
    plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.plot(
        data.columns,
        data.loc["출생아수(명)"],
        color="#0b7285",
        linewidth=2.5,
        marker="o",
        markersize=3.5,
    )
    ax.set_title("대한민국 연도별 출생아 수 (1970~2025)", fontsize=16, pad=14)
    ax.set_xlabel("연도")
    ax.set_ylabel("출생아 수 (명)")
    ax.grid(axis="y", alpha=0.25)
    ax.set_xlim(data.columns.min(), data.columns.max())
    fig.tight_layout()
    fig.savefig(output_file, dpi=160)
    plt.close(fig)


def build_report(data: pd.DataFrame) -> str:
    births = data.loc["출생아수(명)"]
    fertility = data.loc["합계출산율(명)"]
    birth_change = births.pct_change() * 100
    fertility_change = fertility.pct_change() * 100
    correlation = births.corr(fertility)

    def fmt_year_value(series: pd.Series, year: int) -> str:
        return f"{year}년: {series.loc[year]:,.3f}".rstrip("0").rstrip(".")

    period_rows = []
    for start, end in [(1970, 1990), (1990, 2000), (2000, 2010), (2010, 2020), (2020, 2025)]:
        if start in births.index and end in births.index:
            birth_pct = (births.loc[end] / births.loc[start] - 1) * 100
            fertility_pct = (fertility.loc[end] / fertility.loc[start] - 1) * 100
            period_rows.append(
                f"  {start}~{end}: 출생아 수 {birth_pct:+.1f}%, 합계출산율 {fertility_pct:+.1f}%"
            )

    report = [
        "대한민국 출생아 수·합계출산율 분석 보고서",
        "=" * 48,
        f"분석 기간: {int(data.columns.min())}~{int(data.columns.max())}",
        f"관측 연도 수: {len(data.columns)}개",
        f"지표 수: {len(data.index)}개",
        "",
        "[데이터 정제]",
        "- 데이터 시트의 첫 행을 연도 헤더로 사용",
        "- 연도 헤더에서 4자리 연도만 추출하여 2025 p)도 2025년으로 정규화",
        "- 지표명 앞뒤 공백 제거 및 모든 값 숫자형 변환",
        "- 숫자로 변환되지 않거나 비어 있는 관측값은 결측으로 처리 후 제거",
        f"- 정제 데이터 결측치: {int(data.isna().sum().sum())}개",
        f"- 정제 데이터 중복 행: {int(data.reset_index().duplicated().sum())}개",
        "",
        "[핵심 요약]",
        f"- 출생아 수 최댓값: {fmt_year_value(births, int(births.idxmax()))}명",
        f"- 출생아 수 최솟값: {fmt_year_value(births, int(births.idxmin()))}명",
        f"- 합계출산율 최댓값: {fmt_year_value(fertility, int(fertility.idxmax()))}",
        f"- 합계출산율 최솟값: {fmt_year_value(fertility, int(fertility.idxmin()))}",
        f"- 1970년 대비 2025년 출생아 수 변화: {births.iloc[-1] / births.iloc[0] - 1:+.1%}",
        f"- 1970년 대비 2025년 합계출산율 변화: {fertility.iloc[-1] / fertility.iloc[0] - 1:+.1%}",
        f"- 출생아 수와 합계출산율의 Pearson 상관계수: {correlation:.4f}",
        "",
        "[전년 대비 최대 변동]",
        f"- 출생아 수 최대 증가: {int(birth_change.idxmax())}년 ({birth_change.max():+.1f}%)",
        f"- 출생아 수 최대 감소: {int(birth_change.idxmin())}년 ({birth_change.min():+.1f}%)",
        f"- 합계출산율 최대 증가: {int(fertility_change.idxmax())}년 ({fertility_change.max():+.1f}%)",
        f"- 합계출산율 최대 감소: {int(fertility_change.idxmin())}년 ({fertility_change.min():+.1f}%)",
        "",
        "[기간별 변화율]",
        *period_rows,
    ]
    return "\n".join(report) + "\n"


def main() -> None:
    wide_data, long_data = clean_birth_data(INPUT_FILE)
    long_data.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    make_birth_chart(wide_data, OUTPUT_CHART)
    OUTPUT_REPORT.write_text(build_report(wide_data), encoding="utf-8")

    print(f"정제 데이터: {OUTPUT_CSV}")
    print(f"분석 보고서: {OUTPUT_REPORT}")
    print(f"라인그래프: {OUTPUT_CHART}")
    print(f"shape(wide)={wide_data.shape}, shape(long)={long_data.shape}")
    print(build_report(wide_data))


if __name__ == "__main__":
    main()