"""
=============================================================
 [단계 8] 배포된 SPARQL 엔드포인트에 HTTP로 질의하기
 Apache Jena Fuseki 서버(http://localhost:3030)가 실행 중이어야 한다.

 표준 라이브러리(urllib)만 사용 — 추가 설치 불필요.
 실행:  python 04_sparql_client.py
=============================================================
"""
import json
import urllib.parse
import urllib.request

ENDPOINT = "http://localhost:3030/maritime/sparql"
PREFIX = "PREFIX : <http://maritime-kg.example.org/ontology/maritime#>"

QUERIES = {
    "CQ1  부산항에 입항한 선박": f"""
        {PREFIX}
        SELECT ?name WHERE {{
            ?v :hasPortCall ?pc ; :hasName ?name .
            ?pc :atPort :BusanPort .
        }} ORDER BY ?name
    """,
    "CQ3  [서버 추론] 제15조제1항제3호의 상위 단위 (이행적)": f"""
        {PREFIX}
        SELECT ?unit WHERE {{ :Art15_P1_I3 :isPartOf ?unit . }}
    """,
    "CQ4  [서버 추론] 부산신항 제3선석의 상위 지역 (이행적)": f"""
        {PREFIX}
        SELECT ?place WHERE {{ :BusanNewPort_B3 :isLocatedIn ?place . }}
    """,
    "CQ7  [서버 추론] 제43조가 참조하는 조문 (하위 속성 + 이행성)": f"""
        {PREFIX}
        SELECT ?target WHERE {{ :Art43 :refersTo ?target . }}
    """,
    "CQ10 [서버 추론] 제43조 위반 시 적용되는 벌칙 조문": f"""
        {PREFIX}
        SELECT ?no WHERE {{
            :Art43 :junyongOf ?target .
            ?penalty :penalizes ?target ; :hasArticleNo ?no .
        }} ORDER BY ?no
    """,
}


def sparql(query):
    """SPARQL SELECT 질의를 HTTP GET으로 전송하고 JSON 결과를 반환"""
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def rows(result):
    out = []
    vs = result["head"]["vars"]
    for b in result["results"]["bindings"]:
        out.append(" · ".join(b[v]["value"].split("#")[-1] for v in vs if v in b))
    return out


def main():
    print(f"엔드포인트: {ENDPOINT}\n")
    for title, q in QUERIES.items():
        try:
            answers = rows(sparql(q))
            print(f"▶ {title}\n   → {'  '.join(answers) if answers else '(응답 없음)'}\n")
        except Exception as e:
            print(f"▶ {title}\n   ! 오류: {e}")
            print("   (Fuseki 서버가 실행 중인지 확인하세요: fuseki-server --config=fuseki_config.ttl)\n")


if __name__ == "__main__":
    main()
