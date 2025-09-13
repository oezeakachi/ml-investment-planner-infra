import { NextResponse } from 'next/server'

// temporary mock so UI works
export async function POST() {
  return NextResponse.json({
    weights: [{ ticker: 'NVDA', weight: 0.3 }, { ticker: 'AAPL', weight: 0.2 }],
    expected_return: 0.12,
    volatility: 0.18,
    prob_reach_goal: 0.75,
    p5: 150000,
    p50: 260000,
    p95: 550000,
  })
}
