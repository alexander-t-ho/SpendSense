import { useQuery } from '@tanstack/react-query'
import { fetchWeeklyRecap } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Card } from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, Calendar } from 'lucide-react'

interface WeeklyRecapCardProps {
  userId: string
  weekStart?: string
}

export default function WeeklyRecapCard({ userId, weekStart }: WeeklyRecapCardProps) {
  const { data: recap, isLoading, error } = useQuery({
    queryKey: ['weeklyRecap', userId, weekStart],
    queryFn: () => fetchWeeklyRecap(userId, weekStart),
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

  if (error || !recap) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <p className="text-red-500">Failed to load weekly recap</p>
      </div>
    )
  }

  const chartData = recap.daily_spending?.map((day: any) => ({
    day: `Day ${day.day}`,
    date: new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    amount: Math.abs(day.amount),
  })) || []

  const weekOverWeekChange = recap.week_over_week_change || 0
  const isPositive = weekOverWeekChange >= 0

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Calendar className="h-5 w-5 text-blue-500" />
          <h3 className="text-lg font-semibold text-gray-900">Weekly Spending Recap</h3>
        </div>
        <div className="text-sm text-gray-500">
          {new Date(recap.week_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} -{' '}
          {new Date(recap.week_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-1">
            <DollarSign className="h-4 w-4 text-blue-600" />
            <span className="text-sm text-gray-600">Total Spending</span>
          </div>
          <p className="text-2xl font-bold text-blue-900">
            ${Math.abs(recap.total_spending || 0).toFixed(2)}
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-sm text-gray-600">vs. Last Week</span>
          </div>
          <div className="flex items-center space-x-1">
            {isPositive ? (
              <TrendingUp className="h-4 w-4 text-red-500" />
            ) : (
              <TrendingDown className="h-4 w-4 text-green-500" />
            )}
            <p className={`text-2xl font-bold ${isPositive ? 'text-red-600' : 'text-green-600'}`}>
              {Math.abs(weekOverWeekChange).toFixed(1)}%
            </p>
          </div>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-sm text-gray-600">Top Category</span>
          </div>
          <p className="text-lg font-semibold text-purple-900">
            {recap.top_category || 'N/A'}
          </p>
        </div>
      </div>

      {/* Daily Spending Chart */}
      {chartData.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Daily Spending</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `$${value.toFixed(0)}`}
              />
              <Tooltip 
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Spending']}
                labelStyle={{ color: '#374151' }}
              />
              <Bar dataKey="amount" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Insights */}
      {recap.insights && recap.insights.length > 0 && (
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Insights</h4>
          <ul className="space-y-2">
            {recap.insights.map((insight: string, index: number) => (
              <li key={index} className="text-sm text-gray-600 flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

