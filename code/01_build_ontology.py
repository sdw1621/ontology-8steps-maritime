"""
=============================================================
 [단계 4·5·6] 온톨로지를 코드로 구축하기 — rdflib 프로그래밍 버전
 『지식그래프: AI와 온톨로지로 여는 지식혁명』 3장 8단계 방법론 (해사 도메인)

 maritime_ontology.ttl 과 동일한 온톨로지를 파이썬으로 단계별로
 생성하고 Turtle 파일(maritime_ontology_generated.ttl)로 저장한다.

 실행:  python 01_build_ontology.py
 필요:  pip install rdflib
=============================================================
"""
from rdflib import Graph, Namespace, Literal, BNode, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD

# 네임스페이스 정의 (단계 6: URI 명명 규칙)
BASE = "http://maritime-kg.example.org/ontology/maritime"
MAR = Namespace(BASE + "#")

g = Graph()
g.bind("", MAR)       # 기본 네임스페이스
g.bind("owl", OWL)
g.bind("rdfs", RDFS)
g.bind("xsd", XSD)

# 온톨로지 헤더
onto = URIRef(BASE)
g.add((onto, RDF.type, OWL.Ontology))
g.add((onto, RDFS.label, Literal("해사 서비스 온톨로지", lang="ko")))
g.add((onto, OWL.versionInfo, Literal("1.0.0")))


# ---------------------------------------------------------
# [단계 4] 클래스 정의 + 계층 구조
# ---------------------------------------------------------
def add_class(name, label, parent=None):
    g.add((MAR[name], RDF.type, OWL.Class))
    g.add((MAR[name], RDFS.label, Literal(label, lang="ko")))
    if parent:
        g.add((MAR[name], RDFS.subClassOf, MAR[parent]))

# 법령 도메인
add_class("Regulation", "법령")
add_class("Act",       "법률",   "Regulation")
add_class("Decree",    "시행령", "Regulation")
add_class("Ordinance", "시행규칙", "Regulation")
add_class("LegalUnit", "법령 단위")
add_class("Article",   "조", "LegalUnit")
add_class("Paragraph", "항", "LegalUnit")
add_class("Item",      "호", "LegalUnit")
add_class("Term",         "정의어")
add_class("Organization", "기관")

# 장소 도메인
add_class("Place", "장소")
add_class("Berth",   "선석", "Place")
add_class("Port",    "항만", "Place")
add_class("SeaArea", "해역", "Place")
add_class("Country", "국가", "Place")

# 선박 도메인
add_class("Vessel", "선박")
add_class("CargoShip",     "화물선", "Vessel")
add_class("PassengerShip", "여객선", "Vessel")
add_class("Tanker",        "유조선", "Vessel")
add_class("FishingVessel", "어선",   "Vessel")
for n, l in [("VesselType", "선종 코드"), ("Certificate", "검사증서")]:
    add_class(n, l)


# ---------------------------------------------------------
# [단계 4] 데이터 속성 (DatatypeProperty)
# ---------------------------------------------------------
def add_data_prop(name, label, rng, domain=None):
    g.add((MAR[name], RDF.type, OWL.DatatypeProperty))
    g.add((MAR[name], RDFS.label, Literal(label, lang="ko")))
    g.add((MAR[name], RDFS.range, rng))
    if domain:
        g.add((MAR[name], RDFS.domain, MAR[domain]))

add_data_prop("hasName", "명칭", XSD.string)
add_data_prop("effectiveDate", "시행일", XSD.date, "Regulation")
add_data_prop("hasArticleNo", "조문 번호", XSD.string, "LegalUnit")
add_data_prop("hasProviso", "단서", XSD.string, "LegalUnit")
add_data_prop("hasMmsi", "MMSI", XSD.string, "Vessel")
add_data_prop("hasImoNumber", "IMO 번호", XSD.string, "Vessel")
add_data_prop("hasGrossTonnage", "총톤수(GT)", XSD.decimal, "Vessel")
add_data_prop("issuedDate", "증서 발급일", XSD.date, "Certificate")


# ---------------------------------------------------------
# [단계 4·5] 객체 속성 (ObjectProperty) + 논리적 특성
# ---------------------------------------------------------
def add_obj_prop(name, label, domain=None, rng=None,
                 characteristics=None, super_prop=None):
    g.add((MAR[name], RDF.type, OWL.ObjectProperty))
    g.add((MAR[name], RDFS.label, Literal(label, lang="ko")))
    if domain:
        g.add((MAR[name], RDFS.domain, MAR[domain]))
    if rng:
        g.add((MAR[name], RDFS.range, MAR[rng]))
    for c in (characteristics or []):
        g.add((MAR[name], RDF.type, c))   # 예: OWL.TransitiveProperty
    if super_prop:
        g.add((MAR[name], RDFS.subPropertyOf, MAR[super_prop]))

add_obj_prop("hasVesselType", "선종", "Vessel", "VesselType")
add_obj_prop("hasCertificate", "보유 증서", "Vessel", "Certificate")
add_obj_prop("definesTerm", "정의 조문", "LegalUnit", "Term")
add_obj_prop("delegatesTo", "위임", "LegalUnit", "Regulation")
add_obj_prop("appliesTo", "적용 대상 선종", "LegalUnit", "VesselType")
add_obj_prop("penalizes", "벌칙 대상 조문", "Article", "Article")

# 함수적 속성 — 선박의 기국은 하나
add_obj_prop("hasFlagState", "기국", "Vessel", "Country",
             characteristics=[OWL.FunctionalProperty])

# 역 속성 — enforcedBy ↔ enforces
add_obj_prop("enforcedBy", "집행 기관", "LegalUnit", "Organization")
add_obj_prop("enforces", "집행 조문", "Organization", "LegalUnit")
g.add((MAR["enforcedBy"], OWL.inverseOf, MAR["enforces"]))

# 이행적 속성 — 장소 포함(선석→항만→국가), 법령 계층(호→항→조→법령)
add_obj_prop("isLocatedIn", "위치", "Place", "Place",
             characteristics=[OWL.TransitiveProperty])
add_obj_prop("isPartOf", "소속", characteristics=[OWL.TransitiveProperty])

# 대칭적 속성 — 해역 인접
add_obj_prop("isAdjacentTo", "인접 해역", "SeaArea", "SeaArea",
             characteristics=[OWL.SymmetricProperty])

# 조문 참조 + 하위 속성 '준용'(이행적)
#   속성그래프의 refType="준용" 간선 속성을 RDF에서는 하위 속성으로 모델링한다.
add_obj_prop("refersTo", "조문 참조", "LegalUnit", "LegalUnit")
add_obj_prop("junyongOf", "준용", "LegalUnit", "LegalUnit",
             characteristics=[OWL.TransitiveProperty], super_prop="refersTo")

# 카디널리티 제약 — 모든 여객선은 최소 1건의 검사증서 (blank node Restriction)
r = BNode()
g.add((r, RDF.type, OWL.Restriction))
g.add((r, OWL.onProperty, MAR["hasCertificate"]))
g.add((r, OWL.minCardinality, Literal(1, datatype=XSD.nonNegativeInteger)))
g.add((MAR["PassengerShip"], RDFS.subClassOf, r))


# ---------------------------------------------------------
# [단계 6] 인스턴스(개체) 생성 — ABox
# ---------------------------------------------------------
def inst(name, cls, label=None):
    g.add((MAR[name], RDF.type, MAR[cls]))
    if label:
        g.add((MAR[name], RDFS.label, Literal(label)))

def rel(s, p, o):
    g.add((MAR[s], MAR[p], MAR[o]))

def lit(s, p, value, dt=None):
    g.add((MAR[s], MAR[p], Literal(value, datatype=dt) if dt else Literal(value)))

# 선종 코드 · 기관
inst("T_Cargo", "VesselType", "화물선(70)")
inst("T_Tanker", "VesselType", "유조선(80)")
inst("T_Passenger", "VesselType", "여객선(60)")
inst("MOF", "Organization", "해양수산부")
inst("KCG", "Organization", "해양경찰청")
inst("BusanRO", "Organization", "부산지방해양수산청")
rel("BusanRO", "isPartOf", "MOF")

# 장소 계층 (이행적 isLocatedIn 검증용)
inst("BusanNewPort_B3", "Berth", "부산신항 제3선석")
inst("BusanNewPort_B7", "Berth", "부산신항 제7선석")
inst("BusanPort", "Port", "부산항")
inst("UlsanPort", "Port", "울산항")
inst("Korea", "Country", "대한민국")
rel("BusanNewPort_B3", "isLocatedIn", "BusanPort")
rel("BusanNewPort_B7", "isLocatedIn", "BusanPort")
rel("BusanPort", "isLocatedIn", "Korea")
rel("UlsanPort", "isLocatedIn", "Korea")

# 해역 (대칭 isAdjacentTo 검증용 — 한 방향만 명시)
inst("BusanSeaArea", "SeaArea", "부산항 해역")
inst("JinhaeBaySeaArea", "SeaArea", "진해만 해역")
rel("BusanSeaArea", "isAdjacentTo", "JinhaeBaySeaArea")

# 법령 계층 (이행적 isPartOf 검증용)
inst("MaritimeSafetyAct", "Act")
lit("MaritimeSafetyAct", "hasName", "해상교통안전법(예시)", XSD.string)
lit("MaritimeSafetyAct", "effectiveDate", "2024-01-26", XSD.date)
inst("MaritimeSafetyDecree", "Decree")
lit("MaritimeSafetyDecree", "hasName", "해상교통안전법 시행령(예시)", XSD.string)

inst("Art15", "Article")
lit("Art15", "hasArticleNo", "제15조", XSD.string)
lit("Art15", "hasName", "항로에서의 항법", XSD.string)
rel("Art15", "isPartOf", "MaritimeSafetyAct")
rel("Art15", "enforcedBy", "MOF")
rel("Art15", "appliesTo", "T_Cargo")

inst("Art15_P1", "Paragraph")
lit("Art15_P1", "hasArticleNo", "제15조제1항", XSD.string)
rel("Art15_P1", "isPartOf", "Art15")

inst("Art15_P1_I3", "Item")
lit("Art15_P1_I3", "hasArticleNo", "제15조제1항제3호", XSD.string)
lit("Art15_P1_I3", "hasName", "항로 안에서의 추월 금지", XSD.string)
lit("Art15_P1_I3", "hasProviso",
    "다만, 부득이한 사유로 허가를 받은 경우에는 그러하지 아니하다.", XSD.string)
rel("Art15_P1_I3", "isPartOf", "Art15_P1")

inst("Art15_P2", "Paragraph")
lit("Art15_P2", "hasArticleNo", "제15조제2항", XSD.string)
rel("Art15_P2", "isPartOf", "Art15")
rel("Art15_P2", "delegatesTo", "MaritimeSafetyDecree")

# 정의 조문
inst("Art2", "Article")
lit("Art2", "hasArticleNo", "제2조", XSD.string)
lit("Art2", "hasName", "정의", XSD.string)
rel("Art2", "isPartOf", "MaritimeSafetyAct")
inst("Term_GiantVessel", "Term", "거대선")
inst("Term_Passage", "Term", "통항")
rel("Art2", "definesTerm", "Term_GiantVessel")
rel("Art2", "definesTerm", "Term_Passage")

# 준용 연쇄: 제43조 → 제15조 → 제10조
inst("Art43", "Article")
lit("Art43", "hasArticleNo", "제43조", XSD.string)
lit("Art43", "hasName", "예인선의 항법 준용", XSD.string)
rel("Art43", "isPartOf", "MaritimeSafetyAct")
rel("Art43", "junyongOf", "Art15")

inst("Art10", "Article")
lit("Art10", "hasArticleNo", "제10조", XSD.string)
lit("Art10", "hasName", "통항의 원칙", XSD.string)
rel("Art10", "isPartOf", "MaritimeSafetyAct")
rel("Art15", "junyongOf", "Art10")

# 벌칙 조문 (준용을 거쳐야 도달 — 이행성 미선언 시 제90조 누락)
inst("Art83", "Article")
lit("Art83", "hasArticleNo", "제83조", XSD.string)
lit("Art83", "hasName", "벌칙", XSD.string)
rel("Art83", "isPartOf", "MaritimeSafetyAct")
rel("Art83", "enforcedBy", "KCG")
rel("Art83", "penalizes", "Art15")

inst("Art90", "Article")
lit("Art90", "hasArticleNo", "제90조", XSD.string)
lit("Art90", "hasName", "과태료", XSD.string)
rel("Art90", "isPartOf", "MaritimeSafetyAct")
rel("Art90", "enforcedBy", "KCG")
rel("Art90", "penalizes", "Art10")

# 선박 1: 화물선
inst("HL_PIONEER", "CargoShip")
lit("HL_PIONEER", "hasName", "HL PIONEER", XSD.string)
lit("HL_PIONEER", "hasMmsi", "440123000", XSD.string)
lit("HL_PIONEER", "hasImoNumber", "9876543", XSD.string)
lit("HL_PIONEER", "hasGrossTonnage", "74000", XSD.decimal)
rel("HL_PIONEER", "hasVesselType", "T_Cargo")
rel("HL_PIONEER", "hasFlagState", "Korea")

# 선박 2: 여객선 (카디널리티 제약 충족)
inst("SEA_QUEEN", "PassengerShip")
lit("SEA_QUEEN", "hasName", "SEA QUEEN", XSD.string)
lit("SEA_QUEEN", "hasMmsi", "440222000", XSD.string)
lit("SEA_QUEEN", "hasGrossTonnage", "12000", XSD.decimal)
rel("SEA_QUEEN", "hasVesselType", "T_Passenger")
rel("SEA_QUEEN", "hasFlagState", "Korea")
inst("CERT_SQ01", "Certificate", "여객선안전검사증서")
lit("CERT_SQ01", "issuedDate", "2025-05-12", XSD.date)
rel("SEA_QUEEN", "hasCertificate", "CERT_SQ01")

# 선박 3: 유조선 (총톤수 5,000 이상 — CQ2 대상)
inst("BLUE_WHALE", "Tanker")
lit("BLUE_WHALE", "hasName", "BLUE WHALE", XSD.string)
lit("BLUE_WHALE", "hasMmsi", "440333000", XSD.string)
lit("BLUE_WHALE", "hasGrossTonnage", "158000", XSD.decimal)
rel("BLUE_WHALE", "hasVesselType", "T_Tanker")
rel("BLUE_WHALE", "hasFlagState", "Korea")

# 선박 4: 유조선 (총톤수 5,000 미만 — 필터 제외 대상)
inst("OCEAN_STAR", "Tanker")
lit("OCEAN_STAR", "hasName", "OCEAN STAR", XSD.string)
lit("OCEAN_STAR", "hasMmsi", "440444000", XSD.string)
lit("OCEAN_STAR", "hasGrossTonnage", "3200", XSD.decimal)
rel("OCEAN_STAR", "hasVesselType", "T_Tanker")


# ---------------------------------------------------------
# [운항 도메인 확장] 클래스 · 속성 · 인스턴스
# ---------------------------------------------------------
add_class("Position", "항적 포인트")
add_class("PortCall", "입출항 이벤트")
add_class("GridCell", "격자 셀")

add_obj_prop("reportedPosition", "항적 보고", "Vessel", "Position")
add_obj_prop("hasPortCall", "입출항 이벤트", "Vessel", "PortCall")
add_obj_prop("atPort", "대상 항만", "PortCall", "Port")
add_obj_prop("atBerth", "접안 선석", "PortCall", "Berth")
add_obj_prop("inCell", "소속 격자", "Position", "GridCell")

# 관측시각과 적재시각을 분리해 "그 값이 언제의 것인가"를 항상 보존한다.
add_data_prop("observedAt", "관측 시각(UTC)", XSD.dateTime)
add_data_prop("ingestedAt", "적재 시각(UTC)", XSD.dateTime)
add_data_prop("latitude", "위도", XSD.decimal, "Position")
add_data_prop("longitude", "경도", XSD.decimal, "Position")
add_data_prop("callType", "입출항 구분", XSD.string, "PortCall")

inst("G_35N_129E", "GridCell", "격자 35.0N 129.0E (0.5도)")
rel("G_35N_129E", "isLocatedIn", "BusanSeaArea")

inst("POS_HL_001", "Position")
lit("POS_HL_001", "latitude", "35.0821", XSD.decimal)
lit("POS_HL_001", "longitude", "129.0412", XSD.decimal)
lit("POS_HL_001", "observedAt", "2026-03-11T08:14:00Z", XSD.dateTime)
lit("POS_HL_001", "ingestedAt", "2026-03-11T08:15:22Z", XSD.dateTime)
rel("POS_HL_001", "inCell", "G_35N_129E")

inst("POS_SQ_001", "Position")
lit("POS_SQ_001", "latitude", "35.0913", XSD.decimal)
lit("POS_SQ_001", "longitude", "129.0355", XSD.decimal)
lit("POS_SQ_001", "observedAt", "2026-03-11T09:02:00Z", XSD.dateTime)
lit("POS_SQ_001", "ingestedAt", "2026-03-11T09:03:10Z", XSD.dateTime)
rel("POS_SQ_001", "inCell", "G_35N_129E")

inst("PC_HL_001", "PortCall", "HL PIONEER 부산항 입항")
lit("PC_HL_001", "callType", "입항", XSD.string)
lit("PC_HL_001", "observedAt", "2026-03-11T08:20:00Z", XSD.dateTime)
rel("PC_HL_001", "atPort", "BusanPort")
rel("PC_HL_001", "atBerth", "BusanNewPort_B3")

inst("PC_SQ_001", "PortCall", "SEA QUEEN 부산항 입항")
lit("PC_SQ_001", "callType", "입항", XSD.string)
lit("PC_SQ_001", "observedAt", "2026-03-11T09:10:00Z", XSD.dateTime)
rel("PC_SQ_001", "atPort", "BusanPort")
rel("PC_SQ_001", "atBerth", "BusanNewPort_B7")

inst("PC_BW_001", "PortCall", "BLUE WHALE 울산항 입항")
lit("PC_BW_001", "callType", "입항", XSD.string)
lit("PC_BW_001", "observedAt", "2026-03-11T11:40:00Z", XSD.dateTime)
rel("PC_BW_001", "atPort", "UlsanPort")

rel("HL_PIONEER", "reportedPosition", "POS_HL_001")
rel("HL_PIONEER", "hasPortCall", "PC_HL_001")
rel("SEA_QUEEN", "reportedPosition", "POS_SQ_001")
rel("SEA_QUEEN", "hasPortCall", "PC_SQ_001")
rel("BLUE_WHALE", "hasPortCall", "PC_BW_001")


# ---------------------------------------------------------
# [단계 6] 표준 형식으로 직렬화 (Turtle)
# ---------------------------------------------------------
if __name__ == "__main__":
    out = "maritime_ontology_generated.ttl"
    g.serialize(destination=out, format="turtle")
    print(f"[OK] 트리플 {len(g)}개 생성 → {out}")
    print("     클래스/속성/인스턴스가 포함된 OWL2 온톨로지가 저장되었습니다.")
