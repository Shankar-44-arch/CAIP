from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class CrimeSubHeadMapping:
    csv_column: str
    crime_sub_head: str
    crime_head_group: str
    is_aggregate: bool = False
    notes: str = ""

CRIME_CATEGORY_MAPPINGS: list[CrimeSubHeadMapping] = [
    # ── Crimes Against Body ──────────────────────────────────────
    CrimeSubHeadMapping("MURDER", "Murder", "Crimes Against Body"),
    CrimeSubHeadMapping("ATTEMPT TO MURDER", "Attempt to Murder", "Crimes Against Body"),
    CrimeSubHeadMapping("CULPABLE HOMICIDE NOT AMOUNTING TO MURDER",
                        "Culpable Homicide Not Amounting to Murder", "Crimes Against Body"),
    CrimeSubHeadMapping("HURT/GREVIOUS HURT", "Hurt / Grievous Hurt", "Crimes Against Body"),
    CrimeSubHeadMapping("CAUSING DEATH BY NEGLIGENCE", "Death by Negligence", "Crimes Against Body"),
    CrimeSubHeadMapping("RIOTS", "Riots", "Crimes Against Body"),
    CrimeSubHeadMapping("ARSON", "Arson", "Crimes Against Property"),

    # ── Crimes Against Women (official NCRB/KSCRB grouping) ──────
    CrimeSubHeadMapping("RAPE", "Rape", "Crimes Against Women", is_aggregate=True),
    CrimeSubHeadMapping("CUSTODIAL RAPE", "Custodial Rape", "Crimes Against Women"),
    CrimeSubHeadMapping("OTHER RAPE", "Rape (Other)", "Crimes Against Women"),
    CrimeSubHeadMapping("DOWRY DEATHS", "Dowry Death", "Crimes Against Women"),
    CrimeSubHeadMapping("ASSAULT ON WOMEN WITH INTENT TO OUTRAGE HER MODESTY",
                        "Assault on Women (Outraging Modesty)", "Crimes Against Women"),
    CrimeSubHeadMapping("INSULT TO MODESTY OF WOMEN", "Insult to Modesty of Women",
                        "Crimes Against Women"),
    CrimeSubHeadMapping("CRUELTY BY HUSBAND OR HIS RELATIVES",
                        "Cruelty by Husband or Relatives (Sec. 498A)", "Crimes Against Women"),
    CrimeSubHeadMapping("IMPORTATION OF GIRLS FROM FOREIGN COUNTRIES",
                        "Importation of Girls from Foreign Countries", "Crimes Against Women"),

    # ── Kidnapping & Abduction ────────────────────────────────────
    CrimeSubHeadMapping("KIDNAPPING & ABDUCTION", "Kidnapping & Abduction (Total)",
                        "Kidnapping & Abduction", is_aggregate=True),
    CrimeSubHeadMapping("KIDNAPPING AND ABDUCTION OF WOMEN AND GIRLS",
                        "Kidnapping & Abduction of Women and Girls", "Kidnapping & Abduction"),
    CrimeSubHeadMapping("KIDNAPPING AND ABDUCTION OF OTHERS",
                        "Kidnapping & Abduction of Others", "Kidnapping & Abduction"),

    # ── Crimes Against Property ───────────────────────────────────
    CrimeSubHeadMapping("DACOITY", "Dacoity", "Crimes Against Property"),
    CrimeSubHeadMapping("PREPARATION AND ASSEMBLY FOR DACOITY",
                        "Preparation & Assembly for Dacoity", "Crimes Against Property"),
    CrimeSubHeadMapping("ROBBERY", "Robbery", "Crimes Against Property"),
    CrimeSubHeadMapping("BURGLARY", "Burglary", "Crimes Against Property"),
    CrimeSubHeadMapping("THEFT", "Theft (Total)", "Crimes Against Property", is_aggregate=True),
    CrimeSubHeadMapping("AUTO THEFT", "Motor Vehicle Theft", "Crimes Against Property"),
    CrimeSubHeadMapping("OTHER THEFT", "Theft (Other)", "Crimes Against Property"),
    CrimeSubHeadMapping("CRIMINAL BREACH OF TRUST", "Criminal Breach of Trust",
                        "Economic Offences"),
    CrimeSubHeadMapping("CHEATING", "Cheating", "Economic Offences"),
    CrimeSubHeadMapping("COUNTERFIETING", "Counterfeiting", "Economic Offences"),

    # ── Residual / Other ─────────────────────────────────────────
    CrimeSubHeadMapping("OTHER IPC CRIMES", "Other IPC Crimes", "Other IPC Offences"),
]

CRIME_HEAD_GROUPS = sorted({m.crime_head_group for m in CRIME_CATEGORY_MAPPINGS})
