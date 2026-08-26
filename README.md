# 온톨로지 구축 8단계 — 해사 도메인

**해사법령 + 운항데이터**를 예시로 배우는 지식그래프 온톨로지 구축 8단계 방법론 구현.
『지식그래프: AI와 온톨로지로 여는 지식혁명』 3장 · Ontology Development 101 (Noy, 2001) 기반.

원본 [ontology-8steps](https://github.com/sdw1621/ontology-8steps)(공연·전시 도메인)의
`code/` 를 해사 도메인으로 옮긴 것입니다. 8단계 구조와 파일 구성은 그대로 유지하고,
클래스·속성·역량질문만 해사 도메인으로 치환했습니다.

> 대화형 해사서비스 플랫폼 지식그래프 모델 설계의 **TBox 설계 연습용 레퍼런스**입니다.
> ABox의 조문 번호·내용·선박 제원은 **방법론 시연용 예시값**이며 실제 법령·선박
> 데이터와 일치하지 않습니다.

## 📁 코드 (`code/`)

| 파일 | 단계 | 설명 |
|------|:---:|------|
| `maritime_ontology.ttl` | 4·5·6 | 해사 온톨로지 (OWL2/Turtle) |
| `01_build_ontology.py` | 4·5·6 | rdflib로 온톨로지 프로그래밍 구축 |
| `competency_questions.sparql` | 2·7 | 역량질문 SPARQL (CQ1~CQ10) |
| `02_validate_and_query.py` | 7 | owlrl 추론 + 역량질문 검증 (추론 전/후 비교) |
| `03_deploy_neo4j.cypher` | 6·8 | Neo4j/neosemantics 이관 |
| `04_sparql_client.py` · `fuseki_config.ttl` · `05_Fuseki_배포가이드.md` | 8 | Fuseki SPARQL 엔드포인트 배포 |
| `06_Protege_실습가이드.md` | 6·7 | Protégé GUI 실습 |

### 실행

```bash
pip install -r code/requirements.txt
```

```bash
python code/02_validate_and_query.py
```

## 🔑 이 온톨로지의 핵심 — 준용(準用)의 이행성

```
제43조 --준용--> 제15조 --준용--> 제10조
제83조가 제15조를, 제90조가 제10조를 처벌한다.
```

`junyongOf` 를 `refersTo` 의 **하위 속성 + 이행적 속성**으로 선언해야
"제43조 위반 시 적용되는 벌칙"에서 **제90조가 누락되지 않습니다.**
속성그래프(Neo4j)의 `REFERS_TO {refType:"준용"}` 간선 속성과 같은 구분을
RDF에서 재현한 것으로, 규제 판정의 정확도를 좌우하는 설계 지점입니다.

## ✅ 검증 결과 (실측)

추론 전 **353 트리플** → 추론 후 **1,040 트리플**.
CQ3·CQ4·CQ5·CQ6·CQ7·CQ9·CQ10 이 추론 후 새로운 답을 반환합니다.

자세한 대응표·검증 결과는 **[code/README.md](code/README.md)** 참고.
