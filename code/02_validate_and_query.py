"""
=============================================================
 [단계 7] 검증 및 평가 — 추론 + 역량질문(SPARQL) 실행
 『지식그래프: AI와 온톨로지로 여는 지식혁명』 3장 8단계 방법론 (해사 도메인)

 1) maritime_ontology.ttl 로드
 2) 추론(reasoning) 전 역량질문 실행 → 명시된 사실만 반환
 3) owlrl OWL RL 추론기 적용 (이행·역·대칭·하위 속성 자동 도출)
 4) 추론 후 역량질문 재실행 → 암묵적 지식이 명시적 지식으로 도출됨을 확인

 실행:  python 02_validate_and_query.py
 필요:  pip install rdflib owlrl
=============================================================
"""
from rdflib import Graph, Namespace
import owlrl

MAR = Namespace("http://maritime-kg.example.org/ontology/maritime#")
PREFIX = "PREFIX : <http://maritime-kg.example.org/ontology/maritime#>"

# 역량질문 (competency_questions.sparql 와 동일)
QUERIES = {
    "CQ1  부산항에 입항한 선박": f"""
        {PREFIX}
        SELECT ?name WHERE {{
            ?v :hasPortCall ?pc ; :hasName ?name .
            ?pc :atPort :BusanPort .
        }} ORDER BY ?name
    """,
    "CQ2  총톤수 5,000 이상 유조선": f"""
        {PREFIX}
        SELECT ?name ?gt WHERE {{
            ?v :hasVesselType :T_Tanker ; :hasGrossTonnage ?gt ; :hasName ?name .
            FILTER (?gt >= 5000)
        }} ORDER BY DESC(?gt)
    """,
    "CQ3  [추론] 제15조제1항제3호의 상위 단위 (이행적 isPartOf)": f"""
        {PREFIX}
        SELECT ?unit WHERE {{ :Art15_P1_I3 :isPartOf ?unit . }}
    """,
    "CQ4  [추론] 부산신항 제3선석의 상위 지역 (이행적 isLocatedIn)": f"""
        {PREFIX}
        SELECT ?place WHERE {{ :BusanNewPort_B3 :isLocatedIn ?place . }}
    """,
    "CQ5  [추론] 해양수산부가 집행하는 조문 (역 속성 enforces)": f"""
        {PREFIX}
        SELECT ?article WHERE {{ :MOF :enforces ?article . }}
    """,
    "CQ6  [추론] 진해만 해역과 인접한 해역 (대칭 isAdjacentTo)": f"""
        {PREFIX}
        SELECT ?adjacent WHERE {{ :JinhaeBaySeaArea :isAdjacentTo ?adjacent . }}
    """,
    "CQ7  [추론] 제43조가 참조하는 조문 (하위 속성 + 이행성)": f"""
        {PREFIX}
        SELECT ?target WHERE {{ :Art43 :refersTo ?target . }}
    """,
    "CQ8  [운항] 격자 35.0N 129.0E 에서 관측된 선박": f"""
        {PREFIX}
        SELECT ?name WHERE {{
            ?v :reportedPosition ?pos ; :hasName ?name .
            ?pos :inCell :G_35N_129E .
        }} ORDER BY ?name
    """,
    "CQ9  [운항·추론] HL PIONEER 접안 선석이 위치한 모든 지역": f"""
        {PREFIX}
        SELECT ?place WHERE {{
            :HL_PIONEER :hasPortCall ?pc . ?pc :atBerth ?berth .
            ?berth :isLocatedIn ?place .
        }}
    """,
    "CQ10 [추론·핵심] 제43조 위반 시 적용되는 벌칙 조문 (준용 연쇄)": f"""
        {PREFIX}
        SELECT ?no WHERE {{
            :Art43 :junyongOf ?target .
            ?penalty :penalizes ?target ; :hasArticleNo ?no .
        }} ORDER BY ?no
    """,
}


def local(term):
    """URI에서 로컬 이름만 추출해 보기 좋게 출력"""
    s = str(term)
    return s.split("#")[-1] if "#" in s else s


def run_all(graph, phase):
    print(f"\n{'='*66}\n  {phase}  (트리플 {len(graph)}개)\n{'='*66}")
    for title, q in QUERIES.items():
        rows = list(graph.query(q))
        answers = [" · ".join(local(v) for v in row) for row in rows]
        status = "  ".join(answers) if answers else "(응답 없음)"
        print(f"\n▶ {title}\n   → {status}")


def main():
    g = Graph()
    g.parse("maritime_ontology.ttl", format="turtle")

    # ---- 추론 전 ----
    run_all(g, "[1] 추론 전 (Before Reasoning) — 명시된 사실만")

    # ---- OWL RL 추론 적용 (단계 7 핵심) ----
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    # ---- 추론 후 ----
    run_all(g, "[2] 추론 후 (After Reasoning) — 암묵적 지식 자동 도출")

    print(f"\n{'='*66}")
    print("  [검증 결과] CQ3~CQ7 · CQ10 이 추론 후 새로운 답을 반환하면 성공.")
    print("  이행적(isPartOf/isLocatedIn/junyongOf)·역(enforces)·대칭(isAdjacentTo)")
    print("  ·하위(junyongOf⊑refersTo) 속성이 정상 작동함을 의미합니다.")
    print("  특히 CQ10 은 '준용'을 이행적으로 모델링해야 벌칙 경로가")
    print("  끊기지 않는다는 것을 보여줍니다.")
    print(f"{'='*66}")


if __name__ == "__main__":
    main()
