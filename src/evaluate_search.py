from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FAQ_PATH = PROJECT_ROOT / "data" / "faq_corpus.csv"
QUERY_PATH = PROJECT_ROOT / "data" / "search_queries.csv"
RESULTS_DIR = PROJECT_ROOT / "results"

ALLOWED_QUERY_TYPES = {
    "direct",
    "paraphrase",
    "keyword",
}


def load_csv(file_path: Path) -> pd.DataFrame:
    """CSV 파일을 문자열 형식으로 불러오고 공백을 정리한다."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다: {file_path}"
        )

    dataframe = pd.read_csv(
        file_path,
        dtype=str,
        encoding="utf-8-sig",
    ).fillna("")

    dataframe.columns = [
        str(column).strip()
        for column in dataframe.columns
    ]

    for column in dataframe.columns:
        dataframe[column] = dataframe[column].str.strip()

    return dataframe


def validate_columns(
    dataframe: pd.DataFrame,
    required_columns: list[str],
    file_name: str,
) -> None:
    """필요한 열이 모두 존재하는지 확인한다."""

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{file_name}에 필요한 열이 없습니다: "
            + ", ".join(missing_columns)
        )


def validate_data(
    faq_dataframe: pd.DataFrame,
    query_dataframe: pd.DataFrame,
) -> None:
    """FAQ와 검색 질문 데이터의 오류를 검사한다."""

    faq_required_columns = [
        "faq_id",
        "category",
        "faq_question",
        "faq_answer",
        "source_url",
    ]

    query_required_columns = [
        "query_id",
        "query_text",
        "gold_faq_id",
        "query_type",
    ]

    validate_columns(
        faq_dataframe,
        faq_required_columns,
        "faq_corpus.csv",
    )

    validate_columns(
        query_dataframe,
        query_required_columns,
        "search_queries.csv",
    )

    # FAQ ID 중복 확인
    duplicated_faq_ids = faq_dataframe.loc[
        faq_dataframe["faq_id"].duplicated(),
        "faq_id",
    ].tolist()

    if duplicated_faq_ids:
        raise ValueError(
            "중복된 faq_id가 있습니다: "
            + ", ".join(duplicated_faq_ids)
        )

    # 검색 질문 ID 중복 확인
    duplicated_query_ids = query_dataframe.loc[
        query_dataframe["query_id"].duplicated(),
        "query_id",
    ].tolist()

    if duplicated_query_ids:
        raise ValueError(
            "중복된 query_id가 있습니다: "
            + ", ".join(duplicated_query_ids)
        )

    # 필수 값의 빈칸 확인
    faq_empty_columns = [
        column
        for column in faq_required_columns
        if (faq_dataframe[column] == "").any()
    ]

    if faq_empty_columns:
        raise ValueError(
            "faq_corpus.csv에 빈 값이 있는 열이 있습니다: "
            + ", ".join(faq_empty_columns)
        )

    query_empty_columns = [
        column
        for column in query_required_columns
        if (query_dataframe[column] == "").any()
    ]

    if query_empty_columns:
        raise ValueError(
            "search_queries.csv에 빈 값이 있는 열이 있습니다: "
            + ", ".join(query_empty_columns)
        )

    # gold_faq_id가 실제 FAQ에 존재하는지 확인
    faq_ids = set(faq_dataframe["faq_id"])
    gold_faq_ids = set(query_dataframe["gold_faq_id"])

    unknown_faq_ids = sorted(gold_faq_ids - faq_ids)

    if unknown_faq_ids:
        raise ValueError(
            "faq_corpus.csv에 존재하지 않는 gold_faq_id가 있습니다: "
            + ", ".join(unknown_faq_ids)
        )

    # query_type 오타 확인
    query_types = set(query_dataframe["query_type"])
    unknown_query_types = sorted(
        query_types - ALLOWED_QUERY_TYPES
    )

    if unknown_query_types:
        raise ValueError(
            "정해지지 않은 query_type이 있습니다: "
            + ", ".join(unknown_query_types)
            + "\n사용 가능한 값: "
            + ", ".join(sorted(ALLOWED_QUERY_TYPES))
        )


def evaluate_method(
    method_name: str,
    vectorizer: TfidfVectorizer,
    faq_dataframe: pd.DataFrame,
    query_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """하나의 TF-IDF 검색 방식으로 전체 질문을 평가한다."""

    # FAQ의 대표 질문과 답변을 하나의 검색 문서로 결합
    faq_documents = (
        faq_dataframe["faq_question"]
        + " "
        + faq_dataframe["faq_answer"]
    ).tolist()

    query_texts = query_dataframe["query_text"].tolist()

    # FAQ 문서를 기준으로 TF-IDF 학습
    faq_vectors = vectorizer.fit_transform(faq_documents)

    # 검색 질문을 동일한 TF-IDF 형식으로 변환
    query_vectors = vectorizer.transform(query_texts)

    # 각 검색 질문과 FAQ 간의 코사인 유사도 계산
    similarities = cosine_similarity(
        query_vectors,
        faq_vectors,
    )

    faq_ids = faq_dataframe["faq_id"].tolist()
    faq_questions = faq_dataframe["faq_question"].tolist()

    faq_question_by_id = dict(
        zip(faq_ids, faq_questions)
    )

    evaluation_rows = []

    for query_index, query_row in query_dataframe.iterrows():
        scores = similarities[query_index]

        # 유사도가 높은 FAQ부터 정렬
        ranked_indices = scores.argsort()[::-1]

        gold_faq_id = query_row["gold_faq_id"]

        gold_rank = next(
            rank
            for rank, faq_index in enumerate(
                ranked_indices,
                start=1,
            )
            if faq_ids[faq_index] == gold_faq_id
        )

        top_indices = ranked_indices[:3]

        top_faq_ids = [
            faq_ids[index]
            for index in top_indices
        ]

        top_scores = [
            f"{scores[index]:.4f}"
            for index in top_indices
        ]

        predicted_index = ranked_indices[0]
        predicted_faq_id = faq_ids[predicted_index]

        top1_correct = predicted_faq_id == gold_faq_id
        hit_at_3 = gold_faq_id in top_faq_ids
        reciprocal_rank = 1 / gold_rank

        evaluation_rows.append(
            {
                "method": method_name,
                "query_id": query_row["query_id"],
                "query_type": query_row["query_type"],
                "query_text": query_row["query_text"],
                "gold_faq_id": gold_faq_id,
                "gold_faq_question": faq_question_by_id[
                    gold_faq_id
                ],
                "predicted_faq_id": predicted_faq_id,
                "predicted_faq_question": faq_questions[
                    predicted_index
                ],
                "top1_score": round(
                    float(scores[predicted_index]),
                    4,
                ),
                "gold_rank": gold_rank,
                "top1_correct": top1_correct,
                "hit_at_3": hit_at_3,
                "reciprocal_rank": round(
                    reciprocal_rank,
                    4,
                ),
                "top3_faq_ids": "; ".join(top_faq_ids),
                "top3_scores": "; ".join(top_scores),
            }
        )

    return pd.DataFrame(evaluation_rows)


def make_overall_summary(
    results_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """검색 방식별 전체 성능을 집계한다."""

    summary = (
        results_dataframe
        .groupby("method", sort=False)
        .agg(
            query_count=("query_id", "count"),
            top1_accuracy=("top1_correct", "mean"),
            hit_at_3=("hit_at_3", "mean"),
            mrr=("reciprocal_rank", "mean"),
        )
        .reset_index()
    )

    metric_columns = [
        "top1_accuracy",
        "hit_at_3",
        "mrr",
    ]

    summary[metric_columns] = summary[
        metric_columns
    ].round(4)

    return summary


def make_query_type_summary(
    results_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """검색 질문 유형별 성능을 집계한다."""

    summary = (
        results_dataframe
        .groupby(
            ["method", "query_type"],
            sort=False,
        )
        .agg(
            query_count=("query_id", "count"),
            top1_accuracy=("top1_correct", "mean"),
            hit_at_3=("hit_at_3", "mean"),
            mrr=("reciprocal_rank", "mean"),
        )
        .reset_index()
    )

    metric_columns = [
        "top1_accuracy",
        "hit_at_3",
        "mrr",
    ]

    summary[metric_columns] = summary[
        metric_columns
    ].round(4)

    return summary


def save_results(
    results_dataframe: pd.DataFrame,
) -> None:
    """전체 검색 결과와 요약 결과를 CSV로 저장한다."""

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    overall_summary = make_overall_summary(
        results_dataframe
    )

    query_type_summary = make_query_type_summary(
        results_dataframe
    )

    error_cases = results_dataframe.loc[
        ~results_dataframe["top1_correct"]
    ].copy()

    results_dataframe.to_csv(
        RESULTS_DIR / "search_results.csv",
        index=False,
        encoding="utf-8-sig",
    )

    overall_summary.to_csv(
        RESULTS_DIR / "search_metrics.csv",
        index=False,
        encoding="utf-8-sig",
    )

    query_type_summary.to_csv(
        RESULTS_DIR / "search_metrics_by_query_type.csv",
        index=False,
        encoding="utf-8-sig",
    )

    error_cases.to_csv(
        RESULTS_DIR / "search_error_cases.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("\n검색 성능 평가 결과")

    for _, row in overall_summary.iterrows():
        print(f"\n[{row['method']}]")
        print(f"질문 수: {int(row['query_count'])}")
        print(
            "Top-1 Accuracy: "
            f"{row['top1_accuracy']:.2%}"
        )
        print(
            f"Hit@3: {row['hit_at_3']:.2%}"
        )
        print(f"MRR: {row['mrr']:.4f}")

    print("\n생성된 결과 파일")

    print("- results/search_results.csv")
    print("- results/search_metrics.csv")
    print(
        "- results/"
        "search_metrics_by_query_type.csv"
    )
    print("- results/search_error_cases.csv")


def main() -> None:
    faq_dataframe = load_csv(FAQ_PATH)
    query_dataframe = load_csv(QUERY_PATH)

    validate_data(
        faq_dataframe,
        query_dataframe,
    )

    search_methods = {
        "word_tfidf": TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b\w+\b",
            sublinear_tf=True,
        ),
        "char_tfidf": TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            sublinear_tf=True,
        ),
    }

    method_results = []

    for method_name, vectorizer in search_methods.items():
        result = evaluate_method(
            method_name,
            vectorizer,
            faq_dataframe,
            query_dataframe,
        )

        method_results.append(result)

    combined_results = pd.concat(
        method_results,
        ignore_index=True,
    )

    combined_results = combined_results.sort_values(
        by=["method", "query_id"]
    ).reset_index(drop=True)

    save_results(combined_results)


if __name__ == "__main__":
    main()