import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchBudgetTracking, generateRAGBudget } from '../services/api'
import { Pencil, Save, X } from 'lucide-react'
import { useState, useEffect } from 'react'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'

interface UserBudgetDisplayProps {
  userId: string
  month?: string
}

export default function UserBudgetDisplay({ userId, month }: UserBudgetDisplayProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editAmount, setEditAmount] = useState<number>(0)
  const queryClient = useQueryClient()

  const { data: tracking, isLoading } = useQuery({
    queryKey: ['budgetTracking', userId, month || new Date().toISOString().slice(0, 7)],
    queryFn: () => fetchBudgetTracking(userId, month || new Date().toISOString().slice(0, 7)),
    enabled: !!userId,
  })

  // Auto-generate budget if none exists
  const generateBudgetMutation = useMutation({
    mutationFn: () => generateRAGBudget(userId, month || new Date().toISOString().slice(0, 7)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgetTracking', userId] })
      queryClient.invalidateQueries({ queryKey: ['suggestedBudget', userId] })
    },
  })

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
        throw new Error(errorData.detail || 'Failed to save budget')
      }
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgetTracking', userId] })
      setIsEditing(false)
    },
    onError: (error: Error) => {
      alert(`Error saving budget: ${error.message}`)
    },
  })

  // Auto-generate budget on mount if none exists
  useEffect(() => {
    if (userId && !isLoading && tracking && !tracking.total_budget) {
      generateBudgetMutation.mutate()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, isLoading, tracking])

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-[#8B6F47]">Loading budget...</div>
      </div>
    )
  }

  const totalBudget = tracking?.total_budget || 0
  const totalSpent = tracking?.total_spent || 0
  const remaining = (tracking?.remaining || 0)
  const percentageUsed = tracking?.percentage_used || 0

  const handleEdit = () => {
    setEditAmount(totalBudget)
    setIsEditing(true)
  }

  const handleSave = () => {
    if (editAmount > 0) {
      saveBudgetMutation.mutate(editAmount)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditAmount(totalBudget)
  }

  return (
    <div className="bg-white shadow rounded-lg p-6 border border-[#D4C4B0]">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-[#5D4037]">Monthly Budget</h2>
        {!isEditing && (
          <button
            onClick={handleEdit}
            className="p-2 text-[#556B2F] hover:text-[#5D4037] hover:bg-[#F5E6D3] rounded-md transition-colors"
            aria-label="Edit budget"
          >
            <Pencil size={18} />
          </button>
        )}
      </div>

      {isEditing ? (
        <div className="space-y-4">
          <div>
            <label htmlFor="budget-amount" className="block text-sm font-medium text-[#556B2F] mb-2">
              Monthly Budget Amount
            </label>
            <input
              id="budget-amount"
              type="number"
              value={editAmount}
              onChange={(e) => setEditAmount(Number(e.target.value))}
              className="w-full px-3 py-2 border border-[#D4C4B0] rounded-md focus:ring-[#556B2F] focus:border-[#556B2F]"
              min="0"
              max={tracking?.max_budget || undefined}
              step="0.01"
            />
            {tracking?.max_budget && (
              <p className="mt-1 text-xs text-[#8B6F47]">
                Maximum budget: ${tracking.max_budget.toLocaleString('en-US', { maximumFractionDigits: 0 })} 
                {tracking.available_balance && ` (20% of liquid assets: $${tracking.available_balance.toLocaleString('en-US', { maximumFractionDigits: 2 })})`}
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saveBudgetMutation.isPending || editAmount <= 0}
              className="flex items-center gap-2 px-4 py-2 bg-[#556B2F] text-white rounded-md hover:bg-[#6B7A3C] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save size={16} />
              Save
            </button>
            <button
              onClick={handleCancel}
              disabled={saveBudgetMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50"
            >
              <X size={16} />
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Circular Budget Dial */}
          <div className="relative flex items-center justify-center py-6">
            <ResponsiveContainer width="100%" height={280}>
              <RadialBarChart
                innerRadius="70%"
                outerRadius="95%"
                data={[
                  {
                    name: 'Spent',
                    value: Math.min(percentageUsed, 100),
                    fill: percentageUsed > 100 ? '#EF4444' : percentageUsed > 80 ? '#8B6F47' : '#556B2F'
                  },
                  {
                    name: 'Remaining',
                    value: Math.max(100 - percentageUsed, 0),
                    fill: '#E5E7EB'
                  }
                ]}
                startAngle={90}
                endAngle={-270}
              >
                <RadialBar dataKey="value" cornerRadius={10} />
              </RadialBarChart>
            </ResponsiveContainer>
            {/* Center Text Overlay */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <p className="text-3xl font-medium text-[#5D4037] mb-1">
                {percentageUsed.toFixed(0)}%
              </p>
              <p className="text-4xl font-bold text-[#5D4037] mb-1">
                ${totalSpent.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
              <p className="text-sm text-[#8B6F47]">
                ${totalBudget.toLocaleString('en-US', { maximumFractionDigits: 0 })} budget
              </p>
            </div>
          </div>

          {/* Summary Metrics */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-[#D4C4B0]">
            <div>
              <p className="text-xs text-[#556B2F] mb-1">Total Budget</p>
              <p className="text-lg font-bold text-[#5D4037]">
                ${totalBudget.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <div>
              <p className="text-xs text-[#556B2F] mb-1">Spent</p>
              <p className="text-lg font-bold text-red-600">
                ${totalSpent.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <div>
              <p className="text-xs text-[#556B2F] mb-1">Remaining</p>
              <p className={`text-lg font-bold ${remaining >= 0 ? 'text-[#556B2F]' : 'text-red-600'}`}>
                ${Math.abs(remaining).toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            </div>
          </div>

          {/* Rationale Text */}
          <p className="text-[#5D4037]/90 text-sm leading-relaxed pt-4 border-t border-[#D4C4B0] mt-4">
            This budget was based on 80% of your predicted monthly income. We recommend you set 20% of all paychecks towards savings, emergency funds, or paying off debts.
          </p>
        </div>
      )}
    </div>
  )
}

