"""
CAIP-Karnataka — Intelligence Report Endpoint
Dispatches the KarnatakaCrimeIntelligenceSupervisor pipeline.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import re
import json

from app.core.db import get_db, AsyncSessionLocal
from app.models.orm_models import PdfIntelligenceData
from app.core.security import require_any
from app.services.agents.crime_category_agent import CrimeCategoryAnalysisAgent
from app.services.agents.crime_trend_agent import CrimeTrendAgent
from app.services.agents.district_ranking_agent import DistrictRankingAgent
from app.services.supervisor import KarnatakaCrimeIntelligenceSupervisor

router = APIRouter(prefix="/intelligence", tags=["Crime Intelligence"])

supervisor = KarnatakaCrimeIntelligenceSupervisor()


@router.get("/report")
async def get_full_report(
    district_code: Optional[str] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_any),
):
    """
    Primary dashboard endpoint. Dispatches DistrictRanking,
    CrimeCategoryAnalysis, CrimeTrend agents (all real-data-backed),
    plus CriminalNetwork/RepeatOffender/Anomaly agents (which will
    return honest disabled-feature results unless their feature flags
    are enabled with real supporting data).
    """
    return await supervisor.generate_full_report(db=db, district_code=district_code, year=year)


@router.get("/district-ranking")
async def get_district_ranking(
    year: Optional[int] = None,
    ranking_basis: Optional[str] = "raw_count",
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_any),
):
    agent = DistrictRankingAgent()
    result = await agent.execute(db=db, year=year, ranking_basis=ranking_basis)
    return {
        "success": result.success, "confidence": result.confidence,
        "data": result.data, "warnings": result.warnings,
    }


@router.get("/crime-categories")
async def get_crime_categories(
    district_code: Optional[str] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_any),
):
    agent = CrimeCategoryAnalysisAgent()
    result = await agent.execute(db=db, district_code=district_code, year=year)
    return {
        "success": result.success, "confidence": result.confidence,
        "data": result.data, "warnings": result.warnings,
    }


@router.get("/trend")
async def get_trend(
    district_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_any),
):
    agent = CrimeTrendAgent()
    result = await agent.execute(db=db, district_code=district_code)
    return {
        "success": result.success, "confidence": result.confidence,
        "data": result.data, "warnings": result.warnings,
    }


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_any),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    try:
        import pdfplumber
    except ImportError:
        raise HTTPException(status_code=500, detail="pdfplumber is not installed on the server.")

    content = await file.read()
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    extracted_text = ""
    try:
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
    finally:
        os.remove(tmp_path)

    # Strict NLP/Regex Heuristics for single lines
    offender_pattern = r"^(?:Accused|Arrested)\s*(?:accused)?\s*:\s*([A-Za-z \t]+)(?:\s+alias\s+)?([A-Za-z \t]+)?$"
    associate_pattern = r"^(?:Associates|Co-offenders)\s*:\s*([A-Za-z \t,]+)$"
    
    offenders = []
    associates = []

    for line in extracted_text.splitlines():
        line = line.strip()
        if not line:
            continue
            
        o_match = re.search(offender_pattern, line, re.IGNORECASE)
        if o_match:
            name = o_match.group(1).strip()
            alias = o_match.group(2).strip() if o_match.group(2) else None
            # Strict filter for valid names (extra safety)
            if "doc:" in name.lower() or ".pdf" in name.lower() or "offender id" in name.lower() or "total crimes" in name.lower() or "risk level" in name.lower():
                continue
            if len(name) > 2:
                offenders.append({"name": name, "alias": alias})
                
        a_match = re.search(associate_pattern, line, re.IGNORECASE)
        if a_match:
            assocs = [a.strip() for a in a_match.group(1).split(',')]
            for a in assocs:
                if "doc:" in a.lower() or ".pdf" in a.lower() or "offender id" in a.lower() or "total crimes" in a.lower() or "risk level" in a.lower():
                    continue
                if len(a) > 2:
                    associates.append(a)

    parsed_json = {
        "offenders": offenders,
        "associates": associates,
    }

    new_pdf = PdfIntelligenceData(
        filename=file.filename,
        extracted_text=extracted_text,
        parsed_json=parsed_json
    )
    db.add(new_pdf)
    await db.commit()

    return {"success": True, "message": f"Successfully parsed {file.filename}.", "data": parsed_json}


@router.get("/network")
async def get_network(
    district_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_any),
):
    from sqlalchemy import select
    result = await db.execute(select(PdfIntelligenceData))
    pdfs = result.scalars().all()

    if not pdfs:
        # Strict empty fallback for dynamic data
        return {
            "success": True,
            "data": {
                "nodes": [],
                "links": []
            }
        }

    nodes_dict = {}
    links = []
    seen_links = set()

    # Pass 1: Count offender frequency to determine risk_level
    offender_counts = {}
    for pdf in pdfs:
        data = pdf.parsed_json or {}
        for o in data.get("offenders", []):
            name_key = f"{o['name']}"
            offender_counts[name_key] = offender_counts.get(name_key, 0) + 1
            
    for pdf in pdfs:
        data = pdf.parsed_json or {}
        offenders = data.get("offenders", [])
        associates = data.get("associates", [])
        
        for o in offenders:
            node_id = f"A_{o['name']}"
            count = offender_counts.get(o['name'], 1)
            risk = "High" if count >= 3 else ("Medium" if count == 2 else "Low")
            
            if node_id not in nodes_dict:
                nodes_dict[node_id] = {
                    "id": node_id, 
                    "group": "Accused", 
                    "label": f"{o['name']} {('('+o['alias']+')') if o['alias'] else ''}",
                    "risk_level": risk
                }
            
            for a in associates:
                assoc_id = f"A_{a}"
                # If associate not seen, give default Low risk
                if assoc_id not in nodes_dict:
                    nodes_dict[assoc_id] = {
                        "id": assoc_id, 
                        "group": "Accused", 
                        "label": a,
                        "risk_level": "Low"
                    }
                
                # Only link Accused to Associate (no FIR node)
                link_key = tuple(sorted([node_id, assoc_id]))
                if link_key not in seen_links and node_id != assoc_id:
                    links.append({"source": node_id, "target": assoc_id, "value": 1})
                    seen_links.add(link_key)

    nodes = list(nodes_dict.values())

    return {
        "success": True,
        "data": {
            "nodes": nodes,
            "links": links
        }
    }


@router.get("/offenders")
async def get_offenders(
    district_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_any),
):
    from sqlalchemy import select
    result = await db.execute(select(PdfIntelligenceData))
    pdfs = result.scalars().all()

    if not pdfs:
        # Strict empty fallback for dynamic data
        return {
            "success": True,
            "data": []
        }
        
    offender_counts = {}
    for pdf in pdfs:
        data = pdf.parsed_json or {}
        for o in data.get("offenders", []):
            name = f"{o['name']} {('alias '+o['alias']) if o['alias'] else ''}"
            offender_counts[name] = offender_counts.get(name, 0) + 1

    out = []
    for idx, (name, count) in enumerate(sorted(offender_counts.items(), key=lambda x: -x[1])):
        risk = "High" if count >= 3 else ("Medium" if count == 2 else "Low")
        out.append({"id": idx+1, "name": name, "crimes_count": count, "risk_level": risk})

    return {
        "success": True,
        "data": out
    }


@router.get("/anomalies")
async def get_anomalies(
    district_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_any),
):
    from sqlalchemy import select, func
    from app.models.orm_models import DistrictYearTotals, District
    import statistics

    # If district_code is provided, get that district's totals, else get statewide totals per year
    if district_code:
        stmt = (
            select(DistrictYearTotals.year, DistrictYearTotals.total_ipc_crimes)
            .join(District, DistrictYearTotals.district_id == District.district_id)
            .where(District.district_code == district_code)
            .order_by(DistrictYearTotals.year)
        )
    else:
        stmt = (
            select(DistrictYearTotals.year, func.sum(DistrictYearTotals.total_ipc_crimes))
            .group_by(DistrictYearTotals.year)
            .order_by(DistrictYearTotals.year)
        )

    result = await db.execute(stmt)
    records = result.all()

    if not records:
        return {"success": True, "data": []}

    # Calculate mean and std dev
    counts = [float(r[1]) for r in records if r[1] is not None]
    if len(counts) < 2:
        return {
            "success": True,
            "data": [{"year": str(r[0]), "count": r[1], "is_anomaly": False} for r in records]
        }

    mean = statistics.mean(counts)
    stdev = statistics.stdev(counts) if len(counts) > 1 else 0

    data = []
    for r in records:
        year = str(r[0])
        count = float(r[1] or 0)
        # Mark as anomaly if it's > 1.5 standard deviations above the mean (or 2)
        is_anomaly = (count > mean + 1.5 * stdev) if stdev > 0 else False
        data.append({
            "year": year,
            "count": count,
            "is_anomaly": is_anomaly
        })

    return {
        "success": True,
        "data": data
    }



