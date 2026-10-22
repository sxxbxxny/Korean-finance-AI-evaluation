from pathlib import Path

import pandas as pd


# 현재 프로젝트의 최상위 폴더
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# data 폴더 위치를 지정
DATA_DIR = PROJECT_ROOT / "data"

# 원본 엑셀 파일의 위치
EXCEL_PATH = DATA_DIR / "llm_evaluation.xlsx"

# 엑셀 시트 이름과 생성할 CSV 파일명 연결
SHEET_TO_CSV = {
    "questions": "questions.csv",
    "model_responses": "model_responses.csv",
    "annotations": "annotations.csv",
}

OVERWRITE_EXISTING = True

# 엑셀 파일이 실제로 존재하는지 확인
if not EXCEL_PATH.exists():
    raise FileNotFoundError(
        f"엑셀 파일을 찾을 수 없습니다: {EXCEL_PATH}"
    )


# 엑셀 파일에 들어 있는 시트 이름 확인
excel_file = pd.ExcelFile(EXCEL_PATH)

print("엑셀 파일에서 확인된 시트:")
print(excel_file.sheet_names)


# 필요한 시트가 모두 존재하는지 확인
missing_sheets = [
    sheet_name
    for sheet_name in SHEET_TO_CSV
    if sheet_name not in excel_file.sheet_names
]



# 각 시트를 읽어 별도의 CSV 파일로 저장
for sheet_name, csv_file_name in SHEET_TO_CSV.items():
    output_path = DATA_DIR / csv_file_name

    # 기존 CSV 파일에 엑셀 파일 최신 내용으로 덮어쓰기
    if output_path.exists() and not OVERWRITE_EXISTING:
        raise FileExistsError(
            f"이미 존재하는 파일입니다: {output_path}"
        )

    dataframe = pd.read_excel(
        EXCEL_PATH,
        sheet_name=sheet_name,
        dtype=str,
    )

    # 비어 있는 셀을 빈 문자열로 처리
    dataframe = dataframe.fillna("")

    # CSV 파일로 저장
    dataframe.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"{sheet_name} 시트 저장 완료: "
        f"{csv_file_name} ({len(dataframe)}행)"
    )


print("모든 시트를 CSV 파일로 변환했습니다.")