from pathlib import Path

import pandas as pd


# 현재 파일 위치를 기준으로 프로젝트 최상위 폴더를 찾는다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 원본 엑셀 파일 경로
EXCEL_PATH = PROJECT_ROOT / "data" / "llm_evaluation.xlsx"

# CSV로 내보낼 엑셀 시트 목록
SHEET_NAMES = [
    "questions",
    "model_responses",
    "annotations",
    "faq_corpus",
    "search_queries",
]


def export_sheets() -> None:
    """엑셀의 각 시트를 개별 CSV 파일로 저장한다."""

    if not EXCEL_PATH.exists():
        raise FileNotFoundError(
            f"엑셀 파일을 찾을 수 없습니다: {EXCEL_PATH}"
        )

    # 실제 엑셀 파일에 들어 있는 시트 이름 확인
    excel_file = pd.ExcelFile(EXCEL_PATH)
    existing_sheets = excel_file.sheet_names

    missing_sheets = [
        sheet_name
        for sheet_name in SHEET_NAMES
        if sheet_name not in existing_sheets
    ]

    if missing_sheets:
        raise ValueError(
            "엑셀 파일에 다음 시트가 없습니다: "
            + ", ".join(missing_sheets)
        )

    for sheet_name in SHEET_NAMES:
        dataframe = pd.read_excel(
            EXCEL_PATH,
            sheet_name=sheet_name,
            dtype=str,
        )

        # 비어 있는 셀을 빈 문자열로 처리
        dataframe = dataframe.fillna("")

        # 열 이름 앞뒤의 불필요한 공백 제거
        dataframe.columns = [
            str(column).strip()
            for column in dataframe.columns
        ]

        output_path = PROJECT_ROOT / "data" / f"{sheet_name}.csv"

        dataframe.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
        )

        print(
            f"[완료] {sheet_name} → {output_path.name} "
            f"({len(dataframe)}개 행)"
        )


if __name__ == "__main__":
    export_sheets()