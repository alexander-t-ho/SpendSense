import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchSuggestedBudget, fetchBudgetTracking, generateRAGBudget } from '../services/api'
import { Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Legend, ReferenceLine } from 'recharts'
import { useEffect, useState } from 'react'
import { Save, Pencil } from 'lucide-react'

interface SuggestedBudgetCardProps {
  userId: string
  month?: string
  lookbackMonths?: number
  isAdmin?: boolean // If true, show read-only view with deviation
}

export default function SuggestedBudgetCard({ userId, month, lookbackMonths = 6, isAdmin = false }: SuggestedBudgetCardProps) {
  const queryClient = useQueryClient()
  const { data: budget, isLoading, error, refetch } = useQuery({
    queryKey: ['suggestedBudget', userId, month, lookbackMonths],
    queryFn: () => fetchSuggestedBudget(userId, month, lookbackMonths),
    enabled: !!userId,
  })
  
  // Fetch current budget for admin view and tracking data
  const { data: budgetTracking } = useQuery({
    queryKey: ['budgetTracking', userId, month || new Date().toISOString().slice(0, 7)],
    queryFn: () => fetchBudgetTracking(userId, month || new Date().toISOString().slice(0, 7)),
    enabled: !!userId,
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
  
  const [isEditing, setIsEditing] = useState(false)
  const [editAmount, setEditAmount] = useState<number>(0)
  const [isSaving, setIsSaving] = useState(false)
  
  useEffect(() => {
    if (budget?.total_budget) {
      setEditAmount(budget.total_budget)
    }
  }, [budget])
  
  const suggestedBudget = budget?.total_budget || 0
  const userSetBudgetAmount = budgetTracking?.total_budget || suggestedBudget
  
  // Calculate deviation for admin view
  const userSetBudget = budgetTracking?.total_budget || 0
  const deviation = userSetBudget > 0 ? userSetBudget - suggestedBudget : 0
  const deviationPercent = suggestedBudget > 0 ? (deviation / suggestedBudget) * 100 : 0
  
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  
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
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to save budget' }))
        // Handle structured error response
        if (errorData.detail && typeof errorData.detail === 'object') {
          const errorMsg = errorData.detail.error || 'Failed to save budget'
          const detailMsg = errorData.detail.message || ''
          throw new Error(`${errorMsg}. ${detailMsg}`)
        }
        throw new Error(errorData.detail || 'Failed to save budget')
      }
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suggestedBudget', userId] })
      queryClient.invalidateQueries({ queryKey: ['budgetTracking', userId] })
      setIsSaving(false)
      setIsEditing(false) // Exit edit mode on success
      setErrorMessage(null) // Clear any previous errors
    },
    onError: (error: Error) => {
      setIsSaving(false)
      setErrorMessage(error.message)
    },
  })
  
  const handleSaveBudget = () => {
    setIsSaving(true)
    saveBudgetMutation.mutate(editAmount)
  }
  
  const handleEditClick = () => {
    setIsEditing(true)
    setEditAmount(userSetBudgetAmount)
    setErrorMessage(null)
  }
  
  const handleCancelEdit = () => {
    setIsEditing(false)
    setEditAmount(userSetBudgetAmount)
    setErrorMessage(null)
  }
  
  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEditAmount(parseFloat(e.target.value) || 0)
    setErrorMessage(null) // Clear error when user adjusts input
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
        {/* Main Heading with Edit Button */}
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-2xl font-semibold text-[#5D4037]">
            Suggested budget: ${suggestedBudget.toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </h2>
          {!isAdmin && !isEditing && (
            <button
              onClick={handleEditClick}
              className="p-2 text-[#556B2F] hover:bg-[#E8F5E9] rounded-md transition-colors"
              title="Edit budget"
            >
              <Pencil className="w-5 h-5" />
            </button>
          )}
        </div>

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

        {/* Budget Edit - Only for non-admin */}
        {!isAdmin && isEditing && (
          <div className="mb-6 p-4 bg-[#F5E6D3]/50 rounded-lg border border-[#D4C4B0]">
            <label className="block text-sm font-medium text-[#5D4037] mb-2">
              Set Your Monthly Budget
            </label>
            <div className="flex items-center gap-3">
              <span className="text-[#5D4037] font-medium">$</span>
              <input
                type="number"
                value={editAmount || ''}
                onChange={handleAmountChange}
                className="flex-1 px-3 py-2 border border-[#D4C4B0] rounded-md focus:ring-2 focus:ring-[#556B2F] focus:border-[#556B2F] text-lg font-semibold text-[#5D4037]"
                min="0"
                step="0.01"
                placeholder="Enter budget amount"
              />
            </div>
            
            {errorMessage && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800 font-medium">{errorMessage}</p>
              </div>
            )}
            
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleSaveBudget}
                disabled={isSaving || editAmount <= 0}
                className="flex items-center gap-2 px-4 py-2 bg-[#556B2F] text-white text-sm font-medium rounded-md hover:bg-[#6B7A3C] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-4 h-4" />
                {isSaving ? 'Saving...' : 'Save Budget'}
              </button>
              <button
                onClick={handleCancelEdit}
                disabled={isSaving}
                className="px-4 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-300 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
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
        <div className="space-y-3">
          <p className="text-[#5D4037]/90 text-sm leading-relaxed">
            This budget was based on 80% of your predicted monthly income. We recommend you set 20% of all paychecks towards savings, emergency funds, or paying off debts.
          </p>
          {budget.category_budgets && budget.category_budgets['Debt Repayment'] && (
            <div className="bg-[#E8F5E9] border-2 border-[#556B2F] rounded-lg p-3">
              <p className="text-sm text-[#556B2F] font-medium">
                💡 See Admin's recommendations for detailed debt payoff timeline and strategies.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
