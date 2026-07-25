
from __future__ import annotations

# district_code (matches data/district_mapping.py) -> (lat, lng, hq_town)
KARNATAKA_DISTRICT_CENTROIDS: dict[str, tuple[float, float, str]] = {
    "BGK":  (16.1691, 75.6636, "Bagalkote"),
    "BLR":  (12.9716, 77.5946, "Bengaluru"),
    "BLRR": (13.2846, 77.5881, "Bengaluru Rural (Devanahalli area)"),
    "BGM":  (15.8497, 74.4977, "Belagavi"),
    "BLY":  (15.1394, 76.9214, "Ballari"),
    "BDR":  (17.9104, 77.5199, "Bidar"),
    "VJP":  (16.8302, 75.7100, "Vijayapura"),
    "CKB":  (13.4355, 77.7315, "Chikkaballapura"),
    "CMN":  (11.9236, 76.9456, "Chamarajanagar"),
    "CKM":  (13.3161, 75.7720, "Chikkamagaluru"),
    "CTD":  (14.2296, 76.3985, "Chitradurga"),
    "DK":   (12.9141, 74.8560, "Mangaluru (Dakshina Kannada HQ)"),
    "DVG":  (14.4644, 75.9218, "Davanagere"),
    "HDU":  (15.3647, 75.1240, "Hubballi (Commissionerate)"),
    "DWD":  (15.4589, 75.0078, "Dharwad"),
    "GDG":  (15.4318, 75.6303, "Gadag"),
    "KLB":  (17.3297, 76.8343, "Kalaburagi"),
    "HSN":  (13.0033, 76.1004, "Hassan"),
    "HVR":  (14.7936, 75.4044, "Haveri"),
    "KGF":  (12.9585, 78.2666, "Kolar Gold Fields"),
    "KDG":  (12.4244, 75.7382, "Madikeri (Kodagu HQ)"),
    "KLR":  (13.1367, 78.1298, "Kolar"),
    "KPL":  (15.3467, 76.1548, "Koppal"),
    "MND":  (12.5242, 76.8958, "Mandya"),
    "MNG":  (12.9141, 74.8560, "Mangaluru (City)"),
    "MYSU": (12.2958, 76.6394, "Mysuru (Commissionerate)"),
    "MYS":  (12.2958, 76.6394, "Mysuru"),
    "RCH":  (16.2076, 77.3463, "Raichur"),
    "GRP":  (None, None, "Government Railway Police — not a geographic district"),
    "RMN":  (12.7217, 77.2812, "Ramanagara"),
    "SHV":  (13.9299, 75.5681, "Shivamogga"),
    "TMK":  (13.3379, 77.1173, "Tumakuru"),
    "UDP":  (13.3409, 74.7421, "Udupi"),
    "UK":   (14.7873, 74.6197, "Karwar (Uttara Kannada HQ)"),
    "YDG":  (16.7708, 77.1376, "Yadgir"),
    "VJN":  (15.1899, 76.4661, "Hosapete (Vijayanagara HQ)"),
}

# Karnataka state-level bounding box (for map default view / validation
# that incoming coordinates actually fall within the state)
KARNATAKA_BOUNDING_BOX = {
    "min_lat": 11.5945,
    "max_lat": 18.4514,
    "min_lng": 74.0543,
    "max_lng": 78.5860,
}

KARNATAKA_STATE_CENTROID = (15.3173, 75.7139)  # approximate geographic center


def is_within_karnataka(lat: float, lng: float) -> bool:
    """Validation helper: reject coordinates clearly outside Karnataka's
    bounding box (defensive check before accepting any future geocoded
    incident data into the system)."""
    bb = KARNATAKA_BOUNDING_BOX
    return bb["min_lat"] <= lat <= bb["max_lat"] and bb["min_lng"] <= lng <= bb["max_lng"]
