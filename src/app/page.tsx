'use client'
import { useState } from 'react'
import { TrendingUp, DollarSign } from 'lucide-react'
import { InputField } from '@/components/InputField'
import { SelectField } from '@/components/SelectField'
import { ResultCard, StatItem } from '@/components/ResultCard'
import { FormData, FormErrors, PlanResult } from '@/types'
import { validateForm } from '@/lib/validation'
import { formatCurrency, formatPercentage } from '@/lib/formatters'

export default function Home() {
  const [form, setForm] = useState<FormData>({
    targetGoal: '', yearsToInvest: '', monthlyContribution: '', startingCapital: '', riskTolerance: ''
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PlanResult | null>(null)

  const handleChange = (field: keyof FormData, v: string) => {
    setForm(f => ({ ...f, [field]: v }))
    if (errors[field]) setErrors(e => ({ ...e, [field]: undefined }))
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const errs = validateForm(form)
    if (Object.keys(errs).length) return setErrors(errs)
    setLoading(true)
    try {
      const res = await fetch('/api/plan', {
        method: 'POST',
        body: JSON.stringify({
          target_goal: +form.targetGoal.replace(/[£,]/g, ''),
          years_to_invest: +form.yearsToInvest,
          monthly_contribution: +form.monthlyContribution.replace(/[£,]/g, ''),
          starting_capital: +form.startingCapital.replace(/[£,]/g, ''),
          risk_tolerance: form.riskTolerance
        }),
        headers: { 'Content-Type': 'application/json' }
      })
      setResult(await res.json())
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-gradient-to-br from-primary-700 via-primary-800 to-primary-900 text-white py-16 text-center">
        <div className="flex justify-center mb-6">
          <div className="p-4 bg-white/10 rounded-full backdrop-blur-sm">
            <TrendingUp className="h-12 w-12 text-white" />
          </div>
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold mb-4 leading-tight">
          Goal-based Investment Planner
        </h1>
        <p className="text-xl text-primary-100 max-w-2xl mx-auto leading-relaxed">
          Plan your investments to meet your future financial goals with data-driven
          portfolio recommendations and Monte Carlo analysis.
        </p>
      </header>


      <section className="max-w-3xl mx-auto p-6">
        <form onSubmit={submit} className="bg-white p-6 rounded-xl shadow space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <InputField label="Target Goal" id="goal" type="text" placeholder="250000"
              value={form.targetGoal} onChange={v => handleChange('targetGoal', v)}
              error={errors.targetGoal} prefix="£" required />
            <InputField label="Years to Invest" id="years" type="number" placeholder="5"
              value={form.yearsToInvest} onChange={v => handleChange('yearsToInvest', v)}
              error={errors.yearsToInvest} required />
            <InputField label="Monthly Contribution" id="contrib" type="text" placeholder="1000"
              value={form.monthlyContribution} onChange={v => handleChange('monthlyContribution', v)}
              error={errors.monthlyContribution} prefix="£" required />
            <InputField label="Starting Capital" id="capital" type="text" placeholder="20000"
              value={form.startingCapital} onChange={v => handleChange('startingCapital', v)}
              error={errors.startingCapital} prefix="£" required />
          </div>

          <SelectField
            label="Risk Tolerance" id="risk" value={form.riskTolerance}
            onChange={v => handleChange('riskTolerance', v)}
            options={[
              { value: 'conservative', label: 'Conservative' },
              { value: 'balanced', label: 'Balanced' },
              { value: 'aggressive', label: 'Aggressive' }
            ]}
            error={errors.riskTolerance} required
          />

          <button disabled={loading}
            className="w-full flex justify-center items-center gap-2 bg-primary-700 hover:bg-primary-800 text-white py-3 rounded-lg font-semibold">
            {loading && <div className="h-5 w-5 border-2 border-white border-t-transparent animate-spin rounded-full" />}
            <DollarSign className="h-5 w-5" />Generate Plan
          </button>
        </form>

        {result && (
          <div className="mt-12 space-y-6">
            <ResultCard title="Recommended Portfolio">
              {result.weights.map((w, i) =>
                <div key={i} className="flex justify-between border-b py-2">
                  <span>{w.ticker}</span><span>{(w.weight * 100).toFixed(1)}%</span>
                </div>
              )}
            </ResultCard>
            <ResultCard title="Portfolio Stats">
              <div className="grid grid-cols-2 gap-4">
                <StatItem label="Expected Return" value={formatPercentage(result.expected_return)} />
                <StatItem label="Volatility" value={formatPercentage(result.volatility)} />
              </div>
            </ResultCard>
            <ResultCard title="Goal Probability">
              <div className="grid grid-cols-3 gap-4">
                <StatItem label="5th percentile" value={formatCurrency(result.p5)} />
                <StatItem label="Median" value={formatCurrency(result.p50)} />
                <StatItem label="95th percentile" value={formatCurrency(result.p95)} />
              </div>
            </ResultCard>
          </div>
        )}
      </section>
    </main>
  )
}
