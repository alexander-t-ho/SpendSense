import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchSuggestedBudget, fetchBudgetTracking, generateRAGBudget } from '../services/api'
import { Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Legend, ReferenceLine } from 'recharts'
import { useState, useEffect } from 'react'
import { X, Save } from 'lucide-react'

interface SuggestedBudgetCardProps {
  userId: string
  month?: string
  lookbackMonths?: number
  isAdmin?: boolean // If true, show read-only view with deviation
}

export default function SuggestedBudgetCard({ userId, month, lookbackMonths = 6, isAdmin = false }: SuggestedBudgetCardProps) {
  const [isClosed, setIsClosed] = useState(false)
  const queryClient = useQueryClient()
  const { data: budget, isLoading, error, refetch } = useQuery({
    queryKey: ['suggestedBudget', userId, month, lookbackMonths],
    queryFn: () => fetchSuggestedBudget(userId, month, lookbackMonths),
    enabled: !!userId && !isClosed,
  })
  
  // Fetch current budget for admin view and tracking data
  const { data: currentBudget } = useQuery({
    queryKey: ['budgetTracking', userId, month || new Date().toISOString().slice(0, 7)],
    queryFn: () => fetchBudgetTracking(userId, month || new Date().toISOString().slice(0, 7)),
    enabled: !!userId && !isClosed,
  })

  // Auto-generate RAG budget on mount if no budget exists (only for non-admin users)
  const generateBudgetMutation = useMutation({
    mutationFn: () => generateRAGBudget(userId, month || new Date().toISOString().slice(0, 7)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suggestedBudget', userId] })
      queryClient.invalidateQueries({ queryKey: ['budgetTracking', userId] })
      refetch()
    },
  })

  // Check if we need to generate a budget (only once on mount)
  useEffect(() => {
    if (userId && !isAdmin && !budget && !generateBudgetMutation.isPending && !generateBudgetMutation.isSuccess && !isLoading) {
      // Generate budget if not exists (wait a bit for initial query to complete)
      const timer = setTimeout(() => {
        if (!budget) {
          generateBudgetMutation.mutate()
        }
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [userId, budget, isAdmin, isLoading])
  
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
  
  // Calculate deviation for admin view
  const userSetBudget = currentBudget?.total_budget || 0
  const deviation = userSetBudget > 0 ? userSetBudget - suggestedBudget : 0
  const deviationPercent = suggestedBudget > 0 ? (deviation / suggestedBudget) * 100 : 0
  
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
      <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
        <div className="text-[#5D4037]">Loading budget suggestion...</div>
      </div>
    )
  }

  if (error || !budget) {
    return (
      <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
        <div className="text-red-600">Failed to load budget suggestion</div>
      </div>
    )
  }

  // Show only spending vs budget, not income
  const chartData = (budget.history || []).map((month: any) => ({
    month: new Date(month.month + '-01').toLocaleDateString('en-US', { month: 'short' }),
    spending: Math.abs(month.total_spending || 0),
    budget: budget.total_budget || 0,
  }))

  return (
    <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-4xl font-serif text-[#5D4037] mb-2">Suggested Monthly Budget</h1>
        <p className="text-[#556B2F]/80 text-sm">
          AI-powered budget recommendations based on your spending patterns.
        </p>
      </div>

      {/* Main Card */}
      <div className="relative bg-white/90 backdrop-blur-md rounded-xl border border-[#D4C4B0]/50 p-6 shadow-xl">
        {/* Close Button */}
        <button
          onClick={() => setIsClosed(true)}
          className="absolute top-4 right-4 text-[#5D4037] hover:text-[#556B2F] transition-colors z-10"
          aria-label="Close"
        >
          <X size={20} />
        </button>

        {/* Main Heading */}
        <h2 className="text-2xl font-semibold text-[#5D4037] mb-1">
          Suggested budget: ${suggestedBudget.toLocaleString('en-US', { maximumFractionDigits: 0 })}
        </h2>

        {/* Timeframe Label */}
        <p className="text-xs uppercase tracking-wider text-[#556B2F]/60 mb-4">
          FOR {budget.month ? budget.month.toUpperCase() : 'NEXT MONTH'}
        </p>

        {/* Admin View - Show Deviation */}
        {isAdmin && (
          <div className="mb-6 p-4 bg-[#E8F5E9] rounded-lg border border-[#C8E6C9]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-[#556B2F]">Recommended Amount:</span>
              <span className="text-lg font-bold text-[#5D4037]">
                ${suggestedBudget.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </span>
            </div>
            {userSetBudget > 0 ? (
              <>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-[#556B2F]">User Set Budget:</span>
                  <span className="text-lg font-bold text-[#5D4037]">
                    ${userSetBudget.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-[#556B2F]">Deviation:</span>
                  <span className={`text-lg font-bold ${deviation >= 0 ? 'text-[#556B2F]' : 'text-red-600'}`}>
                    {deviation >= 0 ? '+' : ''}${deviation.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                    {' '}({deviationPercent >= 0 ? '+' : ''}{deviationPercent.toFixed(1)}%)
                  </span>
                </div>
              </>
            ) : (
              <p className="text-sm text-[#8B6F47]">User has not set a budget yet.</p>
            )}
          </div>
        )}

        {/* Budget Slider - Only for non-admin */}
        {!isAdmin && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-[#5D4037]">Set Your Budget</label>
              <span className="text-2xl font-bold text-[#5D4037]">
                ${clampedValue.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </span>
            </div>
            
            <div className="flex items-center justify-between text-xs text-[#556B2F] mb-4">
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
              className="w-full h-2 bg-[#D4C4B0] rounded-lg appearance-none cursor-pointer"
              style={{
                background: maxBudget > minBudget 
                  ? `linear-gradient(to right, #556B2F 0%, #556B2F ${((clampedValue - minBudget) / (maxBudget - minBudget)) * 100}%, rgba(212,196,176,0.3) ${((clampedValue - minBudget) / (maxBudget - minBudget)) * 100}%, rgba(212,196,176,0.3) 100%)`
                  : 'rgba(212,196,176,0.3)'
              }}
            />
            
            <button
              onClick={handleSaveBudget}
              disabled={isSaving}
              className="mt-4 flex items-center gap-2 px-4 py-2 bg-[#556B2F] text-white text-sm font-medium rounded-md hover:bg-[#6B7A3C] transition-colors disabled:opacity-50 disabled:cursor-not-allowed mx-auto"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save Budget'}
            </button>
          </div>
        )}

        {/* Chart */}
        {chartData.length > 0 && (
          <div className="mb-6">
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(93,64,55,0.1)" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fill: '#5D4037', fontSize: 12 }}
                  stroke="#5D4037"
                />
                <YAxis 
                  tick={{ fill: '#5D4037', fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
                  stroke="#5D4037"
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(245, 230, 211, 0.95)', 
                    border: '1px solid #5D4037',
                    borderRadius: '8px',
                    color: '#5D4037'
                  }}
                  formatter={(value: number, name: string) => [
                    `$${value.toFixed(2)}`,
                    name === 'spending' ? 'Actual Spending' : 'Budget'
                  ]}
                />
                <Legend 
                  wrapperStyle={{ color: '#5D4037', paddingTop: '10px' }}
                />
                <ReferenceLine 
                  y={budget.total_budget || 0} 
                  stroke="#8B6F47" 
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  label={{ 
                    value: `Budget $${(budget.total_budget || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}`, 
                    position: "insideTopRight", 
                    fill: "#8B6F47", 
                    fontSize: 11,
                    fontWeight: 'bold'
                  }}
                />
                <Bar dataKey="spending" fill="#5D4037" radius={[4, 4, 0, 0]} name="Actual Spending" />
                <Bar dataKey="budget" fill="#556B2F" radius={[4, 4, 0, 0]} name="Budget" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Summary Text */}
        {budget.rationale && (
          <div className="space-y-3">
            <p className="text-[#5D4037]/90 text-sm leading-relaxed">
              {budget.rationale}
            </p>
            {budget.category_budgets && budget.category_budgets['Debt Repayment'] && (
              <div className="bg-[#E8F5E9] border-2 border-[#556B2F] rounded-lg p-3">
                <p className="text-sm text-[#556B2F] font-medium">
                  💡 See Admin's recommendations for detailed debt payoff timeline and strategies.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
