export type Offer = {
  id: number;
  company: string;
  role: string;
  location: string;
  base_salary: number;
  annual_bonus: number;
  annual_equity: number;
  sign_on_bonus: number;
  col_index: number;
  created_at: string;
  updated_at: string;
};

export type OfferInput = {
  company: string;
  role: string;
  location: string;
  base_salary: number;
  annual_bonus?: number;
  annual_equity?: number;
  sign_on_bonus?: number;
  col_index?: number;
};

export type CompareOffer = Offer & {
  total_comp_annual: number;
  total_comp_year1: number;
  total_comp_col_adjusted: number;
};

export type CompareResponse = {
  offers: CompareOffer[];
};

export type Metric = "total_comp_annual" | "total_comp_year1" | "total_comp_col_adjusted";
