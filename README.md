# Korean Finance AI Evaluation

한국어 금융 생활정보를 대상으로 다음 두 가지를 평가한 프로젝트입니다.

1. LLM이 생성한 금융 답변의 정확성과 사용 가능성
2. TF-IDF 기반 한국어 금융 FAQ 검색 성능

신뢰할 수 있는 출처를 기반으로 평가 기준을 먼저 정의한 뒤 LLM 답변을 수동 어노테이션했습니다. 이후 동일한 금융 데이터를 FAQ 검색 데이터셋으로 확장하고, Word TF-IDF와 Character TF-IDF의 검색 성능을 비교했습니다.

## 1. 프로젝트 목적

금융 정보에 대한 LLM 답변이 사실에 부합하는지, 사용자의 판단에 필요한 핵심 내용을 충분히 포함하는지 확인하기 위해 진행했습니다.

답변의 문장이 자연스러운지만 확인하지 않고, 각 질문에 대해 다음 기준을 먼저 정의했습니다.

- 신뢰할 수 있는 출처
- 기준 답변
- 필수 포함 요소
- 중대한 오류 기준

이후 LLM 답변을 `accuracy`와 `final_label`로 나누어 평가했습니다.

답변 평가가 끝난 뒤에는 기존 금융 질문과 기준 답변을 FAQ 데이터로 확장했습니다. 사용자가 다양한 표현으로 질문했을 때 적절한 FAQ를 검색할 수 있는지 확인하기 위해 Word TF-IDF와 Character TF-IDF의 성능을 비교했습니다.

## 2. 프로젝트 개요

- 평가 분야: 한국어 금융 생활정보
- 주요 주제: CMA, MMF, 예금자보호, 세금, 금융상품 비교
- LLM 평가 질문: 15개
- 금융 FAQ: 15개
- FAQ 검색 질문: 45개
- 사용 모델: `Google Gemini Plus`
- 답변 생성 횟수: 질문당 1회
- 평가자 수: 1명
- LLM 평가 방식: 수동 어노테이션
- FAQ 검색 방식: Word TF-IDF, Character TF-IDF
- 진행 기간: `2026.10.15 ~ 2026.10.23`

## 3. 전체 진행 과정

```text
금융 질문 및 출처 조사
        ↓
기준 답변과 평가 기준 작성
        ↓
LLM 답변 수집
        ↓
답변 정확성 및 사용 가능성 어노테이션
        ↓
Python을 이용한 결과 집계
        ↓
금융 FAQ 검색 데이터셋 구축
        ↓
Word·Character TF-IDF 검색 구현
        ↓
Top-1·Hit@3·MRR 평가
        ↓
질문 유형별 성능 및 오류 사례 분석
```

## 4. 데이터 구성

원본 데이터는 `data/llm_evaluation.xlsx`에서 관리하고, `export_sheets.py`를 이용해 각 시트를 CSV로 변환합니다.

### `questions.csv`

LLM 답변 평가에 사용한 질문과 정답 기준을 저장합니다.

- `question_id`: 질문 고유 ID
- `question`: 사용자 질문
- `query_type`: 질문 유형
- `reference_url`: 기준 답변 작성에 사용한 출처
- `reference_summary`: 출처를 바탕으로 정리한 기준 답변
- `required_points`: 올바른 답변에 포함되어야 하는 핵심 내용
- `major_error_criteria`: 중대한 오류로 판단할 조건

### `model_responses.csv`

각 질문에 대한 LLM의 원본 답변을 저장합니다.

- `question_id`: 질문 ID
- `model_name`: 답변을 생성한 모델
- `response`: 모델이 생성한 원본 답변

### `annotations.csv`

LLM 답변을 평가한 결과를 저장합니다.

- `question_id`: 질문 ID
- `accuracy`: 사실 정확성 평가
- `final_label`: 답변의 최종 사용 가능 여부
- `evaluation_reason`: 평가 결과에 대한 근거

`accuracy`에는 다음 값을 사용합니다.

```text
correct
minor_error
major_error
```

`final_label`에는 다음 값을 사용합니다.

```text
pass
need_revision
fail
```

### `faq_corpus.csv`

FAQ 검색 대상이 되는 금융 질문과 답변을 저장합니다.

- `faq_id`: FAQ 고유 ID
- `category`: 금융 주제
- `faq_question`: FAQ 대표 질문
- `faq_answer`: 출처를 바탕으로 작성한 FAQ 답변
- `source_url`: 답변의 출처

### `search_queries.csv`

FAQ 검색 성능 평가에 사용하는 검색 질문을 저장합니다.

- `query_id`: 검색 질문 고유 ID
- `query_text`: 사용자가 입력하는 검색 질문
- `gold_faq_id`: 검색되어야 하는 정답 FAQ
- `query_type`: 검색 질문의 표현 유형

검색 질문은 다음 세 가지 유형으로 구성했습니다.

- `direct`: FAQ 대표 질문과 직접적으로 유사한 문장
- `paraphrase`: 같은 의미를 다른 표현으로 작성한 문장
- `keyword`: 핵심 단어로 구성한 짧은 검색어

## 5. LLM 답변 평가 기준

LLM 답변은 사실 정확성을 나타내는 `accuracy`와 실제 사용 가능성을 나타내는 `final_label`로 나누어 평가했습니다.

### Accuracy

#### `correct`

핵심 내용이 기준 답변과 일치하고 사용자의 판단에 영향을 주는 사실 오류가 없는 경우입니다.

#### `minor_error`

핵심 결론은 맞지만 일부 부가 조건이 누락되었거나, 사용자의 판단을 크게 바꾸지 않는 경미한 부정확성이 있는 경우입니다.

#### `major_error`

기준 답변과 반대되는 결론을 제시하거나 중요한 조건을 잘못 설명해 사용자가 잘못된 판단을 내릴 수 있는 경우입니다.

### Final Label

#### `pass`

핵심 내용이 정확하고 필요한 설명을 충분히 포함해 별도의 수정 없이 사용할 수 있는 답변입니다.

#### `need_revision`

핵심 결론은 맞지만 조건 누락, 불완전한 설명 또는 경미한 오류가 있어 일부 수정이 필요한 답변입니다.

#### `fail`

중대한 사실 오류가 있거나 핵심 질문에 답하지 못해 그대로 사용하기 어려운 답변입니다.

## 6. LLM 답변 평가 결과

총 15개의 LLM 답변을 평가한 결과는 다음과 같습니다.

| Final Label | 개수 | 비율 |
| --- | ---: | ---: |
| `pass` | 9 | 60.0% |
| `need_revision` | 6 | 40.0% |
| `fail` | 0 | 0.0% |
| 전체 | 15 | 100.0% |

9개 답변은 별도의 수정 없이 사용할 수 있는 `pass`, 6개 답변은 일부 수정이 필요한 `need_revision`으로 평가했습니다. 중대한 오류로 인해 사용할 수 없는 `fail` 답변은 발견되지 않았습니다.

이 결과는 본 프로젝트에서 구성한 15개 질문과 한 번씩 생성한 답변에 대한 결과이며, 해당 모델의 일반적인 금융 답변 성능을 의미하지 않습니다.

## 7. LLM 답변 평가 사례

### 질문

`CMA란 무엇인가요?`

### 기준 답변

CMA(Cash Management Account)는 주로 증권사에서 개설하는 자산관리계좌로, 입금한 자금을 RP, MMF, MMW, 발행어음 등의 단기금융상품에 자동으로 운용하는 구조다. 비교적 자유롭게 입출금할 수 있어 투자 전 대기자금이나 단기 여유 자금 관리에 활용된다. 수익률, 예금자보호 여부와 출금 조건은 CMA 유형 및 금융회사에 따라 다르다.

### 필수 포함 내용

- 주로 증권사에서 개설할 수 있는 자산관리계좌
- 단기금융상품에 자금을 운용하는 구조
- 비교적 자유로운 입출금
- 유형별 위험과 수익률 차이

### 최종 평가

`pass`

### 평가 근거

LLM 답변이 CMA의 핵심 개념과 활용 목적을 정확하게 설명했고, 사전에 정의한 필수 내용을 포함했습니다. 기준 답변과 반대되는 설명이나 사용자의 판단에 영향을 줄 수 있는 오류가 발견되지 않아 `pass`로 평가했습니다.

## 8. FAQ 검색 성능 평가

### 검색 방식

#### Word TF-IDF

문장을 단어 단위로 나누고 검색 질문과 FAQ에 공통으로 등장하는 단어를 중심으로 유사도를 계산합니다.

#### Character TF-IDF

문장을 연속된 글자 조각으로 나누고 글자 패턴의 유사도를 계산합니다. 한국어의 조사, 어미, 띄어쓰기 및 구분 기호 차이를 일부 반영할 수 있습니다.

FAQ의 대표 질문과 답변을 결합한 텍스트를 검색 대상으로 사용하고, 코사인 유사도를 기준으로 검색 결과의 순위를 결정했습니다.

### 평가 지표

- `Top-1 Accuracy`: 첫 번째 검색 결과가 정답인 비율
- `Hit@3`: 상위 3개 검색 결과 안에 정답이 포함된 비율
- `MRR`: 정답 FAQ가 전체적으로 얼마나 높은 순위에 나타나는지를 보여주는 지표

### 전체 검색 성능

| 검색 방식 | 질문 수 | Top-1 Accuracy | Hit@3 | MRR |
| --- | ---: | ---: | ---: | ---: |
| Character TF-IDF | 45 | 60.00% | 86.67% | 0.7308 |
| Word TF-IDF | 45 | 48.89% | 66.67% | 0.6132 |

Character TF-IDF는 45개 질문 중 27개에서 정답 FAQ를 첫 번째 결과로 검색했습니다. Word TF-IDF는 22개 질문에서 정답을 첫 번째 결과로 검색했습니다.

Character TF-IDF의 Top-1 Accuracy는 Word TF-IDF보다 11.11%p 높았고, Hit@3는 20.00%p 높았습니다. MRR도 Character TF-IDF가 0.1176 높아 정답 FAQ를 전반적으로 더 높은 순위에 배치했습니다.

이번 데이터셋에서는 단어 전체보다 글자 단위 패턴을 비교한 방식이 더 높은 검색 성능을 보였습니다.

### 질문 유형별 검색 성능

| 검색 방식 | 질문 유형 | 질문 수 | Top-1 Accuracy | Hit@3 | MRR |
| --- | --- | ---: | ---: | ---: | ---: |
| Character TF-IDF | Direct | 15 | 93.33% | 100.00% | 0.9667 |
| Character TF-IDF | Paraphrase | 15 | 33.33% | 80.00% | 0.5622 |
| Character TF-IDF | Keyword | 15 | 53.33% | 80.00% | 0.6636 |
| Word TF-IDF | Direct | 15 | 93.33% | 100.00% | 0.9667 |
| Word TF-IDF | Paraphrase | 15 | 33.33% | 53.33% | 0.4816 |
| Word TF-IDF | Keyword | 15 | 20.00% | 46.67% | 0.3912 |

### 유형별 Top-1 오류 개수

| 질문 유형 | Character TF-IDF | Word TF-IDF |
| --- | ---: | ---: |
| Direct | 1개 | 1개 |
| Paraphrase | 10개 | 10개 |
| Keyword | 7개 | 12개 |
| 전체 | 18개 | 23개 |

#### Direct 질문

두 검색 방식 모두 Direct 질문에서 93.33%의 Top-1 Accuracy와 100%의 Hit@3를 기록했습니다. FAQ 대표 질문과 검색 질문의 표현이 비슷해 대부분 정답을 높은 순위로 검색했습니다.

#### Paraphrase 질문

두 방식 모두 Paraphrase 질문의 Top-1 Accuracy가 33.33%로 가장 낮았습니다. 각각 15개 중 5개만 정답 FAQ를 첫 번째 결과로 검색했습니다.

Character TF-IDF도 정답을 첫 번째 결과로 배치하는 데는 어려움이 있었지만, Hit@3는 80.00%로 Word TF-IDF의 53.33%보다 높았습니다. 정답을 상위 3개 후보에 포함하는 성능은 Character TF-IDF가 상대적으로 높았습니다.

#### Keyword 질문

Keyword 질문에서 두 검색 방식의 차이가 가장 크게 나타났습니다.

- Character TF-IDF: 15개 중 8개 정답
- Word TF-IDF: 15개 중 3개 정답

Character TF-IDF의 Top-1 Accuracy와 Hit@3는 Word TF-IDF보다 각각 33.33%p 높았습니다. MRR도 Character TF-IDF가 0.2724 높았습니다.

Word TF-IDF만 실패하고 Character TF-IDF는 성공한 질문은 다음 5개였습니다.

- `CMA 전체 예금자보호 여부`
- `CMA 고정금리 여부`
- `MMF 예금자보호 여부`
- `MMF 카드결제 자동이체 ATM`
- `CMA 파킹통장 차이`

이번 데이터에서는 짧은 한국어 검색어를 처리할 때 글자 단위 패턴을 비교하는 방식이 더 효과적인 것으로 나타났습니다.

## 9. FAQ 검색 오류 분석

Character TF-IDF에서는 18개, Word TF-IDF에서는 23개의 Top-1 오류가 발생했습니다.

Character TF-IDF가 틀린 18개 질문은 Word TF-IDF에서도 모두 틀렸습니다. 반면 Word TF-IDF만 틀리고 Character TF-IDF는 맞힌 질문은 5개였으며, 모두 Keyword 유형이었습니다.

### 대표 검색 오류 사례

| ID | 검색 질문 | 방식 | 정답 FAQ | 첫 번째 검색 결과 | 정답 순위 |
| --- | --- | --- | --- | --- | ---: |
| SQ019 | 종금형 CMA는 예금자보호 대상인가요? | 두 방식 | 종금형 CMA는 예금자보호가 되나요? | MMF는 예금자보호 대상인가요? | 2위 |
| SQ012 | CMA MMF 차이 | Character | CMA와 MMF는 같은 금융상품인가요? | 투자 경험이 없는 사람에게 CMA와 MMF 중 어느 쪽이 더 적합한가요? | 5위 |
| SQ012 | CMA MMF 차이 | Word | CMA와 MMF는 같은 금융상품인가요? | 투자 경험이 없는 사람에게 CMA와 MMF 중 어느 쪽이 더 적합한가요? | 13위 |
| SQ023 | MMF에 넣은 돈도 예금처럼 보호받을 수 있나요? | 두 방식 | MMF는 예금자보호 대상인가요? | 종금형 CMA는 예금자보호가 되나요? | 10위 |
| SQ027 | MMF 카드결제 자동이체 ATM | Word | MMF에서 카드결제·자동이체·ATM 출금이 가능한가요? | 투자 경험이 없는 사람에게 CMA와 MMF 중 어느 쪽이 더 적합한가요? | 7위 |
| SQ041 | 곧 사용할 단기 자금을 MMF에 보관해도 괜찮나요? | Character | 한 달 뒤 납부할 등록금 300만원을 MMF에 넣어도 될까요? | MMF에서 카드결제·자동이체·ATM 출금이 가능한가요? | 2위 |
| SQ041 | 곧 사용할 단기 자금을 MMF에 보관해도 괜찮나요? | Word | 한 달 뒤 납부할 등록금 300만원을 MMF에 넣어도 될까요? | RP형 CMA와 MMF형 CMA는 어떤 자산에 투자하나요? | 4위 |

### SQ019 분석

SQ019는 두 검색 방식 모두에서 실패한 유일한 Direct 질문입니다.

```text
검색 질문:
종금형 CMA는 예금자보호 대상인가요?

정답 FAQ:
종금형 CMA는 예금자보호가 되나요?

첫 번째 검색 결과:
MMF는 예금자보호 대상인가요?
```

Character TF-IDF에서 첫 번째 결과의 유사도는 0.2642, 정답 FAQ의 유사도는 0.2611로 차이가 0.0031에 불과했습니다.

Word TF-IDF에서도 첫 번째 결과는 0.1538, 정답 FAQ는 0.1511로 매우 유사했습니다.

두 FAQ에 `예금자보호 대상인가요`라는 표현이 공통으로 포함되어 있어, 금융상품을 구분하는 `종금형 CMA`와 `MMF`보다 공통된 질문 표현이 검색 순위에 더 크게 반영된 것으로 보입니다.

정답은 두 방식에서 모두 2위에 있어 Hit@3에는 성공했지만, 유사한 FAQ 사이의 순위 결정에는 개선이 필요했습니다.

### 주요 오류 원인

#### 비슷한 금융 주제 간 혼동

예금자보호 관련 FAQ에는 `CMA`, `MMF`, `예금자보호`와 같은 단어가 반복됩니다. 이 때문에 전체 CMA에 대한 질문, 특정 CMA 유형에 대한 질문, MMF에 대한 질문을 서로 혼동하는 사례가 발생했습니다.

#### 비교와 추천 의도 구분 실패

`CMA MMF 차이`의 정답은 두 상품의 차이를 설명하는 FAQ입니다. 그러나 검색 시스템은 CMA와 MMF 중 적합한 상품을 선택하는 FAQ를 첫 번째 결과로 제시했습니다.

두 FAQ에 CMA와 MMF가 모두 포함되어 있어 TF-IDF만으로는 `상품 비교`와 `상품 추천`이라는 의도 차이를 충분히 구분하지 못했습니다.

#### 한국어 조사와 띄어쓰기

Word TF-IDF는 `CMA`와 `CMA에는`, `파킹통장`과 `파킹통장은`을 서로 다른 단어로 처리할 수 있습니다.

Character TF-IDF는 단어의 일부 글자 패턴을 비교하기 때문에 Keyword 질문에서 Word TF-IDF보다 높은 성능을 보인 것으로 추정됩니다.

#### 의미는 같지만 표현이 다른 질문

`곧 사용할 단기 자금`과 `한 달 뒤 납부할 등록금`은 단기 자금 보관이라는 의미는 유사하지만 직접적으로 겹치는 단어가 적습니다.

TF-IDF는 문장의 의미보다 단어와 글자 패턴의 일치를 중심으로 검색하기 때문에 이러한 Paraphrase 질문에서 낮은 Top-1 Accuracy를 보였습니다.

#### FAQ 답변에 포함된 공통 단어의 영향

현재 검색에서는 FAQ 대표 질문뿐 아니라 답변도 검색 문서에 포함합니다. 정답이 아닌 FAQ 답변에 검색어와 같은 금융 용어가 반복되면 해당 FAQ의 검색 순위가 높아질 수 있습니다.

## 10. 프로젝트 구조

```text
Korean-finance-AI-evaluation/
├─ data/
│  ├─ llm_evaluation.xlsx
│  ├─ questions.csv
│  ├─ model_responses.csv
│  ├─ annotations.csv
│  ├─ faq_corpus.csv
│  └─ search_queries.csv
│
├─ guidelines/
├─ report/
│
├─ results/
│  ├─ combined_results.csv
│  ├─ final_label_summary.csv
│  ├─ accuracy_summary.csv
│  ├─ query_type_summary.csv
│  ├─ accuracy_by_query_type.csv
│  ├─ accuracy_final_label_crosscheck.csv
│  ├─ review_cases.csv
│  ├─ accuracy_error_cases.csv
│  ├─ search_results.csv
│  ├─ search_metrics.csv
│  ├─ search_metrics_by_query_type.csv
│  └─ search_error_cases.csv
│
├─ scripts/
│
├─ src/
│  ├─ export_sheets.py
│  ├─ analyze.py
│  └─ evaluate_search.py
│
├─ .gitignore
├─ README.md
└─ requirements.txt
```

### 주요 파일의 역할

- `export_sheets.py`: 원본 엑셀의 각 시트를 CSV로 변환
- `analyze.py`: LLM 답변 평가 결과 집계
- `evaluate_search.py`: FAQ 검색 실행 및 검색 성능 평가
- `combined_results.csv`: 질문, LLM 답변 및 평가 결과를 결합한 파일
- `search_results.csv`: 각 검색 질문의 검색 결과와 정답 순위
- `search_metrics.csv`: 검색 방식별 전체 성능
- `search_metrics_by_query_type.csv`: 검색 방식과 질문 유형별 성능
- `search_error_cases.csv`: 정답 FAQ가 첫 번째로 검색되지 않은 사례

## 11. 실행 방법

### 실행 환경

- Python 3.10 이상
- Git
- Excel 파일을 열 수 있는 프로그램(선택 사항)

### 1. 저장소 내려받기

```bash
git clone https://github.com/sxxbxxny/Korean-finance-AI-evaluation.git
cd Korean-finance-AI-evaluation
```

### 2. 가상환경 생성

#### Windows

```bash
py -m venv .venv
```

#### macOS/Linux

```bash
python3 -m venv .venv
```

### 3. 필요한 라이브러리 설치

`requirements.txt`에는 다음 라이브러리가 포함되어 있습니다.

```text
pandas
openpyxl
scikit-learn
```

#### Windows

```bash
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

#### macOS/Linux

```bash
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

### 4. 엑셀 시트를 CSV로 내보내기

#### Windows

```bash
.venv\Scripts\python.exe src\export_sheets.py
```

#### macOS/Linux

```bash
.venv/bin/python src/export_sheets.py
```

실행이 완료되면 `data/` 폴더의 다음 파일이 생성되거나 최신 내용으로 갱신됩니다.

```text
questions.csv
model_responses.csv
annotations.csv
faq_corpus.csv
search_queries.csv
```

### 5. LLM 답변 평가 결과 분석

#### Windows

```bash
.venv\Scripts\python.exe src\analyze.py
```

#### macOS/Linux

```bash
.venv/bin/python src/analyze.py
```

### 6. FAQ 검색 성능 평가

#### Windows

```bash
.venv\Scripts\python.exe src\evaluate_search.py
```

#### macOS/Linux

```bash
.venv/bin/python src/evaluate_search.py
```

검색 평가가 완료되면 다음 파일이 생성됩니다.

```text
results/search_results.csv
results/search_metrics.csv
results/search_metrics_by_query_type.csv
results/search_error_cases.csv
```

### 전체 실행 순서

```text
llm_evaluation.xlsx 수정
        ↓
export_sheets.py 실행
        ↓
data 폴더의 CSV 갱신
        ↓
analyze.py 실행
        ↓
LLM 답변 평가 결과 생성
        ↓
evaluate_search.py 실행
        ↓
FAQ 검색 성능 평가 결과 생성
```

### 데이터를 수정한 경우

엑셀 파일을 저장하고 닫은 뒤 다음 명령어를 순서대로 다시 실행합니다.

#### Windows

```bash
.venv\Scripts\python.exe src\export_sheets.py
.venv\Scripts\python.exe src\analyze.py
.venv\Scripts\python.exe src\evaluate_search.py
```

#### macOS/Linux

```bash
.venv/bin/python src/export_sheets.py
.venv/bin/python src/analyze.py
.venv/bin/python src/evaluate_search.py
```

> `data/`와 `results/`의 CSV 파일은 실행 과정에서 최신 결과로 갱신될 수 있습니다.

## 12. 사용 기술

- Python
- pandas
- openpyxl
- scikit-learn
- TF-IDF
- Cosine Similarity
- Excel
- CSV
- Git/GitHub

## 13. 프로젝트 한계

### LLM 답변 평가

- 평가 질문이 15개로 제한적입니다.
- 하나의 LLM 답변만 평가했습니다.
- 각 질문에 대해 한 번 생성된 답변만 평가했습니다.
- 한 명이 평가 기준 작성과 답변 평가를 모두 진행했습니다.
- 비교적 명확한 금융 질문을 중심으로 구성했습니다.

따라서 이번 결과를 해당 모델의 일반적인 금융 답변 성능으로 확대해 해석하기 어렵습니다.

### FAQ 검색 평가

- 15개의 FAQ와 45개의 검색 질문으로 구성한 소규모 평가입니다.
- FAQ와 검색 질문을 한 명이 작성해 작성자의 표현 방식이 결과에 반영되었을 수 있습니다.
- Direct 질문은 FAQ 대표 질문과 표현이 유사해 전체 검색 성능을 높이는 요인이 될 수 있습니다.
- 하나의 검색 질문에 하나의 정답 FAQ만 지정해 관련성이 있는 다른 FAQ도 오답으로 처리될 수 있습니다.
- TF-IDF는 단어와 글자 패턴을 중심으로 검색하므로 문장의 의미와 검색 의도를 충분히 반영하지 못합니다.

## 14. 향후 개선 방향

### LLM 답변 평가

- 조건이 복잡하거나 사용자의 오해를 포함한 질문 추가
- 여러 LLM의 답변을 동일한 기준으로 비교
- 동일 질문을 여러 번 실행해 답변 일관성 확인
- 복수 평가자를 통한 평가 결과 비교
- 오류 유형을 사실 오류, 조건 누락, 과도한 일반화 등으로 세분화
- 질문과 평가 데이터 규모 확대

### FAQ 검색 평가

- FAQ 질문만 사용한 결과와 질문·답변을 함께 사용한 결과 비교
- FAQ 질문과 답변에 서로 다른 가중치 적용
- 한국어 형태소 분석을 적용한 Word TF-IDF 성능 비교
- 문장 임베딩 기반 의미 검색 추가
- TF-IDF와 의미 검색의 성능 비교
- 유사도 점수 차이가 작을 때 상위 3개 FAQ를 함께 제공하는 방식 적용
- 오타, 구어체 및 실제 사용자 표현을 반영한 검색 질문 추가