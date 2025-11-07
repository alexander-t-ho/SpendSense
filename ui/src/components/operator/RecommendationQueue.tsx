import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, Flag, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import {
  fetchRecommendationQueue,
  approveRecommendation,
  flagRecommendation,
  rejectRecommendation,
  OperatorRecommendation,
} from '../../services/operatorApi'
import { fetchUsers } from '../../services/api'
import UserSearch from './UserSearch'
import { RecommendationWebSocket, RecommendationUpdate } from '../../services/recommendationWebSocket'

export default function RecommendationQueue() {
  const [statusFilter, setStatusFilter] = useState<'pending' | 'approved' | 'flagged' | 'rejected' | 'all'>('pending')
  const [selectedUserId, setSelectedUserId] = useState<string>('')
  const queryClient = useQueryClient()
  const wsRef = useRef<RecommendationWebSocket | null>(null)

  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers,
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['operator-recommendations', statusFilter, selectedUserId],
    queryFn: () => fetchRecommendationQueue(statusFilter, selectedUserId || undefined),
  })

  // Set up WebSocket for real-time updates
  useEffect(() => {
    const handleUpdate = (update: RecommendationUpdate) => {
      console.log('Real-time recommendation update received:', update)
      
      // Remove the recommendation from the current query cache if it's in pending status
      // and the action would move it out of pending
      if (statusFilter === 'pending' && 
          (update.action === 'approved' || update.action === 'rejected' || update.action === 'flagged')) {
        queryClient.setQueryData(
          ['operator-recommendations', statusFilter, selectedUserId],
          (oldData: any) => {
            if (!oldData) return oldData
            return {
              ...oldData,
              recommendations: oldData.recommendations.filter(
                (rec: OperatorRecommendation) => rec.id !== update.recommendation_id
              ),
              total: oldData.recommendations.filter(
                (rec: OperatorRecommendation) => rec.id !== update.recommendation_id
              ).length,
            }
          }
        )
      } else {
        // For other statuses, invalidate the query to refetch
        queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
      }
    }

    wsRef.current = new RecommendationWebSocket(handleUpdate)
    wsRef.current.connect()

    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect()
      }
    }
  }, [statusFilter, selectedUserId, queryClient])

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
        <div className="text-[#8B6F47]">Loading recommendations...</div>
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
      <div className="px-6 py-4 border-b border-[#D4C4B0]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-[#5D4037]">Recommendation Queue</h2>
            <p className="text-sm text-[#556B2F] mt-1">
              Review and approve or flag recommendations before they're shown to users
            </p>
          </div>
        </div>
        
        {/* User Search */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-[#556B2F] mb-2">
            Filter by User (Optional)
          </label>
          <UserSearch
            users={users || []}
            selectedUserId={selectedUserId}
            onSelectUser={setSelectedUserId}
            placeholder="Search for a user to filter recommendations..."
            className="max-w-md"
          />
        </div>

        {/* Status Filters */}
        <div className="flex gap-2">
            <button
              onClick={() => setStatusFilter('pending')}
              className={`px-4 py-2 text-sm rounded-md ${
                statusFilter === 'pending'
                  ? 'bg-blue-600 text-white'
                  : 'bg-[#F5E6D3] text-[#556B2F] hover:bg-gray-200'
              }`}
            >
              Pending
            </button>
            <button
              onClick={() => setStatusFilter('approved')}
              className={`px-4 py-2 text-sm rounded-md ${
                statusFilter === 'approved'
                  ? 'bg-green-600 text-white'
                  : 'bg-[#F5E6D3] text-[#556B2F] hover:bg-gray-200'
              }`}
            >
              Approved
            </button>
            <button
              onClick={() => setStatusFilter('flagged')}
              className={`px-4 py-2 text-sm rounded-md ${
                statusFilter === 'flagged'
                  ? 'bg-red-600 text-white'
                  : 'bg-[#F5E6D3] text-[#556B2F] hover:bg-gray-200'
              }`}
            >
              Flagged
            </button>
            <button
              onClick={() => setStatusFilter('rejected')}
              className={`px-4 py-2 text-sm rounded-md ${
                statusFilter === 'rejected'
                  ? 'bg-orange-600 text-white'
                  : 'bg-[#F5E6D3] text-[#556B2F] hover:bg-gray-200'
              }`}
            >
              Rejected
            </button>
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-4 py-2 text-sm rounded-md ${
                statusFilter === 'all'
                  ? 'bg-gray-800 text-white'
                  : 'bg-[#F5E6D3] text-[#556B2F] hover:bg-gray-200'
              }`}
            >
              All
            </button>
          </div>
        </div>

      {recommendations.length === 0 ? (
        <div className="px-6 py-12 text-center text-[#8B6F47]">
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
  const [isExpanded, setIsExpanded] = useState(false)
  
  const getRiskColor = (risk: string | undefined) => {
    if (!risk) return 'bg-[#F5E6D3] text-[#5D4037]'
    switch (risk.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800'
      case 'HIGH':
        return 'bg-orange-100 text-orange-800'
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800'
      case 'LOW':
        return 'bg-[#E8F5E9] text-[#5D4037]'
      case 'MINIMAL':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-[#F5E6D3] text-[#5D4037]'
    }
  }

  return (
    <div className="px-6 py-4 hover:bg-[#E8F5E9]">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-2 text-left hover:text-[#556B2F] transition-colors"
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 text-[#556B2F]" />
              ) : (
                <ChevronDown className="h-4 w-4 text-[#556B2F]" />
              )}
              <h3 className="text-lg font-medium text-[#5D4037]">{recommendation.title}</h3>
            </button>
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
                'bg-[#F5E6D3] text-[#5D4037]'
              }`}>
                {recommendation.priority.toUpperCase()} Priority
              </span>
            )}
          </div>
          <div className="mt-2 text-sm text-[#556B2F]">
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
          </div>
          
          {/* Expanded content */}
          {isExpanded && (
            <div className="mt-4 space-y-3">
              {recommendation.description && (
                <div className="p-3 bg-[#E8F5E9] rounded-md">
                  <p className="text-sm font-medium text-[#5D4037] mb-1">Recommendation:</p>
                  <p className="text-sm text-[#556B2F]">{recommendation.description}</p>
                </div>
              )}
              {recommendation.action_items && recommendation.action_items.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-[#5D4037] mb-1">Action Items:</p>
                  <ul className="list-disc list-inside text-sm text-[#556B2F] space-y-1">
                    {recommendation.action_items.map((item: string, idx: number) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {recommendation.expected_impact && (
                <div className="p-2 bg-green-50 rounded-md">
                  <p className="text-xs font-medium text-green-900">Expected Impact:</p>
                  <p className="text-xs text-green-800 mt-1">{recommendation.expected_impact}</p>
                </div>
              )}
              {recommendation.rationale && (
                <div className="p-3 bg-blue-50 rounded-md">
                  <p className="text-sm font-medium text-blue-900">Rationale:</p>
                  <p className="text-sm text-[#5D4037] mt-1">{recommendation.rationale}</p>
                </div>
              )}
            </div>
          )}
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

