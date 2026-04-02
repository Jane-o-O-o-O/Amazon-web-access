// ─── Task ─────────────────────────────────────────────────────────────────────

export type TaskStatus = "queued" | "running" | "done" | "failed";
export type TaskStage =
  | "queued"
  | "crawling"
  | "parsing"
  | "searching"
  | "matching"
  | "analyzing"
  | "pricing"
  | "generating"
  | "done";

export interface TaskProgress {
  taskId: string;
  status: TaskStatus;
  progress: number; // 0-100
  stage: TaskStage;
  error?: string | null;
}

// ─── Product ──────────────────────────────────────────────────────────────────

export interface Product {
  title?: string;
  brand?: string;
  category?: string;
  price_min?: number;
  price_max?: number;
  currency?: string;
  moq?: number;
  material?: string;
  size?: string;
  color?: string;
  package_quantity?: number;
  rating?: number;
  review_count?: number;
  seller_name?: string;
  ship_from?: string;
  images?: string[];
  attributes?: Record<string, string>;
  description?: string;
  source_url?: string;
  platform?: string;
  // Amazon specific
  asin?: string;
  url?: string;
  price?: number;
}

// ─── Match ────────────────────────────────────────────────────────────────────

export type MatchLevel = "same" | "high" | "medium" | "low";

export interface MatchResult {
  match_score: number;
  match_level: MatchLevel;
  title_similarity?: number;
  attribute_overlap?: number;
  category_match?: number;
  material_match?: number;
  size_match?: number;
  price_reasonableness?: number;
  same_points?: string[];
  diff_points?: string[];
  final_reason?: string;
  candidate: Product;
  error?: string;
}

// ─── Competitor Analysis ──────────────────────────────────────────────────────

export interface PricingRange {
  min: number;
  max: number;
  main_range: string;
}

export interface CompetitorAnalysis {
  market_summary: string;
  pricing_range: PricingRange;
  top_features: string[];
  complaint_topics: string[];
  keyword_themes: string[];
  differentiation_suggestions: string[];
  market_opportunity: string;
  risk_warnings: string[];
}

// ─── Margin ───────────────────────────────────────────────────────────────────

export interface MarginResult {
  purchase_usd: number;
  domestic_shipping_usd: number;
  international_shipping: number;
  fba_fee: number;
  commission: number;
  ads_cost: number;
  tax: number;
  total_cost: number;
  sell_price: number;
  gross_profit: number;
  net_profit: number;
  gross_margin: number;
  net_margin: number;
  suggested_price_min: number;
  suggested_price_max: number;
}

// ─── Listing ──────────────────────────────────────────────────────────────────

export interface ListingDraft {
  title: string;
  bullets: string[];
  description: string;
  search_terms: string;
  image_copy_suggestions?: Array<{ image_number: number; copy: string }>;
}

// ─── Task Result ──────────────────────────────────────────────────────────────

export interface TaskResult {
  task_id: string;
  status: TaskStatus;
  source_product: Product;
  candidates: MatchResult[];
  competitor_analysis: CompetitorAnalysis;
  margin: MarginResult;
  listing: ListingDraft;
}

// ─── Cost Params ──────────────────────────────────────────────────────────────

export interface CostParams {
  purchasePrice: number;
  domesticShipping: number;
  internationalShipping: number;
  fbaFee: number;
  commissionRate: number;
  adsRate: number;
  taxRate: number;
  exchangeRate: number;
}

export interface CreateTaskRequest {
  sourceUrl: string;
  targetMarketplace: string;
  cost: CostParams;
}
