QUESTION_TYPE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("documents", ("서류", "구비서류", "준비서류", "필요한 서류")),
    ("period", ("며칠", "기간", "언제까지", "기한")),
    ("numeric", ("얼마", "몇", "이율", "비율", "환급률", "수치")),
    ("definition", ("무엇", "뜻", "의미", "정의")),
    ("conditions", ("누구", "대상", "조건", "경우")),
    ("comparison", ("비교", "차이", "구분")),
]


DOCUMENT_HINT_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "pricing_method": {
        "keywords": (
            "산출방법서",
            "적용 이율",
            "적용이율",
            "연복리",
            "기초율",
            "해지율",
            "환급률",
            "계약체결비용",
            "계약관리비용",
            "영업보험료",
            "m과 t",
        ),
        "query_expansions": (
            "산출방법서",
            "산출방법서 적용 이율",
            "산출방법서 연복리",
            "보험료 및 해약환급금 산출방법서",
            "기초율",
        ),
    },
    "terms": {
        "keywords": (
            "약관",
            "청약 철회",
            "청약철회",
            "보험계약",
            "납입한도",
            "승낙",
            "거절",
            "자필서명",
        ),
        "query_expansions": (
            "약관",
            "보통보험약관",
            "보험계약",
            "보통보험약관 청약 철회",
            "약관 청약철회 기간",
        ),
    },
    "change_process": {
        "keywords": (
            "계약자 변경",
            "계약자변경",
            "계약관계자변경",
            "대리인",
            "동의 대상",
            "동의대상",
            "구비서류",
            "상세동의서",
        ),
        "query_expansions": (
            "계약관계자변경",
            "계약자 변경",
            "계약자 변경 구비서류",
            "계약자 변경 동의 대상",
        ),
    },
}


QUESTION_TYPE_QUERY_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "documents": ("구비서류", "필요서류", "준비서류"),
    "period": ("기간", "며칠", "기한"),
    "numeric": ("얼마", "수치", "기준 값"),
}


def infer_question_type_from_rules(query: str) -> str | None:
    lowered_query = query.lower()
    for question_type, keywords in QUESTION_TYPE_RULES:
        if any(keyword in query or keyword in lowered_query for keyword in keywords):
            return question_type
    return None


def infer_document_hint_from_rules(text: str) -> str | None:
    lowered_text = text.lower()
    for document_hint, rule in DOCUMENT_HINT_RULES.items():
        keywords = rule.get("keywords", ())
        if any(keyword in lowered_text for keyword in keywords):
            return document_hint
    return None


def get_document_hint_expansions(document_hint: str | None) -> list[str]:
    if not document_hint:
        return []
    rule = DOCUMENT_HINT_RULES.get(document_hint, {})
    expansions = rule.get("query_expansions", ())
    return [str(item).strip() for item in expansions if str(item).strip()]


def get_question_type_expansions(question_type: str | None) -> list[str]:
    if not question_type:
        return []
    expansions = QUESTION_TYPE_QUERY_EXPANSIONS.get(question_type, ())
    return [str(item).strip() for item in expansions if str(item).strip()]
