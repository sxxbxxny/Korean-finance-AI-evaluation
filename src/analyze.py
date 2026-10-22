from pathlib import Path

import pandas as pd


# =========================================================
# 1. 프로젝트 경로 설정
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# 2. 열 이름과 허용값 설정
# =========================================================

ID_COLUMN = "question_id"
QUERY_TYPE_COLUMN = "query_type"

ACCURACY_COLUMN = "accuracy"
FINAL_LABEL_COLUMN = "final_label"

ACCURACY_ORDER = [
    "correct",
    "minor_error",
    "major_error",
]

FINAL_LABEL_ORDER = [
    "pass",
    "need_revision",
    "fail",
]


# =========================================================
# 3. CSV 파일을 읽는 함수
# =========================================================

def read_csv_file(file_name):
    """
    data 폴더에서 CSV 파일을 읽습니다.
    모든 데이터를 문자열로 읽고 빈칸을 빈 문자열로 유지합니다.
    """

    file_path = DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSV 파일을 찾을 수 없습니다: {file_path}"
        )

    dataframe = pd.read_csv(
        file_path,
        dtype=str,
        keep_default_na=False,
    )

    # 열 이름 앞뒤 공백 제거
    dataframe.columns = dataframe.columns.str.strip()

    return dataframe


# =========================================================
# 4. CSV 파일 불러오기
# =========================================================

questions = read_csv_file("questions.csv")
model_responses = read_csv_file("model_responses.csv")
annotations = read_csv_file("annotations.csv")


print("CSV 파일 불러오기 완료")
print(f"questions.csv: {len(questions)}행")
print(f"model_responses.csv: {len(model_responses)}행")
print(f"annotations.csv: {len(annotations)}행")

print("\nannotations.csv 열 이름")
print(annotations.columns.tolist())


# =========================================================
# 5. 필수 열 확인
# =========================================================

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
        ACCURACY_COLUMN,
        FINAL_LABEL_COLUMN,
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
            f"{file_name}에 필요한 열이 없습니다: "
            f"{sorted(missing_columns)}\n"
            f"현재 열: {list(dataframes[file_name].columns)}"
        )


# =========================================================
# 6. question_id 정리
# =========================================================

for dataframe in dataframes.values():
    dataframe[ID_COLUMN] = (
        dataframe[ID_COLUMN]
        .astype(str)
        .str.strip()
    )


# =========================================================
# 7. 빈 question_id 확인
# =========================================================

for file_name, dataframe in dataframes.items():
    empty_id_rows = dataframe.index[
        dataframe[ID_COLUMN] == ""
    ].tolist()

    if empty_id_rows:
        excel_row_numbers = [
            row_index + 2
            for row_index in empty_id_rows
        ]

        raise ValueError(
            f"{file_name}에 question_id가 비어 있습니다.\n"
            f"확인할 행 번호: {excel_row_numbers}"
        )


# =========================================================
# 8. 중복 question_id 확인
# =========================================================

for file_name, dataframe in dataframes.items():
    duplicated_ids = dataframe.loc[
        dataframe[ID_COLUMN].duplicated(keep=False),
        ID_COLUMN,
    ].unique().tolist()

    if duplicated_ids:
        raise ValueError(
            f"{file_name}에 중복된 question_id가 있습니다: "
            f"{sorted(duplicated_ids)}"
        )


# =========================================================
# 9. 세 파일의 question_id 일치 여부 확인
# =========================================================

question_ids = set(questions[ID_COLUMN])
response_ids = set(model_responses[ID_COLUMN])
annotation_ids = set(annotations[ID_COLUMN])

id_errors = []

missing_responses = question_ids - response_ids
extra_responses = response_ids - question_ids

missing_annotations = question_ids - annotation_ids
extra_annotations = annotation_ids - question_ids

if missing_responses:
    id_errors.append(
        f"답변이 없는 question_id: {sorted(missing_responses)}"
    )

if extra_responses:
    id_errors.append(
        f"questions.csv에 없는 답변 ID: "
        f"{sorted(extra_responses)}"
    )

if missing_annotations:
    id_errors.append(
        f"평가가 없는 question_id: "
        f"{sorted(missing_annotations)}"
    )

if extra_annotations:
    id_errors.append(
        f"questions.csv에 없는 평가 ID: "
        f"{sorted(extra_annotations)}"
    )

if id_errors:
    raise ValueError("\n".join(id_errors))

print("\nquestion_id 검수 완료")


# =========================================================
# 10. 평가값 표기 통일
# =========================================================

def normalize_category(value):
    """
    대소문자, 공백, 하이픈 차이를 정리합니다.

    예:
    Minor Error -> minor_error
    minor-error -> minor_error
    NEED REVISION -> need_revision
    """

    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


annotations[ACCURACY_COLUMN] = (
    annotations[ACCURACY_COLUMN]
    .apply(normalize_category)
)

annotations[FINAL_LABEL_COLUMN] = (
    annotations[FINAL_LABEL_COLUMN]
    .apply(normalize_category)
)


# =========================================================
# 11. accuracy 허용값 확인
# =========================================================

invalid_accuracy_values = sorted(
    set(annotations[ACCURACY_COLUMN])
    - set(ACCURACY_ORDER)
)

if invalid_accuracy_values:
    raise ValueError(
        f"accuracy에 정해지지 않은 값이 있습니다: "
        f"{invalid_accuracy_values}\n"
        f"사용 가능한 값: {ACCURACY_ORDER}"
    )

print("accuracy 값 검수 완료")


# =========================================================
# 12. final_label 허용값 확인
# =========================================================

invalid_final_labels = sorted(
    set(annotations[FINAL_LABEL_COLUMN])
    - set(FINAL_LABEL_ORDER)
)

if invalid_final_labels:
    raise ValueError(
        f"final_label에 정해지지 않은 값이 있습니다: "
        f"{invalid_final_labels}\n"
        f"사용 가능한 값: {FINAL_LABEL_ORDER}"
    )

print("final_label 값 검수 완료")


# =========================================================
# 13. 세 데이터 연결
# =========================================================

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


# =========================================================
# 14. 요약표 생성 함수
# =========================================================

def create_summary(dataframe, column_name, value_order):
    """
    지정한 열의 항목별 개수와 비율을 계산합니다.
    """

    total_count = len(dataframe)

    counts = (
        dataframe[column_name]
        .value_counts()
        .reindex(value_order, fill_value=0)
    )

    summary = (
        counts
        .rename_axis(column_name)
        .reset_index(name="count")
    )

    summary["percentage"] = (
        summary["count"]
        / total_count
        * 100
    ).round(1)

    return summary


# =========================================================
# 15. final_label 전체 결과
# =========================================================

final_label_summary = create_summary(
    merged_data,
    FINAL_LABEL_COLUMN,
    FINAL_LABEL_ORDER,
)


# =========================================================
# 16. accuracy 전체 결과
# =========================================================

accuracy_summary = create_summary(
    merged_data,
    ACCURACY_COLUMN,
    ACCURACY_ORDER,
)


# =========================================================
# 17. query_type별 final_label 결과
# =========================================================

query_type_summary = pd.crosstab(
    merged_data[QUERY_TYPE_COLUMN],
    merged_data[FINAL_LABEL_COLUMN],
)

query_type_summary = query_type_summary.reindex(
    columns=FINAL_LABEL_ORDER,
    fill_value=0,
)

query_type_summary["total"] = (
    query_type_summary[FINAL_LABEL_ORDER]
    .sum(axis=1)
)

query_type_summary["pass_rate_percent"] = (
    query_type_summary["pass"]
    / query_type_summary["total"]
    * 100
).round(1)

query_type_summary = query_type_summary.reset_index()


# =========================================================
# 18. query_type별 accuracy 결과
# =========================================================

accuracy_by_query_type = pd.crosstab(
    merged_data[QUERY_TYPE_COLUMN],
    merged_data[ACCURACY_COLUMN],
)

accuracy_by_query_type = accuracy_by_query_type.reindex(
    columns=ACCURACY_ORDER,
    fill_value=0,
)

accuracy_by_query_type["total"] = (
    accuracy_by_query_type[ACCURACY_ORDER]
    .sum(axis=1)
)

accuracy_by_query_type["correct_rate_percent"] = (
    accuracy_by_query_type["correct"]
    / accuracy_by_query_type["total"]
    * 100
).round(1)

accuracy_by_query_type = (
    accuracy_by_query_type.reset_index()
)


# =========================================================
# 19. accuracy와 final_label 교차표
# =========================================================

accuracy_final_label_crosscheck = pd.crosstab(
    merged_data[ACCURACY_COLUMN],
    merged_data[FINAL_LABEL_COLUMN],
)

accuracy_final_label_crosscheck = (
    accuracy_final_label_crosscheck
    .reindex(
        index=ACCURACY_ORDER,
        columns=FINAL_LABEL_ORDER,
        fill_value=0,
    )
    .reset_index()
)


# =========================================================
# 20. 최종 판정상 검토가 필요한 사례
# =========================================================

review_cases = merged_data[
    merged_data[FINAL_LABEL_COLUMN] != "pass"
].copy()


# =========================================================
# 21. 정확성 오류 사례
# =========================================================

accuracy_error_cases = merged_data[
    merged_data[ACCURACY_COLUMN] != "correct"
].copy()


# =========================================================
# 22. 결과 파일 저장
# =========================================================

merged_data.to_csv(
    RESULTS_DIR / "combined_results.csv",
    index=False,
    encoding="utf-8-sig",
)

final_label_summary.to_csv(
    RESULTS_DIR / "final_label_summary.csv",
    index=False,
    encoding="utf-8-sig",
)

accuracy_summary.to_csv(
    RESULTS_DIR / "accuracy_summary.csv",
    index=False,
    encoding="utf-8-sig",
)

query_type_summary.to_csv(
    RESULTS_DIR / "query_type_summary.csv",
    index=False,
    encoding="utf-8-sig",
)

accuracy_by_query_type.to_csv(
    RESULTS_DIR / "accuracy_by_query_type.csv",
    index=False,
    encoding="utf-8-sig",
)

accuracy_final_label_crosscheck.to_csv(
    RESULTS_DIR
    / "accuracy_final_label_crosscheck.csv",
    index=False,
    encoding="utf-8-sig",
)

review_cases.to_csv(
    RESULTS_DIR / "review_cases.csv",
    index=False,
    encoding="utf-8-sig",
)

accuracy_error_cases.to_csv(
    RESULTS_DIR / "accuracy_error_cases.csv",
    index=False,
    encoding="utf-8-sig",
)


# =========================================================
# 23. 터미널에 결과 출력
# =========================================================

print("\n최종 판정 결과")
print(final_label_summary.to_string(index=False))

print("\n정확성 평가 결과")
print(accuracy_summary.to_string(index=False))

print("\nquery_type별 최종 판정")
print(query_type_summary.to_string(index=False))

print("\nquery_type별 정확성 평가")
print(accuracy_by_query_type.to_string(index=False))

print("\naccuracy와 final_label 교차 확인")
print(
    accuracy_final_label_crosscheck.to_string(
        index=False
    )
)

print(f"\n최종 검토 대상: {len(review_cases)}개")
print(
    f"정확성 오류 사례: {len(accuracy_error_cases)}개"
)
print(f"결과 저장 위치: {RESULTS_DIR}")