export type Branch = {
  sube_kodu: string;
  sube_adi: string;
  il: string;
  ilce: string;
  sube_tipi: string;
};

export type Metrics = {
  toplam_islem_hacmi: number;
  toplam_gonderi: number;
  toplam_teslim: number;
  toplam_geciken: number;
  toplam_iade: number;
  toplam_sikayet: number;
  toplam_gelir: number;
  teslim_basarisi_pct: number;
  gecikme_orani_pct: number;
  iade_orani_pct: number;
  sikayet_orani_binde: number;
  personel_verimliligi: number;
  dagitici_is_yuku: number;
  gonderi_basi_gelir: number;
  ortalama_teslim_suresi: number;
};

export type BranchSummary = Branch & {
  toplam_kabul: number;
  toplam_teslim: number;
  toplam_geciken: number;
  toplam_iade: number;
  toplam_sikayet: number;
  toplam_gelir: number;
  teslim_basarisi_pct: number;
  gecikme_orani_pct: number;
  iade_orani_pct: number;
  sikayet_orani_binde: number;
  personel_verimliligi: number;
  dagitici_is_yuku: number;
  gonderi_basi_gelir: number;
  ortalama_teslim_suresi: number;
  genel_basari_puani: number;
  genel_basari_alt_puanlari: Record<string, number>;
  genel_basari_katkilari: Record<string, number>;
  siralama?: number;
};

export type TrendPoint = BranchSummary & {
  tarih?: string;
  ay?: string;
  kabul_edilen?: number;
  teslim_edilen?: number;
  geciken?: number;
  sikayet_sayisi?: number;
  toplam_personel?: number;
  dagitici_sayisi?: number;
};

export type Period = { start: string; end: string };

export type MetadataResponse = {
  min_date: string;
  max_date: string;
  record_count: number;
  branch_count: number;
  provinces: string[];
  branch_types: string[];
  validation_warnings: string[];
};

export type FormulaItem = {
  key: string;
  label: string;
  formula: string;
  summary_formula: string;
  unit: string;
  description: string;
  weight_pct: number;
  direction: "higher" | "lower" | "target";
  direction_label: string;
};

export type MethodologyResponse = {
  kpi_formulas: FormulaItem[];
  general_success: {
    label: string;
    formula: string;
    range: string;
    method: string;
    reference_scope: string;
    target_rule: string;
    weights: Record<string, number>;
  };
  analysis: {
    institution_gap_ratio: number;
    period_change_ratio: number;
    minimum_correlation: number;
    complaint_trend_weeks: number;
    minimum_period_days: number;
    note: string;
  };
  anomaly: {
    method: string;
    median_formula: string;
    mad_formula: string;
    scale_formula: string;
    score_formula: string;
    warning_threshold: number;
    high_threshold: number;
    minimum_observations: number;
    metrics: Array<{ key: string; label: string; adverse_direction: number }>;
  };
  scoring_note: string;
};

export type OverviewResponse = {
  metrics: Metrics | null;
  trend: TrendPoint[];
  monthly: TrendPoint[];
  branches: BranchSummary[];
  highlights: { best_branch: BranchSummary; risk_branch: BranchSummary } | null;
  period: Period | null;
  record_count: number;
  branch_count: number;
};

export type BranchDetailResponse = {
  branch: BranchSummary;
  metrics: Metrics;
  deltas: {
    teslim_basarisi_pct: number | null;
    gecikme_orani_pct: number | null;
    ortalama_teslim_suresi: number | null;
  };
  rank: number;
  branch_count: number;
  trend: TrendPoint[];
  monthly: TrendPoint[];
  period: Period;
  record_count: number;
};

export type ComparisonResponse = {
  branches: BranchSummary[];
  monthly: TrendPoint[];
  highlights: {
    best_general: BranchSummary;
    risk_general: BranchSummary;
    best_success: BranchSummary;
    lowest_delay: BranchSummary;
    highest_productivity: BranchSummary;
    highest_unit_revenue: BranchSummary;
  } | null;
  period: Period | null;
  record_count: number;
};

export type Finding = {
  rule_id: string;
  branch_code: string;
  branch_name: string;
  title: string;
  detail: string;
  possible_cause: string;
  evidence: Record<string, number | string>;
  severity: string;
};

export type Anomaly = {
  branch_code: string;
  branch_name: string;
  date: string;
  metric: string;
  metric_label: string;
  actual_value: number;
  expected_value: number;
  deviation_pct: number;
  anomaly_score: number;
  severity: string;
  suggested_check: string;
};

export type AnalysisResponse = {
  findings: Array<{ finding: Finding; action: string }>;
  anomalies: Anomaly[];
  summary: {
    finding_count: number;
    high_findings: number;
    affected_finding_branches: number;
    studied_days: number;
    anomaly_count: number;
    high_anomalies: number;
    affected_anomaly_branches: number;
    latest_anomaly: string | null;
    recommendation_count: number;
  };
  period: Period | null;
};

export type OverviewFilters = {
  startDate?: string;
  endDate?: string;
  provinces?: string[];
  branchTypes?: string[];
  branchCodes?: string[];
};
