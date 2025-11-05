import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, Flag, AlertCircle } from 'lucide-react'
import { useState } from 'react'
import {
  fetchRecommendationQueue,
  approveRecommendation,
  flagRecommendation,
  rejectRecommendation,
  OperatorRecommendation,
} from '../../services/operatorApi'

export default function RecommendationQueue() {
  const [statusFilter, setStatusFilter] = useState<'pending' | 'approved' | 'flagged' | 'rejected' | 'all'>('pending')
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['operator-recommendations', statusFilter],
    queryFn: () => fetchRecommendationQueue(statusFilter),
  })

  const approveMutation = useMutation({
    mutationFn: approveRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  const flagMutation = useMutation({
    mutationFn: flagRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: rejectRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-gray-500">Loading recommendations...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-red-600">Error loading recommendations: {(error as Error).message}</div>
      </div>
    )
  }

  const recommendations = data?.recommendations || []

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Recommendation Queue</h2>
            <p className="text-sm text-gray-600 mt-1">
              Review and approve or flag recommendations before they're shown to users
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setStatusFilter('pending')}
              className={`px-4 py-2 text-sm rounded-md ${
                statusFilter === 'pending'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Pending
            </button>
            <button
              onClick={() => setStatusFilter('approved')}
              className={`px-4 py-2 text-sm rounded-md ${
                statusFilter === 'approved'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Approved
            </button>
            <button
              onClick={() => setStatusFilter('flagged')}
              className={`px-4 py-2 text-sm rounded-md ${
                statusFilter === 'flagged'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Flagged
            </button>
            <button
              onClick={() => setStatusFilter('rejected')}
              className={`px-4 py-2 text-sm rounded-md ${
                statusFilter === 'rejected'
                  ? 'bg-orange-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Rejected
            </button>
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-4 py-2 text-sm rounded-md ${
                statusFilter === 'all'
                  ? 'bg-gray-800 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All
            </button>
          </div>
        </div>
      </div>

      {recommendations.length === 0 ? (
        <div className="px-6 py-12 text-center text-gray-500">
          <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p>No recommendations found for status: {statusFilter}</p>
          <p className="text-sm mt-2">
            Recommendations will appear here once they are generated and stored in the system.
          </p>
        </div>
      ) : (
        <div className="divide-y divide-gray-200">
          {recommendations.map((rec: OperatorRecommendation) => (
            <RecommendationCard
              key={rec.id}
              recommendation={rec}
              onApprove={() => approveMutation.mutate(rec.id)}
              onFlag={() => flagMutation.mutate(rec.id)}
              onReject={() => rejectMutation.mutate(rec.id)}
              isApproving={approveMutation.isPending}
              isFlagging={flagMutation.isPending}
              isRejecting={rejectMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function RecommendationCard({
  recommendation,
  onApprove,
  onFlag,
  onReject,
  isApproving,
  isFlagging,
  isRejecting,
}: {
  recommendation: OperatorRecommendation
  onApprove: () => void
  onFlag: () => void
  onReject: () => void
  isApproving: boolean
  isFlagging: boolean
  isRejecting: boolean
}) {
  const getRiskColor = (risk: string | undefined) => {
    if (!risk) return 'bg-gray-100 text-gray-800'
    switch (risk.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800'
      case 'HIGH':
        return 'bg-orange-100 text-orange-800'
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800'
      case 'LOW':
        return 'bg-blue-100 text-blue-800'
      case 'MINIMAL':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="px-6 py-4 hover:bg-gray-50">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h3 className="text-lg font-medium text-gray-900">{recommendation.title}</h3>
            {recommendation.persona_name && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                Persona: {recommendation.persona_name}
              </span>
            )}
            {!recommendation.persona_name && recommendation.persona_id && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                Persona: {recommendation.persona_id}
              </span>
            )}
            {recommendation.persona_info && (
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRiskColor(recommendation.persona_info.risk)}`}>
                {recommendation.persona_info.primary_persona} ({recommendation.persona_info.risk_level})
              </span>
            )}
            {recommendation.approved && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                <CheckCircle className="h-3 w-3 mr-1" />
                Approved
              </span>
            )}
            {recommendation.flagged && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                <Flag className="h-3 w-3 mr-1" />
                Flagged
              </span>
            )}
            {recommendation.rejected && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                <AlertCircle className="h-3 w-3 mr-1" />
                Rejected
              </span>
            )}
            {recommendation.priority && (
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                recommendation.priority === 'high' ? 'bg-red-100 text-red-800' :
                recommendation.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {recommendation.priority.toUpperCase()} Priority
              </span>
            )}
          </div>
          <div className="mt-2 text-sm text-gray-600">
            <p>
              <span className="font-medium">User:</span> {recommendation.user_name} ({recommendation.user_email})
            </p>
            <p className="mt-1">
              <span className="font-medium">Type:</span> {recommendation.recommendation_type}
            </p>
            {(recommendation.persona_name || recommendation.persona_id) && (
              <p className="mt-1">
                <span className="font-medium">Target Persona:</span> {recommendation.persona_name || recommendation.persona_id}
              </p>
            )}
            {recommendation.description && (
              <div className="mt-2 p-3 bg-gray-50 rounded-md">
                <p className="text-sm font-medium text-gray-900 mb-1">Recommendation:</p>
                <p className="text-sm text-gray-700">{recommendation.description}</p>
              </div>
            )}
            {recommendation.action_items && recommendation.action_items.length > 0 && (
              <div className="mt-2">
                <p className="text-sm font-medium text-gray-900 mb-1">Action Items:</p>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {recommendation.action_items.slice(0, 3).map((item: string, idx: number) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {recommendation.expected_impact && (
              <div className="mt-2 p-2 bg-green-50 rounded-md">
                <p className="text-xs font-medium text-green-900">Expected Impact:</p>
                <p className="text-xs text-green-800 mt-1">{recommendation.expected_impact}</p>
              </div>
            )}
          </div>
          <div className="mt-3 p-3 bg-blue-50 rounded-md">
            <p className="text-sm font-medium text-blue-900">Rationale:</p>
            <p className="text-sm text-blue-800 mt-1">{recommendation.rationale}</p>
          </div>
        </div>
        {!recommendation.approved && !recommendation.flagged && !recommendation.rejected && (
          <div className="ml-4 flex gap-2">
            <button
              onClick={onApprove}
              disabled={isApproving || isFlagging || isRejecting}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Approve
            </button>
            <button
              onClick={onReject}
              disabled={isApproving || isFlagging || isRejecting}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <AlertCircle className="h-4 w-4 mr-2" />
              Reject
            </button>
            <button
              onClick={onFlag}
              disabled={isApproving || isFlagging || isRejecting}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Flag className="h-4 w-4 mr-2" />
              Flag
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

