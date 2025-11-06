import { useQuery } from '@tanstack/react-query'
import { fetchSpendingAnalysis } from '../services/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { TrendingUp, DollarSign, Calendar } from 'lucide-react'
import FinancialTrackingFeatureTemplate, { KeyMetric } from './FinancialTrackingFeatureTemplate'

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

  if (isLoading || error || !analysis) {
    return (
      <FinancialTrackingFeatureTemplate
        title="6-Month Spending Analysis"
        icon={TrendingUp}
        iconColor="green"
        isLoading={isLoading}
        error={error ? 'Failed to load spending analysis' : null}
      />
    )
  }

  const chartData = analysis.monthly_breakdown?.map((month: any) => ({
    month: new Date(month.month).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
    spending: Math.abs(month.total_spending || 0),
    income: month.total_income || 0,
  })) || []

  const topInsights = analysis.insights?.slice(0, 3) || []

  const keyMetrics: KeyMetric[] = [
    {
      label: 'Total Spending',
      value: `$${Math.abs(analysis.total_spending || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}`,
      color: 'red',
      icon: DollarSign,
    },
    {
      label: 'Avg Monthly',
      value: `$${Math.abs(analysis.average_monthly_spending || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}`,
      color: 'green',
      icon: DollarSign,
    },
    {
      label: 'Income Stability',
      value: analysis.income_stability?.stability_level || 'Unknown',
      color: 'blue',
      icon: Calendar,
    },
  ]

  return (
    <FinancialTrackingFeatureTemplate
      title="6-Month Spending Analysis"
      icon={TrendingUp}
      iconColor="green"
      period={`${months} months`}
      keyMetrics={keyMetrics}
      visualizations={
        chartData.length > 0 ? (
          <div>
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
        ) : null
      }
      insights={topInsights}
    />
  )
}

