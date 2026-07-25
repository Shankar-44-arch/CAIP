// CAIP-Karnataka — Shared TypeScript types (mirrors backend/app/schemas/schemas.py)

export interface DistrictRankingItem {
  rank: number;
  district_code: string;
  district_name: string;
  total_ipc_crimes: number;
  crime_rate_per_lakh: number | null;
  z_score_vs_state_mean: number;
  elevated: boolean;
  ranking_basis: string;
}

export interface CrimeCategoryGroup {
  crime_group: string;
  count: number;
  pct_of_total: number;
}

export interface DisabledFeature {
  feature: string;
  status: string;
  reason: string;
}

export interface ExecutiveSummary {
  headline: string;
  period: string;
  total_ipc_crimes_statewide: number;
  districts_analyzed: number;
  data_year: number | null;
  key_takeaway: string;
  data_maturity_notice: string;
}

export interface AuditTrailEntry {
  agent: string;
  action: string;
  data_sources: string[];
  timestamp: string;
  duration_ms: number | null;
}

export interface KarnatakaCrimeReport {
  executive_summary: ExecutiveSummary;
  key_findings: string[];
  district_ranking: DistrictRankingItem[];
  crime_category_breakdown: {
    year?: number;
    grand_total?: number;
    group_breakdown?: CrimeCategoryGroup[];
    sub_head_breakdown?: { crime_head_name: string; crime_group: string; count: number; pct_of_total: number }[];
  };
  trend_analysis: {
    method?: string;
    is_prediction?: boolean;
    year_analyzed?: number;
    district_relative_burden?: { district_code: string; district_name: string; total_ipc_crimes: number; relative_to_state_mean: number | null }[];
    explainability?: { method: string; note: string };
  };
  network_analysis: null;
  repeat_offender_analysis: null;
  anomaly_alerts: unknown[];
  disabled_features: DisabledFeature[];
  recommendations: string[];
  confidence_scores: Record<string, number>;
  audit_trail: AuditTrailEntry[];
  generated_at: string;
  overall_confidence: number;
}

export interface District {
  district_code: string;
  district_name: string;
  historical_data_name: string | null;
  is_geographic_district: boolean;
  jurisdiction_type: string;
  population_2011_census: number | null;
  data_available_from: number;
  notes: string | null;
  centroid: { lat: number; lng: number } | null;
}
