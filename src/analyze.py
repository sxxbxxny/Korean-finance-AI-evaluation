from pathlib import Path

import pandas as pd



# 1. 기본 경로 설정
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

# results 폴더가 없으면 자동으로 생성
RESULTS_DIR.mkdir(exist_ok=True)



# 2. 사용할 열 이름 설정
ID_COLUMN = "question_id"
QUERY_TYPE_COLUMN = "query_type"
LABEL_COLUMN = "final_label"

# 평가값의 표준 순서입니다.
LABEL_ORDER = [
    "Pass",
    "Minor Error",
    "Major Error",
]


# 3. CSV 파일 불러오기
questions = pd.read_csv(
    DATA_DIR / "questions.csv",
    dtype=str,
    keep_default_na=False,
)

model_responses = pd.read_csv(
    DATA_DIR / "model_responses.csv",
    dtype=str,
    keep_default_na=False,
)

annotations = pd.read_csv(
    DATA_DIR / "annotations.csv",
    dtype=str,
    keep_default_na=False,
)


print("CSV 파일 불러오기 완료")
print(f"questions: {len(questions)}행")
print(f"model_responses: {len(model_responses)}행")
print(f"annotations: {len(annotations)}행")


# 4. 필수 열이 존재하는지 확인
required_columns = {
    "questions.csv": {
        ID_COLUMN,
        QUERY_TYPE_COLUMN,
    },
    "model_responses.csv": {
        ID_COLUMN,
    },
    "annotations.csv": {
        ID_COLUMN,
        LABEL_COLUMN,
    },
}

dataframes = {
    "questions.csv": questions,
    "model_responses.csv": model_responses,
    "annotations.csv": annotations,
}

for file_name, required in required_columns.items():
    actual_columns = set(dataframes[file_name].columns)
    missing_columns = required - actual_columns

    if missing_columns:
        raise ValueError(
            f"{file_name}에 필요한 열이 없습니다: {missing_columns}\n"
            f"현재 열: {list(dataframes[file_name].columns)}"
        )



# 5. question_id 중복 여부 확인
for file_name, dataframe in dataframes.items():
    duplicated_ids = dataframe.loc[
        dataframe[ID_COLUMN].duplicated(),
        ID_COLUMN,
    ].tolist()

    if duplicated_ids:
        raise ValueError(
            f"{file_name}에 중복된 question_id가 있습니다: "
            f"{duplicated_ids}"
        )



# 6. 세 파일의 question_id가 일치하는지 확인
question_ids = set(questions[ID_COLUMN])
response_ids = set(model_responses[ID_COLUMN])
annotation_ids = set(annotations[ID_COLUMN])

missing_responses = question_ids - response_ids
extra_responses = response_ids - question_ids

missing_annotations = question_ids - annotation_ids
extra_annotations = annotation_ids - question_ids

if missing_responses:
    raise ValueError(
        f"답변이 없는 question_id: {sorted(missing_responses)}"
    )

if extra_responses:
    raise ValueError(
        f"questions.csv에 없는 답변 ID: {sorted(extra_responses)}"
    )

if missing_annotations:
    raise ValueError(
        f"평가가 없는 question_id: {sorted(missing_annotations)}"
    )

if extra_annotations:
    raise ValueError(
        f"questions.csv에 없는 평가 ID: {sorted(extra_annotations)}"
    )

print("question_id 검수 완료")



# 7. 평가값 표기 통일
def normalize_label(value):
    """
    pass, PASS, minor_error처럼 서로 다르게 작성된 평가값을
    Pass, Minor Error, Major Error로 통일합니다.
    """

    normalized_value = (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )

    label_mapping = {
        "pass": "Pass",
        "minor error": "Minor Error",
        "major error": "Major Error",
    }

    return label_mapping.get(normalized_value, value)


annotations[LABEL_COLUMN] = annotations[LABEL_COLUMN].apply(
    normalize_label
)

# 정해진 세 가지 이외의 평가값이 있는지 확인
invalid_labels = sorted(
    set(annotations[LABEL_COLUMN]) - set(LABEL_ORDER)
)

if invalid_labels:
    raise ValueError(
        f"정해지지 않은 평가값이 있습니다: {invalid_labels}\n"
        f"사용 가능한 평가값: {LABEL_ORDER}"
    )

print("평가값 표기 통일 완료")



# 8. 세 데이터 연결
merged_data = questions.merge(
    model_responses,
    on=ID_COLUMN,
    how="left",
    validate="one_to_one",
    suffixes=("_question", "_response"),
)

merged_data = merged_data.merge(
    annotations,
    on=ID_COLUMN,
    how="left",
    validate="one_to_one",
    suffixes=("", "_annotation"),
)

print(f"데이터 연결 완료: {len(merged_data)}행")



# 9. 전체 평가 결과 집계
total_count = len(merged_data)

label_counts = (
    merged_data[LABEL_COLUMN]
    .value_counts()
    .reindex(LABEL_ORDER, fill_value=0)
)

overall_summary = (
    label_counts
    .rename_axis("label")
    .reset_index(name="count")
)

overall_summary["percentage"] = (
    overall_summary["count"] / total_count * 100
).round(1)



# 10. query_type별 결과 집계
query_type_summary = pd.crosstab(
    merged_data[QUERY_TYPE_COLUMN],
    merged_data[LABEL_COLUMN],
)

query_type_summary = query_type_summary.reindex(
    columns=LABEL_ORDER,
    fill_value=0,
)

query_type_summary["Total"] = (
    query_type_summary[LABEL_ORDER].sum(axis=1)
)

query_type_summary["Pass Rate (%)"] = (
    query_type_summary["Pass"]
    / query_type_summary["Total"]
    * 100
).round(1)

query_type_summary = query_type_summary.reset_index()



# 11. 오류 사례만 분리
error_cases = merged_data[
    merged_data[LABEL_COLUMN] != "Pass"
].copy()



# 12. 분석 결과를 CSV 파일로 저장
merged_data.to_csv(
    RESULTS_DIR / "combined_results.csv",
    index=False,
    encoding="utf-8-sig",
)

overall_summary.to_csv(
    RESULTS_DIR / "overall_summary.csv",
    index=False,
    encoding="utf-8-sig",
)

query_type_summary.to_csv(
    RESULTS_DIR / "query_type_summary.csv",
    index=False,
    encoding="utf-8-sig",
)

error_cases.to_csv(
    RESULTS_DIR / "error_cases.csv",
    index=False,
    encoding="utf-8-sig",
)



# 13. 터미널에 결과 출력
print("\n전체 평가 결과")
print(overall_summary.to_string(index=False))

print("\nquery_type별 평가 결과")
print(query_type_summary.to_string(index=False))

print(f"\n오류 사례: {len(error_cases)}개")
print(f"결과 저장 위치: {RESULTS_DIR}")