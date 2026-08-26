# [단계 8] Apache Jena Fuseki 배포 — 실전 가이드 (해사 도메인)

해사 온톨로지를 **SPARQL 엔드포인트**(웹 API)로 배포해, 대화형 해사서비스
플랫폼이 HTTP로 지식을 질의하고 **서버 측 추론**까지 활용하도록 만든다.

---

## 1. Fuseki 설치

1. Java 11+ 설치 확인
   ```bash
   java -version
   ```
2. [Apache Jena Fuseki 다운로드](https://jena.apache.org/download/) → `apache-jena-fuseki-x.x.x.zip` 압축 해제
3. 압축 푼 폴더로 이동

> `fuseki_config.ttl` 의 `file:///maritime_ontology.ttl` 경로를
> 실제 `.ttl` 절대경로로 수정하세요. (Windows 예: `file:///C:/.../maritime_ontology.ttl`)

---

## 2. 추론 켜고 서버 실행

```bash
fuseki-server --config=fuseki_config.ttl
```

- 관리 콘솔: **http://localhost:3030**
- SPARQL 엔드포인트: **http://localhost:3030/maritime/sparql**

`fuseki_config.ttl` 이 `OWLFBRuleReasoner` 를 켜므로, 이행·역·대칭·하위 속성이
**서버에서 자동 추론**됩니다. (rdflib+owlrl 로컬 추론과 동일한 효과)

---

## 3. 질의 방법 3가지

### (A) 웹 UI
브라우저에서 `http://localhost:3030` → dataset `maritime` → **Query** 탭에
SPARQL 붙여넣고 실행.

### (B) Python 클라이언트 (추가 설치 불필요)
```bash
python 04_sparql_client.py
```

### (C) curl
```bash
curl -G http://localhost:3030/maritime/sparql --data-urlencode 'query=PREFIX : <http://maritime-kg.example.org/ontology/maritime#> SELECT ?unit WHERE { :Art15_P1_I3 :isPartOf ?unit . }' -H 'Accept: application/sparql-results+json'
```

> 추론이 켜져 있으므로 `:Art15_P1_I3 :isPartOf ?unit` 은 **제15조제1항 + 제15조 +
> 해상교통안전법** 을 모두 반환합니다 (이행적 추론).

---

## 4. 데이터 업로드 (config 없이 빈 서버에 적재할 때)

```bash
fuseki-server --update --mem /maritime
```

```bash
curl -X POST -H "Content-Type: text/turtle" --data-binary @maritime_ontology.ttl http://localhost:3030/maritime/data
```

---

## 5. 해사 도메인 운영 시 추가 고려사항 (단계 8)

| 항목 | 이 도메인에서의 쟁점 |
|------|----------------------|
| **법령 개정 주기** | 조문 개정 시 `owl:versionInfo` + `effectiveDate` 로 시점 관리. 폐지 조문은 삭제가 아니라 `deprecated` 표시(과거 항해 이력 판정에 필요) |
| **대용량 시계열** | AIS 항적(`Position`)은 트리플스토어에 전량 적재하지 말 것. 격자 집계(`GridCell`)·입출항 이벤트(`PortCall`)만 KG에 두고, 원 항적은 시계열 DB에 두고 조인키(MMSI)로 연결 |
| **비식별 관측** | 레이다·CCTV 트랙을 선박에 확정 연결할 수 없을 때는 억지 매칭 대신 미식별 상태로 남긴다(오매칭이 규제 판정 오류로 번짐) |
| **접근 제어** | 조문·항만 통계는 공개, 개별 선박 항적은 제한 등급. update 엔드포인트는 반드시 인증 |
| **백업·버전** | `.ttl` 을 Git 으로, 트리플스토어는 정기 스냅샷 |

---

## 6. 운영 체크리스트
- [ ] **버전 관리**: `.ttl` 을 Git으로 관리, `owl:versionInfo` 갱신
- [ ] **백업**: 트리플스토어 데이터 정기 백업
- [ ] **접근 제어**: 운영 시 update 엔드포인트 인증 설정
- [ ] **모니터링**: 질의 성능·응답시간 측정 (단계 7 애플리케이션 평가와 연계)
- [ ] **거버넌스**: 온톨로지 변경 승인 절차·책임자 지정 (법령 개정 반영 담당 포함)
