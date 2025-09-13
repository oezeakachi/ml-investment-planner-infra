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
  weight: number;
}

export interface PlanResult {
  weights: PortfolioWeight[];
  expected_return: number;
  volatility: number;
  prob_reach_goal: number;
  p5: number;
  p50: number;
  p95: number;
}
