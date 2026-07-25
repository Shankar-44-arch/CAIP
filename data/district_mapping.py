from __future__ import annotations
from dataclasses import dataclass

@dataclass
class DistrictMapping:
    historical_data_name: str
    official_district: str
    district_code: str
    notes: str = ""

DISTRICT_MAPPINGS: list[DistrictMapping] = [
    DistrictMapping("BAGALKOT", "Bagalkote", "BGK"),
    DistrictMapping("BANGALORE COMMR.", "Bengaluru Urban", "BLR"),
    DistrictMapping("BANGALORE RURAL", "Bengaluru Rural", "BLRR"),
    DistrictMapping("BELGAUM", "Belagavi", "BGM"),
    DistrictMapping("BELLARY", "Ballari", "BLY"),
    DistrictMapping("BIDAR", "Bidar", "BDR"),
    DistrictMapping("BIJAPUR", "Vijayapura", "VJP"),
    DistrictMapping("CBPURA", "Chikkaballapura", "CKB"),
    DistrictMapping("CHAMARAJNAGAR", "Chamarajanagar", "CMN"),
    DistrictMapping("CHICKMAGALUR", "Chikkamagaluru", "CKM"),
    DistrictMapping("CHITRADURGA", "Chitradurga", "CTD"),
    DistrictMapping("DAKSHIN KANNADA", "Dakshina Kannada", "DK"),
    DistrictMapping("DAVANAGERE", "Davanagere", "DVG"),
    DistrictMapping("DHARWAD COMMR.", "Hubballi-Dharwad (Urban/Commissionerate)", "HDU"),
    DistrictMapping("DHARWAD RURAL", "Dharwad", "DWD"),
    DistrictMapping("GADAG", "Gadag", "GDG"),
    DistrictMapping("GULBARGA", "Kalaburagi", "KLB"),
    DistrictMapping("HASSAN", "Hassan", "HSN"),
    DistrictMapping("HAVERI", "Haveri", "HVR"),
    DistrictMapping("K.G.F.", "Kolar Gold Fields (KGF town, Kolar district)", "KGF"),
    DistrictMapping("KODAGU", "Kodagu", "KDG"),
    DistrictMapping("KOLAR", "Kolar", "KLR"),
    DistrictMapping("KOPPAL", "Koppal", "KPL"),
    DistrictMapping("MANDYA", "Mandya", "MND"),
    DistrictMapping("MANGALORE CITY", "Mangaluru (City/Commissionerate)", "MNG"),
    DistrictMapping("MYSORE COMMR.", "Mysuru (Urban/Commissionerate)", "MYSU"),
    DistrictMapping("MYSORE RURAL", "Mysuru", "MYS"),
    DistrictMapping("RAICHUR", "Raichur", "RCH"),
    DistrictMapping("RAILWAYS", "Government Railway Police (GRP) — cross-district", "GRP"),
    DistrictMapping("RAMANAGAR", "Ramanagara", "RMN"),
    DistrictMapping("SHIMOGA", "Shivamogga", "SHV"),
    DistrictMapping("TUMKUR", "Tumakuru", "TMK"),
    DistrictMapping("UDUPI", "Udupi", "UDP"),
    DistrictMapping("UTTAR KANNADA", "Uttara Kannada", "UK"),
    DistrictMapping("YADGIRI", "Yadgir", "YDG"),

    # --- 2014 specific mappings ---
    DistrictMapping("Ballari", "Ballari", "BLY"),
    DistrictMapping("Belagavi City", "Belagavi City", "BGC"),
    DistrictMapping("Belagavi District", "Belagavi", "BGM"),
    DistrictMapping("Bengaluru City", "Bengaluru Urban", "BLR"),
    DistrictMapping("Bengaluru District", "Bengaluru Rural", "BLRR"),
    DistrictMapping("Chikkaballapura", "Chikkaballapura", "CKB"),
    DistrictMapping("Chikkamagaluru", "Chikkamagaluru", "CKM"),
    DistrictMapping("Dakshina Kannada", "Dakshina Kannada", "DK"),
    DistrictMapping("Dharwad", "Dharwad", "DWD"),
    DistrictMapping("Hubballi Dharwad City", "Hubballi-Dharwad (Urban/Commissionerate)", "HDU"),
    DistrictMapping("K.Railways", "Government Railway Police (GRP) — cross-district", "GRP"),
    DistrictMapping("Kalaburgi", "Kalaburagi", "KLB"),
    DistrictMapping("Mangaluru City", "Mangaluru (City/Commissionerate)", "MNG"),
    DistrictMapping("Mysuru City", "Mysuru (Urban/Commissionerate)", "MYSU"),
    DistrictMapping("Mysuru District", "Mysuru", "MYS"),
    DistrictMapping("Tumakuru", "Tumakuru", "TMK"),
    DistrictMapping("Uttara Kannada", "Uttara Kannada", "UK"),
    DistrictMapping("Vijayapura", "Vijayapura", "VJP"),
]

DISTRICTS_MISSING_FROM_2013_DATA: list[dict] = [
    {
        "official_district": "Vijayanagara",
        "district_code": "VJN",
        "notes": "Created 2021",
    },
]

CURRENT_KARNATAKA_DISTRICTS_OFFICIAL = sorted({
    m.official_district for m in DISTRICT_MAPPINGS
    if "cross-district" not in m.official_district
} | {d["official_district"] for d in DISTRICTS_MISSING_FROM_2013_DATA})
