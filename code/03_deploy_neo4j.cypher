// =============================================================
//  [단계 8] 배포 — 해사 온톨로지를 Neo4j 그래프 DB로 이관
//  『지식그래프: AI와 온톨로지로 여는 지식혁명』 3장 8단계 방법론
//
//  두 가지 방법을 제공한다.
//   (A) neosemantics(n10s) 플러그인으로 Turtle 파일을 그대로 임포트
//   (B) 순수 Cypher 로 스키마·데이터를 직접 구성 (플러그인 불필요)
// =============================================================


// -------------------------------------------------------------
// (A) neosemantics(n10s) 로 RDF 온톨로지 직접 임포트
//     사전: Neo4j에 n10s 플러그인 설치 후 아래 실행
// -------------------------------------------------------------

// 1) 고유 제약(URI 유일성) 생성 — n10s 필수
CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS
FOR (r:Resource) REQUIRE r.uri IS UNIQUE;

// 2) 그래프 설정 초기화
CALL n10s.graphconfig.init({ handleVocabUris: "IGNORE" });

// 3) Turtle 파일 임포트 (경로는 환경에 맞게 수정)
CALL n10s.rdf.import.fetch(
  "file:///maritime_ontology.ttl", "Turtle"
);
// → 임포트 후 클래스/인스턴스/관계가 노드·관계로 적재된다.


// -------------------------------------------------------------
// (B) 순수 Cypher 로 스키마·데이터 구성 (n10s 없이)
//     운영 조회 성능을 위한 인덱스 포함
// -------------------------------------------------------------

// 조회 축이 되는 식별자에 인덱스 (MMSI · 조문번호)
CREATE INDEX vessel_mmsi   IF NOT EXISTS FOR (v:Vessel)    ON (v.mmsi);
CREATE INDEX article_no    IF NOT EXISTS FOR (a:Article)   ON (a.articleNo);
CREATE INDEX portcall_time IF NOT EXISTS FOR (p:PortCall)  ON (p.observedAt);

// --- 법령 계층 · 기관 ---
MERGE (act:Regulation:Act {name:"MaritimeSafetyAct", label:"해상교통안전법(예시)"})
MERGE (a10:LegalUnit:Article {name:"Art10", articleNo:"제10조", label:"통항의 원칙"})
MERGE (a15:LegalUnit:Article {name:"Art15", articleNo:"제15조", label:"항로에서의 항법"})
MERGE (a43:LegalUnit:Article {name:"Art43", articleNo:"제43조", label:"예인선의 항법 준용"})
MERGE (a83:LegalUnit:Article {name:"Art83", articleNo:"제83조", label:"벌칙"})
MERGE (a90:LegalUnit:Article {name:"Art90", articleNo:"제90조", label:"과태료"})
MERGE (p1:LegalUnit:Paragraph {name:"Art15_P1", articleNo:"제15조제1항"})
MERGE (i3:LegalUnit:Item {name:"Art15_P1_I3", articleNo:"제15조제1항제3호",
                          label:"항로 안에서의 추월 금지",
                          proviso:"다만, 부득이한 사유로 허가를 받은 경우에는 그러하지 아니하다."})
MERGE (mof:Organization {name:"MOF", label:"해양수산부"})
MERGE (kcg:Organization {name:"KCG", label:"해양경찰청"})

// --- 장소 계층 · 해역 ---
MERGE (b3:Place:Berth {name:"BusanNewPort_B3", label:"부산신항 제3선석"})
MERGE (bp:Place:Port  {name:"BusanPort", label:"부산항"})
MERGE (kr:Place:Country {name:"Korea", label:"대한민국"})
MERGE (bsa:Place:SeaArea {name:"BusanSeaArea", label:"부산항 해역"})
MERGE (jsa:Place:SeaArea {name:"JinhaeBaySeaArea", label:"진해만 해역"})

// --- 선박 · 입출항 ---
MERGE (hl:Vessel:CargoShip {name:"HL_PIONEER", label:"HL PIONEER",
                            mmsi:"440123000", imo:"9876543", grossTonnage:74000})
MERGE (pc:PortCall {name:"PC_HL_001", callType:"입항",
                    observedAt:"2026-03-11T08:20:00Z"})

// --- 관계: 객체 속성을 그래프 관계로 표현 ---
MERGE (i3)-[:IS_PART_OF]->(p1)
MERGE (p1)-[:IS_PART_OF]->(a15)
MERGE (a15)-[:IS_PART_OF]->(act)
MERGE (a43)-[:IS_PART_OF]->(act)
MERGE (a83)-[:IS_PART_OF]->(act)
MERGE (a90)-[:IS_PART_OF]->(act)
MERGE (a15)-[:ENFORCED_BY]->(mof)
MERGE (a83)-[:ENFORCED_BY]->(kcg)

// 준용(準用)은 일반 참조와 구분해야 한다.
// RDF에서는 하위 속성(junyongOf ⊑ refersTo)으로, 속성그래프에서는
// REFERS_TO 관계의 refType 속성으로 표현한다.
MERGE (a43)-[:REFERS_TO {refType:"준용"}]->(a15)
MERGE (a15)-[:REFERS_TO {refType:"준용"}]->(a10)
MERGE (a83)-[:PENALIZES]->(a15)
MERGE (a90)-[:PENALIZES]->(a10)

MERGE (b3)-[:IS_LOCATED_IN]->(bp)
MERGE (bp)-[:IS_LOCATED_IN]->(kr)
MERGE (bsa)-[:IS_ADJACENT_TO]->(jsa)
MERGE (jsa)-[:IS_ADJACENT_TO]->(bsa)   // 대칭 속성은 양방향 간선으로 구현

MERGE (hl)-[:HAS_FLAG_STATE]->(kr)
MERGE (hl)-[:HAS_PORT_CALL]->(pc)
MERGE (pc)-[:AT_PORT]->(bp)
MERGE (pc)-[:AT_BERTH]->(b3);


// -------------------------------------------------------------
// (C) 배포 후 역량질문 — Cypher 로 재현
//     Neo4j 는 가변 길이 경로(*)로 이행적 관계를 질의한다.
// -------------------------------------------------------------

// CQ1) 부산항에 입항한 선박
MATCH (v:Vessel)-[:HAS_PORT_CALL]->(:PortCall)-[:AT_PORT]->(:Port {name:"BusanPort"})
RETURN v.label AS 선박, v.mmsi AS MMSI;

// CQ3) [이행적] 제15조제1항제3호가 속한 모든 상위 단위 (항·조·법령)
//      SPARQL 의 TransitiveProperty ↔ Cypher 의 가변 길이 경로 *1..
MATCH (:Item {name:"Art15_P1_I3"})-[:IS_PART_OF*1..]->(u)
RETURN labels(u) AS 유형, coalesce(u.articleNo, u.label) AS 소속;

// CQ4) [이행적] 부산신항 제3선석이 위치한 모든 상위 지역 (항만·국가)
MATCH (:Berth {name:"BusanNewPort_B3"})-[:IS_LOCATED_IN*1..]->(place)
RETURN labels(place) AS 유형, place.label AS 지역;

// CQ5) [역방향] 해양수산부가 집행하는 조문
//      RDF의 inverseOf 는 Cypher 에서 관계를 반대로 매칭하면 된다.
MATCH (:Organization {name:"MOF"})<-[:ENFORCED_BY]-(a:LegalUnit)
RETURN a.articleNo AS 조문, a.label AS 제목;

// CQ7) [이행적] 제43조가 준용으로 도달하는 모든 조문
//      refType="준용" 인 간선만 따라간다 — 일반 참조까지 따라가면 과잉 확장된다.
MATCH p = (:Article {name:"Art43"})-[r:REFERS_TO*1..]->(t:Article)
WHERE all(x IN relationships(p) WHERE x.refType = "준용")
RETURN t.articleNo AS 준용대상, t.label AS 제목;

// CQ10) [핵심] 제43조 위반 시 적용되는 벌칙 조문
//       준용 경로를 따라가지 않으면 제90조(과태료)가 누락된다.
MATCH p = (:Article {name:"Art43"})-[:REFERS_TO*1..]->(t:Article)
WHERE all(x IN relationships(p) WHERE x.refType = "준용")
MATCH (pen:Article)-[:PENALIZES]->(t)
RETURN DISTINCT pen.articleNo AS 벌칙조문, pen.label AS 제목, t.articleNo AS 위반조문;
