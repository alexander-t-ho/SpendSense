import { useQuery } from '@tanstack/react-query'
import { fetchSuggestedBudget } from '../services/api'
import { Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, ReferenceLine } from 'recharts'
import { Target } from 'lucide-react'

interface SuggestedBudgetCardProps {
  userId: string
  month?: string
  lookbackMonths?: number
}

export default function SuggestedBudgetCard({ userId, month, lookbackMonths = 6 }: SuggestedBudgetCardProps) {
  const { data: budget, isLoading, error } = useQuery({
    queryKey: ['suggestedBudget', userId, month, lookbackMonths],
    queryFn: () => fetchSuggestedBudget(userId, month, lookbackMonths),
    enabled: !!userId,
  })

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error || !budget) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <p className="text-red-500">Failed to load budget suggestion</p>
      </div>
    )
  }

  // Prepare chart data from budget history if available
  const chartData = (budget.history || []).map((month: any) => ({
    month: new Date(month.month + '-01').toLocaleDateString('en-US', { month: 'short' }),
    spending: month.total_spending || 0,
    income: month.total_income || 0,
  }))

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Target className="h-5 w-5 text-green-500" />
          <h3 className="text-lg font-semibold text-gray-900">Suggested Monthly Budget</h3>
        </div>
        <div className="text-sm text-gray-500">
          For {budget.month || 'next month'}
        </div>
      </div>

      {/* Suggested Budget Amount */}
      <div className="bg-green-50 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 mb-1">Suggested Budget</p>
            <p className="text-4xl font-bold text-green-600">
              ${budget.total_budget?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Based on</p>
            <p className="text-lg font-semibold text-gray-900">{lookbackMonths} months</p>
            <p className="text-sm text-gray-600">of history</p>
          </div>
        </div>
      </div>

      {/* Rationale */}
      {budget.rationale && (
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded mb-6">
          <p className="text-sm text-gray-700">
            <span className="font-medium">Why this budget:</span> {budget.rationale}
          </p>
        </div>
      )}

      {/* Budget Breakdown */}
      {budget.income_based && budget.expense_based && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Income-Based</p>
            <p className="text-xl font-semibold text-gray-900">
              ${budget.income_based?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Expense-Based</p>
            <p className="text-xl font-semibold text-gray-900">
              ${budget.expense_based?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
            </p>
          </div>
        </div>
      )}

      {/* Historical Spending Chart */}
      {chartData.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Historical Spending vs. Budget</h4>
          <ResponsiveContainer width="100%" height={250}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="month" 
                tick={{ fontSize: 12 }}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `$${value.toFixed(0)}`}
              />
              <Tooltip 
                formatter={(value: number, name: string) => [
                  `$${value.toFixed(2)}`,
                  name === 'spending' ? 'Spending' : name === 'income' ? 'Income' : 'Budget'
                ]}
                labelStyle={{ color: '#374151' }}
              />
              <Bar dataKey="spending" fill="#EF4444" radius={[4, 4, 0, 0]} name="Spending" />
              <Bar dataKey="income" fill="#10B981" radius={[4, 4, 0, 0]} name="Income" />
              <ReferenceLine 
                y={budget.total_budget} 
                stroke="#3B82F6" 
                strokeDasharray="5 5" 
                label={{ value: 'Budget', position: 'right' }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Category Breakdown */}
      {budget.category_budgets && Object.keys(budget.category_budgets).length > 0 && (
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Budget by Category</h4>
          <div className="space-y-2">
            {Object.entries(budget.category_budgets)
              .sort((a, b) => (b[1] as number) - (a[1] as number))
              .slice(0, 5)
              .map(([category, amount]) => (
                <div key={category} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">{category.replace('_', ' ')}</span>
                  <span className="text-sm font-semibold text-gray-900">
                    ${(amount as number).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

