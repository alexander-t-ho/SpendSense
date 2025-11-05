import { useQuery } from '@tanstack/react-query'
import { fetchEvaluationMetrics } from '../services/api'
import { CheckCircle, XCircle, TrendingUp, Clock, Users, BarChart3, Target } from 'lucide-react'
import { useState } from 'react'

interface EvaluationMetricsProps {
  latencySampleSize?: number
}

export default function EvaluationMetrics({ latencySampleSize }: EvaluationMetricsProps) {
  const [isRefreshing, setIsRefreshing] = useState(false)
  
  const { data: metrics, isLoading, error, refetch } = useQuery({
    queryKey: ['evaluationMetrics', latencySampleSize],
    queryFn: () => fetchEvaluationMetrics(latencySampleSize),
    refetchOnWindowFocus: false,
  })

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await refetch()
    setIsRefreshing(false)
  }

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-red-500">
          <p className="font-semibold">Error loading evaluation metrics</p>
          <p className="text-sm mt-2">{error instanceof Error ? error.message : 'Unknown error'}</p>
        </div>
      </div>
    )
  }

  if (!metrics) {
    return null
  }

  const getStatusIcon = (passed: boolean) => {
    return passed ? (
      <CheckCircle className="h-5 w-5 text-green-500" />
    ) : (
      <XCircle className="h-5 w-5 text-red-500" />
    )
  }

  const getStatusColor = (passed: boolean) => {
    return passed ? 'text-green-600' : 'text-red-600'
  }

  const targetsMet = Object.values(metrics.targets_met || {}).filter(Boolean).length
  const totalTargets = Object.keys(metrics.targets_met || {}).length

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">System Evaluation Metrics</h2>
          <p className="text-sm text-gray-500 mt-1">
            Phase 8: Evaluation & Metrics Dashboard
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
        >
          <span>{isRefreshing ? 'Refreshing...' : 'Refresh Metrics'}</span>
        </button>
      </div>

      {/* Overall Score */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Overall Score</p>
            <p className="text-4xl font-bold text-gray-900 mt-2">
              {metrics.overall_score ? (metrics.overall_score * 100).toFixed(1) : '0.0'}%
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Targets Met: {targetsMet} / {totalTargets}
            </p>
          </div>
          <Target className="h-16 w-16 text-blue-500 opacity-50" />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Coverage Metric */}
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5 text-blue-500" />
              <h3 className="font-semibold text-gray-900">Coverage</h3>
            </div>
            {getStatusIcon(metrics.targets_met?.coverage_100_pct || false)}
          </div>
          <div className="space-y-2">
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold text-gray-900">
                {metrics.coverage?.coverage_percentage || 0}%
              </span>
              <span className="text-sm text-gray-500">of users</span>
            </div>
            <p className="text-xs text-gray-500">
              Target: 100% (users with persona + ≥3 behaviors)
            </p>
            <div className="text-xs text-gray-600 mt-2">
              <p>• {metrics.coverage?.users_with_persona || 0} users with persona</p>
              <p>• {metrics.coverage?.users_with_3plus_behaviors || 0} users with ≥3 behaviors</p>
              <p>• {metrics.coverage?.users_with_persona_and_3plus_behaviors || 0} meeting coverage</p>
            </div>
          </div>
        </div>

        {/* Explainability Metric */}
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-green-500" />
              <h3 className="font-semibold text-gray-900">Explainability</h3>
            </div>
            {getStatusIcon(metrics.targets_met?.explainability_100_pct || false)}
          </div>
          <div className="space-y-2">
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold text-gray-900">
                {metrics.explainability?.explainability_percentage || 0}%
              </span>
              <span className="text-sm text-gray-500">with rationales</span>
            </div>
            <p className="text-xs text-gray-500">
              Target: 100% (recommendations with plain-language rationales)
            </p>
            <div className="text-xs text-gray-600 mt-2">
              <p>• {metrics.explainability?.total_recommendations || 0} total recommendations</p>
              <p>• {metrics.explainability?.recommendations_with_rationales || 0} with rationales</p>
            </div>
          </div>
        </div>

        {/* Relevance Metric */}
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-purple-500" />
              <h3 className="font-semibold text-gray-900">Relevance</h3>
            </div>
            {getStatusIcon(metrics.targets_met?.relevance_high || false)}
          </div>
          <div className="space-y-2">
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold text-gray-900">
                {metrics.relevance?.relevance_percentage || 0}%
              </span>
              <span className="text-sm text-gray-500">persona fit</span>
            </div>
            <p className="text-xs text-gray-500">
              Target: ≥80% (education-persona fit scoring)
            </p>
            <div className="text-xs text-gray-600 mt-2">
              <p>• {metrics.relevance?.total_recommendations || 0} total recommendations</p>
              <p>• {metrics.relevance?.relevant_recommendations || 0} relevant to persona</p>
            </div>
          </div>
        </div>

        {/* Latency Metric */}
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-orange-500" />
              <h3 className="font-semibold text-gray-900">Latency</h3>
            </div>
            {getStatusIcon(metrics.targets_met?.latency_under_5_s || false)}
          </div>
          <div className="space-y-2">
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold text-gray-900">
                {metrics.latency?.average_latency_seconds?.toFixed(3) || '0.000'}s
              </span>
              <span className="text-sm text-gray-500">average</span>
            </div>
            <p className="text-xs text-gray-500">
              Target: &lt;5 seconds (time to generate recommendations)
            </p>
            <div className="text-xs text-gray-600 mt-2">
              <p>• {metrics.latency?.total_users_tested || 0} users tested</p>
              <p>• Min: {metrics.latency?.min_latency_seconds?.toFixed(3) || '0.000'}s</p>
              <p>• Max: {metrics.latency?.max_latency_seconds?.toFixed(3) || '0.000'}s</p>
            </div>
          </div>
        </div>

        {/* Fairness Metric */}
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-indigo-500" />
              <h3 className="font-semibold text-gray-900">Fairness</h3>
            </div>
            {getStatusIcon(metrics.targets_met?.fairness_good || false)}
          </div>
          <div className="space-y-2">
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold text-gray-900">
                {metrics.fairness?.fairness_score?.toFixed(3) || '0.000'}
              </span>
            </div>
            <p className="text-xs text-gray-500">
              Target: ≥0.7 (demographic parity in persona distribution)
            </p>
            <p className="text-xs font-medium text-gray-700 mt-2">
              {metrics.fairness?.interpretation || 'N/A'}
            </p>
            {metrics.fairness?.persona_distribution && (
              <div className="text-xs text-gray-600 mt-2 space-y-1">
                {Object.entries(metrics.fairness.persona_distribution).map(([persona, count]: [string, any]) => (
                  <p key={persona}>
                    • {persona}: {count.count} users ({count.percentage}%)
                  </p>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Timestamp */}
      {metrics.timestamp && (
        <div className="mt-6 text-xs text-gray-500 text-center">
          Last updated: {new Date(metrics.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  )
}

