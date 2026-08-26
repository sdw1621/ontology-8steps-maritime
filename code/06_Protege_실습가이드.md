# [단계 6·7] Protégé 실습 가이드 — GUI로 해사 온톨로지 열기·편집·추론

**Protégé**는 스탠포드 대학이 개발한 무료 오픈소스 온톨로지 편집기입니다.
`maritime_ontology.ttl` 을 시각적으로 열어 편집하고, 추론기를 돌려
검증(단계 7)까지 실습합니다.

---

## 1. 설치
1. [protege.stanford.edu](https://protege.stanford.edu/) 에서 데스크톱 버전 다운로드
2. 설치 후 실행 (Java 포함 번들 권장)

---

## 2. 온톨로지 열기
- `File ▸ Open...` → `maritime_ontology.ttl` 선택
- 상단 탭 구성:
  - **Active Ontology**: 네임스페이스·버전 정보
  - **Entities / Classes**: 클래스 계층 (단계 4)
  - **Object/Data Properties**: 속성 (단계 4·5)
  - **Individuals**: 인스턴스 (단계 6)

---

## 3. 클래스 계층 확인 (단계 4)
`Classes` 탭에서 트리 확인:
```
Thing
├─ Regulation
│   ├─ Act          ← 해상교통안전법
│   ├─ Decree
│   └─ Ordinance
├─ LegalUnit
│   ├─ Article      ← 제15조 · 제43조 · 제83조
│   ├─ Paragraph    ← 제15조제1항
│   └─ Item         ← 제15조제1항제3호
├─ Place (Berth / Port / SeaArea / Country)
├─ Vessel
│   ├─ CargoShip      ← HL PIONEER
│   ├─ PassengerShip  ← SEA QUEEN
│   ├─ Tanker         ← BLUE WHALE · OCEAN STAR
│   └─ FishingVessel
├─ Position, PortCall, GridCell   (운항 확장)
└─ Term, Organization, VesselType, Certificate
```

---

## 4. 새 클래스·인스턴스 추가하기 (단계 4·6)
### 클래스 추가
1. `Classes` 탭 → `Vessel` 선택 → **Add subclass** (자식 아이콘)
2. 이름 입력 (예: `TugBoat` 예인선) → 화물선처럼 선박의 하위 클래스가 됨

### 인스턴스 추가
1. `Individuals` 탭 → **Add individual** → 이름 입력 (예: `KOREA_STAR`)
2. `Types` 에 `CargoShip` 지정
3. `Object property assertions` 에서 `hasFlagState → Korea`,
   `hasVesselType → T_Cargo` 추가
4. `Data property assertions` 에서 `hasMmsi "440555000"`,
   `hasGrossTonnage 52000` 추가

---

## 5. 속성 특성 확인 (단계 5)
`Object Properties` 탭에서 각 속성을 선택하면 우측 **Characteristics** 패널에
체크된 특성이 보입니다.

| 속성 | 특성 | 해사 도메인에서의 의미 |
|------|------|------------------------|
| `isLocatedIn` | ☑ Transitive | 선석 → 항만 → 국가 관할 자동 승계 |
| `isPartOf` | ☑ Transitive | 호 → 항 → 조 → 법령 계층 자동 승계 |
| `junyongOf` | ☑ Transitive, ⊑ `refersTo` | 준용의 연쇄 — 벌칙 경로가 끊기지 않음 |
| `isAdjacentTo` | ☑ Symmetric | 인접 해역은 서로 인접 |
| `hasFlagState` | ☑ Functional | 선박의 기국은 하나 |
| `enforcedBy` | Inverse Of = `enforces` | 조문↔집행기관 양방향 조회 |

---

## 6. 추론기 실행 — 검증의 핵심 (단계 7)
1. 상단 메뉴 `Reasoner ▸ HermiT` (또는 Pellet) 선택
2. `Reasoner ▸ Start reasoner` 클릭
3. 추론 후 확인할 것:
   - **일관성 검사**: 모순이 있으면 빨간 경고 표시
   - **추론된 관계**(노란 배경): `Art15_P1_I3` 개체를 열면
     `isPartOf MaritimeSafetyAct` 가 **자동 추론**되어 나타남 (이행성)
   - `MOF` 개체에 `enforces Art15` 가 추론됨 (역 속성)
   - `Art43` 개체에 `refersTo Art10` 이 추론됨 (하위 속성 + 이행성)

> 노란색으로 표시되는 항목이 "명시하지 않았지만 추론된 지식"입니다.
> 이것이 단계 7 검증에서 확인하는 추론기의 역할입니다.

### 일관성 위반 실습
`OCEAN_STAR` 에 `hasFlagState → Korea` 와 `hasFlagState → Panama` 를 함께 넣고
추론기를 돌려보세요. `hasFlagState` 가 **Functional** 이므로 추론기는 두 국가를
동일한 개체(`owl:sameAs`)로 간주합니다. `Korea` 와 `Panama` 를
`Different Individuals` 로 선언해두면 **비일관(inconsistent)** 으로 잡힙니다.
→ "한 선박은 기국이 하나"라는 업무 규칙을 온톨로지가 강제하는 순간입니다.

---

## 7. SPARQL 질의 실습 (단계 7)
1. `Window ▸ Tabs ▸ SPARQL Query` 로 탭 활성화
2. 아래 붙여넣고 실행:
   ```sparql
   PREFIX : <http://maritime-kg.example.org/ontology/maritime#>
   SELECT ?name ?gt WHERE {
       ?v :hasVesselType :T_Tanker ; :hasGrossTonnage ?gt ; :hasName ?name .
       FILTER (?gt >= 5000)
   }
   ```

---

## 8. 품질 기준 자가 점검 (단계 7 — Gruber 원칙)
| 기준 | 점검 질문 | Protégé 확인 방법 |
|------|-----------|-------------------|
| **일관성** | 논리적 모순은 없는가? | Reasoner 실행 → 경고 없음 |
| **명확성** | '준용'과 일반 '참조'가 구분되는가? | `junyongOf` / `refersTo` 계층 확인 |
| **완전성** | 역량질문에 모두 답하는가? | SPARQL 탭에서 CQ1~CQ10 실행 |
| **확장성** | 새 선종·새 법령 추가가 쉬운가? | subclass 추가 테스트 |
| **최소 약속** | 불필요한 제약은 없는가? | 과도한 카디널리티 점검 |

---

## 9. 저장·내보내기 (단계 6·8)
- `File ▸ Save as...` → **Turtle / RDF-XML / Manchester Syntax / JSON-LD** 선택 가능
- 저장한 `.ttl` 을 그대로 Fuseki에 배포 (→ `05_Fuseki_배포가이드.md`)
