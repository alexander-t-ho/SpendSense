import { useQuery } from '@tanstack/react-query'
import { fetchSpendingAnalysis } from '../services/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { TrendingUp, AlertCircle, DollarSign, Calendar } from 'lucide-react'

interface SpendingAnalysisCardProps {
  userId: string
  months?: number
}

export default function SpendingAnalysisCard({ userId, months = 6 }: SpendingAnalysisCardProps) {
  const { data: analysis, isLoading, error } = useQuery({
    queryKey: ['spendingAnalysis', userId, months],
    queryFn: () => fetchSpendingAnalysis(userId, months),
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

  if (error || !analysis) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <p className="text-red-500">Failed to load spending analysis</p>
      </div>
    )
  }

  const chartData = analysis.monthly_breakdown?.map((month: any) => ({
    month: new Date(month.month).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
    spending: Math.abs(month.total_spending || 0),
    income: month.total_income || 0,
  })) || []

  const topInsights = analysis.insights?.slice(0, 3) || []

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <TrendingUp className="h-5 w-5 text-green-500" />
          <h3 className="text-lg font-semibold text-gray-900">6-Month Spending Analysis</h3>
        </div>
        <div className="text-sm text-gray-500">
          {months} months
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-red-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-1">
            <DollarSign className="h-4 w-4 text-red-600" />
            <span className="text-sm text-gray-600">Total Spending</span>
          </div>
          <p className="text-2xl font-bold text-red-900">
            ${Math.abs(analysis.total_spending || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </p>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-1">
            <DollarSign className="h-4 w-4 text-green-600" />
            <span className="text-sm text-gray-600">Avg Monthly</span>
          </div>
          <p className="text-2xl font-bold text-green-900">
            ${Math.abs(analysis.average_monthly_spending || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </p>
        </div>

        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-1">
            <Calendar className="h-4 w-4 text-blue-600" />
            <span className="text-sm text-gray-600">Income Stability</span>
          </div>
          <p className="text-lg font-semibold text-blue-900">
            {analysis.income_stability?.stability_level || 'Unknown'}
          </p>
        </div>
      </div>

      {/* Monthly Trend Chart */}
      {chartData.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Monthly Spending vs Income</h4>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="month" 
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`}
              />
              <Tooltip 
                formatter={(value: number, name: string) => [
                  `$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`,
                  name === 'spending' ? 'Spending' : 'Income'
                ]}
                labelStyle={{ color: '#374151' }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="spending" 
                stroke="#EF4444" 
                strokeWidth={2}
                name="Spending"
                dot={{ r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="income" 
                stroke="#10B981" 
                strokeWidth={2}
                name="Income"
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Key Insights */}
      {topInsights.length > 0 && (
        <div className="border-t pt-4">
          <div className="flex items-center space-x-2 mb-3">
            <AlertCircle className="h-4 w-4 text-amber-500" />
            <h4 className="text-sm font-medium text-gray-700">Key Insights</h4>
          </div>
          <ul className="space-y-2">
            {topInsights.map((insight: string, index: number) => (
              <li key={index} className="text-sm text-gray-600 flex items-start">
                <span className="text-amber-500 mr-2">•</span>
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}


