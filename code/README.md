# 온톨로지 구축 8단계 — 해사 도메인 구현

『지식그래프: AI와 온톨로지로 여는 지식혁명』 3장의 **온톨로지 8단계 방법론**을
**해사 도메인**(해사법령 + 운항데이터)으로 옮겨 실행 가능한 코드로 구현한 예제입니다.
(Ontology Development 101 기반 / 원본: 공연·전시 온톨로지)

> 대화형 해사서비스 플랫폼 지식그래프 모델 설계의 **TBox 설계 연습용 레퍼런스**입니다.
> ABox의 조문 번호·내용·선박 제원은 **방법론 시연용 예시값**이며 실제 법령·선박
> 데이터와 일치하지 않습니다. 실데이터 적재는 별도 ETL 파이프라인이 담당합니다.

---

## 📁 파일 구성

| 파일 | 대응 단계 | 설명 |
|------|-----------|------|
| `maritime_ontology.ttl` | **4·5·6** | 손으로 작성한 OWL2 온톨로지 (클래스·속성·관계·인스턴스) |
| `01_build_ontology.py` | **4·5·6** | 같은 온톨로지를 rdflib로 프로그래밍 구축 → TTL 생성 |
| `competency_questions.sparql` | **2·7** | 역량 질문(Competency Questions)을 SPARQL로 정의 |
| `02_validate_and_query.py` | **7** | owlrl 추론 적용 + 역량질문 실행 (추론 전/후 비교) |
| `03_deploy_neo4j.cypher` | **6·8** | Neo4j/neosemantics 이관 + Cypher 역량질문 |
| `04_sparql_client.py` | **8** | 배포된 Fuseki 엔드포인트에 HTTP 질의 (urllib) |
| `fuseki_config.ttl` | **8** | Fuseki 서비스 설정 (OWL 추론기 ON) |
| `05_Fuseki_배포가이드.md` | **8** | Apache Jena Fuseki 실전 배포 가이드 |
| `06_Protege_실습가이드.md` | **6·7** | Protégé GUI로 열기·편집·추론 실습 |
| `온톨로지_8단계_파일별_설명.pptx` | **전체** | 파일별 단계 설명 발표자료 (14장) |
| `requirements.txt` | — | 의존성 (rdflib, owlrl) |

> 온톨로지는 **법령 도메인**(조-항-호·준용·위임·집행)을 기본으로,
> **운항 도메인**(AIS 항적·입출항·격자)까지 확장되어 있습니다. (CQ8~CQ10)

---

## 🚀 실행 방법

```bash
pip install -r requirements.txt
```

```bash
python 01_build_ontology.py
```

```bash
python 02_validate_and_query.py
```

> Windows 터미널에서 한글이 깨지면 `set PYTHONIOENCODING=utf-8` 후 실행하세요.

---

## 🧩 8단계 ↔ 코드 매핑

| 단계 | 방법론 | 해사 도메인에서의 구현 |
|:---:|--------|------------------------|
| **1** 도메인 이해 | 개념·용어 파악 | 법령(조-항-호·준용·위임)과 운항(MMSI·항적·입출항) 용어 정리 |
| **2** 범위 결정 | 역량 질문 정의 | `competency_questions.sparql` 의 CQ1~CQ10 |
| **3** 개체 탐색 | 핵심 용어 목록화 | `01_build_ontology.py` 의 클래스/개체 목록 |
| **4** 클래스·속성 | `owl:Class`, 데이터/객체 속성, domain/range | `.ttl` [단계 4] 블록 · `add_class/add_*_prop()` |
| **5** 관계 정의 | 이행·역·대칭·함수·하위 속성, 카디널리티 | `.ttl` [단계 5] 블록 · `characteristics=[...]` |
| **6** 표현·구현 | OWL2/Turtle 직렬화, 인스턴스 생성 | `g.serialize()` · ABox 블록 |
| **7** 검증·평가 | 추론기(OWL RL) · 역량질문 응답 | `02_validate_and_query.py` |
| **8** 배포·유지보수 | 트리플스토어/그래프DB·버전 | `03_deploy_neo4j.cypher` · `owl:versionInfo` |

---

## 🔑 단계 5 — 해사 도메인의 논리적 특성 설계

| 속성 | OWL 특성 | 해사 도메인에서 그렇게 선언한 이유 |
|------|----------|-----------------------------------|
| `isPartOf` | Transitive | 제3호가 제1항에 속하면, 제15조·법률에도 속한다 |
| `isLocatedIn` | Transitive | 선석의 관할·관제구역은 항만·국가로 승계된다 |
| `junyongOf` | Transitive + ⊑`refersTo` | **준용은 연쇄된다.** 일반 참조와 구분하지 않으면 벌칙 경로가 끊긴다 |
| `isAdjacentTo` | Symmetric | 인접 해역 관계는 방향이 없다 |
| `hasFlagState` | Functional | 한 선박의 기국은 하나뿐이다 |
| `enforcedBy` | inverseOf `enforces` | 조문→기관, 기관→조문 양방향 조회가 모두 필요하다 |
| `hasCertificate` | minCardinality 1 (여객선) | 여객선은 검사증서 없이 존재할 수 없다 |

### 준용(準用)을 왜 하위 속성으로 모델링했는가

속성그래프(Neo4j)에서는 `REFERS_TO` 관계에 `refType:"준용"` 속성을 붙여 구분합니다.
RDF에는 간선 속성이 없으므로 **하위 속성**으로 같은 구분을 만듭니다.

```
junyongOf  rdfs:subPropertyOf  refersTo ,  a owl:TransitiveProperty
```

이렇게 하면 ① 준용만 따로 추적할 수 있고(`junyongOf`), ② 참조 일반을 물을 때는
준용도 함께 잡히며(`refersTo`), ③ 준용의 연쇄가 자동으로 이어집니다.
`03_deploy_neo4j.cypher` 의 CQ7·CQ10 은 같은 논리를 Cypher의
`WHERE all(x IN relationships(p) WHERE x.refType = "준용")` 로 재현합니다.

---

## ✅ 검증 결과 (실측)

`python 02_validate_and_query.py` 실행 결과. 추론 전 **353 트리플** →
추론 후 **1,040 트리플**로 확장되며, 명시하지 않은 지식이 자동 도출됩니다.

| 역량질문 | 추론 전 | 추론 후 | 검증 속성 |
|----------|---------|---------|-----------|
| CQ3 제15조제1항제3호의 상위 단위 | Art15_P1 | Art15_P1, **Art15**, **MaritimeSafetyAct** | 이행적 `isPartOf` |
| CQ4 부산신항 제3선석의 상위 지역 | BusanPort | BusanPort, **Korea** | 이행적 `isLocatedIn` |
| CQ5 해양수산부가 집행하는 조문 | (없음) | **Art15** | 역 속성 `enforces` |
| CQ6 진해만 해역과 인접한 해역 | (없음) | **BusanSeaArea** | 대칭 `isAdjacentTo` |
| CQ7 제43조가 참조하는 조문 | (없음) | **Art15, Art10** | 하위 속성 + 이행성 |
| CQ9 HL PIONEER 접안 선석의 소재 지역 | BusanPort | BusanPort, **Korea** | 이행적 `isLocatedIn` |
| CQ10 제43조 위반 시 벌칙 조문 | 제83조 | 제83조, **제90조** | 이행적 `junyongOf` |

> **CQ10이 이 온톨로지의 핵심 검증입니다.**
> 제43조 --준용--> 제15조 --준용--> 제10조 이고, 제83조가 제15조를,
> 제90조가 제10조를 처벌합니다. `junyongOf` 를 이행적으로 선언하지 않으면
> **제90조(과태료)가 조회에서 통째로 누락**됩니다. 규제 판정에서 이런 누락은
> "위반이 아니다"라는 잘못된 결론으로 이어집니다.
>
> CQ1·CQ2·CQ8 은 추론 없이도 답이 나옵니다 — 모든 질의가 추론을
> 필요로 하는 것은 아니며, 그 구분 자체가 단계 7 평가의 일부입니다.

`01_build_ontology.py` 가 생성한 `maritime_ontology_generated.ttl` 은
손으로 작성한 `maritime_ontology.ttl` 과 **동일하게 353 트리플**이며
역량질문 응답도 일치합니다.

---

## 🔧 실무 확장 아이디어
- **Protégé** 로 `maritime_ontology.ttl` 을 열어 시각적으로 편집 (단계 6)
- **HermiT/Pellet** 추론기로 일관성 위반 자동 탐지 — 예: 한 선박에 기국 2개
  (`hasFlagState` Functional 위반) → `06_Protege_실습가이드.md` 6절 실습
- **SPARQL 엔드포인트**(Fuseki 등)에 배포해 대화형 질의 연동 (단계 8)
- **실데이터 연결**: `hasMmsi`·`hasImoNumber`·UN/LOCODE 를 조인키로 삼아
  AIS·PORT-MIS 등 외부 소스를 `Vessel`·`Port` 노드에 연결
- **대용량 항적 분리**: `Position` 전량을 트리플스토어에 넣지 말고
  격자 집계(`GridCell`)·입출항(`PortCall`)만 KG에 두고 MMSI로 시계열 DB와 연결
- **Git** 으로 온톨로지 버전 관리, 법령 개정 시 `owl:versionInfo`·`effectiveDate` 갱신

---

## 🔁 원본(공연·전시) 대비 변환 대응표

| 원본 개념 | 해사 개념 | 비고 |
|-----------|-----------|------|
| Performance / Musical·Concert | Vessel / CargoShip·PassengerShip·Tanker | 상위-하위 클래스 |
| Genre (장르 개체) | VesselType (AIS 선종 코드) | 코드 목록형 개체 |
| Venue → City → Country | Berth → Port → Country | 이행적 `isLocatedIn` |
| Section → Festival | Item → Paragraph → Article → Regulation | 이행적 `isPartOf` |
| hasPerformer ↔ performsIn | enforcedBy ↔ enforces | 역 속성 |
| isSimilarTo (유사 공연) | isAdjacentTo (인접 해역) | 대칭 속성 |
| hasDirector (감독 1명) | hasFlagState (기국 1개) | 함수적 속성 |
| Musical minCard 1 hasPerformer | PassengerShip minCard 1 hasCertificate | 카디널리티 |
| hasRating ≥ 4.0 필터 | hasGrossTonnage ≥ 5000 필터 | CQ2 수치 필터 |
| (없음) | **junyongOf ⊑ refersTo, Transitive** | 해사 도메인 고유 — 준용 연쇄 |
| 전시(Exhibition) 도메인 확장 | 운항(AIS·입출항) 도메인 확장 | Position·PortCall·GridCell |
