export interface FormData {
  targetGoal: string;
  yearsToInvest: string;
  monthlyContribution: string;
  startingCapital: string;
  riskTolerance: string;
}

export interface FormErrors {
  targetGoal?: string;
  yearsToInvest?: string;
  monthlyContribution?: string;
  startingCapital?: string;
  riskTolerance?: string;
}

export interface PortfolioWeight {
  ticker: string;
  company_name: string;
  weight: number;
  current_price: number;
  initial_allocation_gbp: number;
  shares_to_buy: number;
}

export interface PlanResult {
  weights: PortfolioWeight[];
  expected_return: number;
  volatility: number;
  prob_reach_goal: number;
  expected_final_value: number;
  low_estimate: number;
  high_estimate: number;
  initial_capital: number;
}
