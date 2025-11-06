import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchSuggestedBudget } from '../services/api'
import { Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, ReferenceLine } from 'recharts'
import { useState, useEffect } from 'react'
import { X, Save } from 'lucide-react'

interface SuggestedBudgetCardProps {
  userId: string
  month?: string
  lookbackMonths?: number
}

export default function SuggestedBudgetCard({ userId, month, lookbackMonths = 6 }: SuggestedBudgetCardProps) {
  const [isClosed, setIsClosed] = useState(false)
  const queryClient = useQueryClient()
  const { data: budget, isLoading, error } = useQuery({
    queryKey: ['suggestedBudget', userId, month, lookbackMonths],
    queryFn: () => fetchSuggestedBudget(userId, month, lookbackMonths),
    enabled: !!userId && !isClosed,
  })
  
  const [sliderValue, setSliderValue] = useState<number>(0)
  const [isSaving, setIsSaving] = useState(false)
  
  useEffect(() => {
    if (budget?.total_budget) {
      setSliderValue(budget.total_budget)
    }
  }, [budget])
  
  const minBudget = budget?.min_budget || 0
  const maxBudget = budget?.max_budget || (budget?.total_budget || 0) * 2
  const suggestedBudget = budget?.total_budget || 0
  const clampedValue = Math.max(minBudget, Math.min(maxBudget, sliderValue))
  
  const saveBudgetMutation = useMutation({
    mutationFn: async (amount: number) => {
      const response = await fetch(`/api/insights/${userId}/budget`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount,
          month: month || new Date().toISOString().slice(0, 7),
        }),
      })
      if (!response.ok) throw new Error('Failed to save budget')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suggestedBudget', userId] })
      queryClient.invalidateQueries({ queryKey: ['budgetTracking', userId] })
      setIsSaving(false)
    },
    onError: () => setIsSaving(false),
  })
  
  const handleSaveBudget = () => {
    setIsSaving(true)
    saveBudgetMutation.mutate(clampedValue)
  }
  
  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSliderValue(parseFloat(e.target.value))
  }

  if (isClosed) {
    return null
  }

  if (isLoading) {
    return (
      <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
        <div className="text-white">Loading budget suggestion...</div>
      </div>
    )
  }

  if (error || !budget) {
    return (
      <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
        <div className="text-red-300">Failed to load budget suggestion</div>
      </div>
    )
  }

  const chartData = (budget.history || []).map((month: any) => ({
    month: new Date(month.month + '-01').toLocaleDateString('en-US', { month: 'short' }),
    spending: month.total_spending || 0,
    income: month.total_income || 0,
  }))

  return (
    <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-4xl font-serif text-white mb-2">Suggested Monthly Budget</h1>
        <p className="text-white/80 text-sm">
          AI-powered budget recommendations based on your spending patterns.
        </p>
      </div>

      {/* Main Card */}
      <div className="relative bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 shadow-xl">
        {/* Close Button */}
        <button
          onClick={() => setIsClosed(true)}
          className="absolute top-4 right-4 text-white hover:text-white/70 transition-colors z-10"
          aria-label="Close"
        >
          <X size={20} />
        </button>

        {/* Main Heading */}
        <h2 className="text-2xl font-semibold text-white mb-1">
          Suggested budget: ${suggestedBudget.toLocaleString('en-US', { maximumFractionDigits: 0 })}
        </h2>

        {/* Timeframe Label */}
        <p className="text-xs uppercase tracking-wider text-white/60 mb-4">
          FOR {budget.month ? budget.month.toUpperCase() : 'NEXT MONTH'}
        </p>

        {/* Budget Slider */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-white/90">Set Your Budget</label>
            <span className="text-2xl font-bold text-white">
              ${clampedValue.toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </span>
          </div>
          
          <div className="flex items-center justify-between text-xs text-white/60 mb-4">
            <span>Min: ${minBudget.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
            <span>AI: ${suggestedBudget.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
            <span>Max: ${maxBudget.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
          </div>
          
          <input
            type="range"
            min={minBudget}
            max={maxBudget}
            step={100}
            value={clampedValue}
            onChange={handleSliderChange}
            className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
            style={{
              background: maxBudget > minBudget 
                ? `linear-gradient(to right, #10B981 0%, #10B981 ${((clampedValue - minBudget) / (maxBudget - minBudget)) * 100}%, rgba(255,255,255,0.2) ${((clampedValue - minBudget) / (maxBudget - minBudget)) * 100}%, rgba(255,255,255,0.2) 100%)`
                : 'rgba(255,255,255,0.2)'
            }}
          />
          
          <button
            onClick={handleSaveBudget}
            disabled={isSaving}
            className="mt-4 flex items-center gap-2 px-4 py-2 bg-green-500 text-white text-sm font-medium rounded-md hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed mx-auto"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save Budget'}
          </button>
        </div>

        {/* Chart */}
        {chartData.length > 0 && (
          <div className="mb-6">
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }}
                  stroke="rgba(255,255,255,0.3)"
                />
                <YAxis 
                  tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
                  stroke="rgba(255,255,255,0.3)"
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                  formatter={(value: number, name: string) => [
                    `$${value.toFixed(2)}`,
                    name === 'spending' ? 'Spending' : name === 'income' ? 'Income' : 'Budget'
                  ]}
                />
                <Bar dataKey="spending" fill="#EF4444" radius={[4, 4, 0, 0]} name="Spending" />
                <Bar dataKey="income" fill="#10B981" radius={[4, 4, 0, 0]} name="Income" />
                <ReferenceLine 
                  y={budget.total_budget} 
                  stroke="#FFFFFF" 
                  strokeDasharray="5 5" 
                  strokeWidth={2}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Summary Text */}
        {budget.rationale && (
          <p className="text-white/90 text-sm leading-relaxed">
            {budget.rationale}
          </p>
        )}
      </div>
    </div>
  )
}
