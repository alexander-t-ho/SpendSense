import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronDown, ChevronUp, Clock, Flag, XCircle, CheckCircle, AlertCircle } from 'lucide-react'
import { approveRecommendation, flagRecommendation, rejectRecommendation, OperatorRecommendation } from '../../services/operatorApi'

interface RecommendationsDropdownProps {
  userId: string
}

export default function RecommendationsDropdown({ userId }: RecommendationsDropdownProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [expandedRecs, setExpandedRecs] = useState<Set<string>>(new Set())
  const queryClient = useQueryClient()

  const { data: allRecs, isLoading } = useQuery({
    queryKey: ['all-recommendations-dropdown', userId],
    queryFn: async () => {
      const response = await fetch(`/api/operator/recommendations?status=all&user_id=${userId}&limit=100`)
      if (!response.ok) {
        throw new Error('Failed to fetch recommendations')
      }
      return response.json()
    },
    enabled: !!userId && isExpanded,
    retry: false,
  })

  const approveMutation = useMutation({
    mutationFn: approveRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-recommendations-dropdown', userId] })
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  const flagMutation = useMutation({
    mutationFn: flagRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-recommendations-dropdown', userId] })
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: rejectRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-recommendations-dropdown', userId] })
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  // Filter out approved recommendations (those are shown in main view)
  // Also ensure we only show recommendations for this specific user (backend should filter, but double-check)
  const nonApprovedRecs = (allRecs?.recommendations || [])
    .filter((rec: any) => !rec.approved && rec.user_id === userId) || []

  // Group by status
  const pending = nonApprovedRecs.filter((rec: any) => !rec.approved && !rec.flagged && !rec.rejected)
  const flagged = nonApprovedRecs.filter((rec: any) => rec.flagged)
  const userRejected = nonApprovedRecs.filter((rec: any) => rec.rejected && rec.rejected_by) // User rejected
  const adminRejected = nonApprovedRecs.filter((rec: any) => rec.rejected && !rec.rejected_by) // Admin rejected

  const toggleExpandRec = (recId: string) => {
    setExpandedRecs(prev => {
      const newSet = new Set(prev)
      if (newSet.has(recId)) {
        newSet.delete(recId)
      } else {
        newSet.add(recId)
      }
      return newSet
    })
  }

  const getStatusBadge = (rec: OperatorRecommendation) => {
    if (rec.flagged) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-300">
          <Flag size={12} />
          Flagged
        </span>
      )
    }
    if (rec.rejected && rec.rejected_by) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 border border-orange-300">
          <XCircle size={12} />
          User Rejected
        </span>
      )
    }
    if (rec.rejected) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-300">
          <XCircle size={12} />
          Rejected
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 border border-gray-300">
        <Clock size={12} />
        Pending
      </span>
    )
  }

  const renderRecommendation = (rec: OperatorRecommendation) => {
    const isRecExpanded = expandedRecs.has(rec.id)
    return (
      <div key={rec.id} className="border-b border-gray-200 last:border-b-0">
        <div className="p-4 hover:bg-gray-50">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 flex-wrap mb-2">
                <button
                  onClick={() => toggleExpandRec(rec.id)}
                  className="flex items-center gap-2 text-left hover:text-[#556B2F] transition-colors"
                >
                  {isRecExpanded ? (
                    <ChevronUp className="h-4 w-4 text-[#556B2F]" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-[#556B2F]" />
                  )}
                  <h5 className="text-sm font-medium text-gray-900">{rec.title}</h5>
                </button>
                {getStatusBadge(rec)}
              </div>
              
              {isRecExpanded && (
                <div className="mt-3 space-y-3 pl-6">
                  {rec.description && (
                    <div className="p-3 bg-gray-50 rounded-md">
                      <p className="text-sm text-gray-700">{rec.description}</p>
                    </div>
                  )}
                  {rec.action_items && rec.action_items.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-700 mb-1">Action Items:</p>
                      <ul className="list-disc list-inside text-xs text-gray-600 space-y-1">
                        {rec.action_items.map((item: string, idx: number) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {rec.expected_impact && (
                    <div className="p-2 bg-green-50 rounded-md">
                      <p className="text-xs font-medium text-green-900">Expected Impact:</p>
                      <p className="text-xs text-green-800 mt-1">{rec.expected_impact}</p>
                    </div>
                  )}
                  {rec.rationale && (
                    <div className="p-2 bg-blue-50 rounded-md">
                      <p className="text-xs font-medium text-blue-900">Rationale:</p>
                      <p className="text-xs text-gray-700 mt-1">{rec.rationale}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="ml-4 flex gap-2 flex-shrink-0">
              <button
                onClick={() => approveMutation.mutate(rec.id)}
                disabled={approveMutation.isPending || flagMutation.isPending || rejectMutation.isPending}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Approve"
              >
                <CheckCircle className="h-3 w-3 mr-1" />
                Approve
              </button>
              <button
                onClick={() => rejectMutation.mutate(rec.id)}
                disabled={approveMutation.isPending || flagMutation.isPending || rejectMutation.isPending}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Reject"
              >
                <AlertCircle className="h-3 w-3 mr-1" />
                Reject
              </button>
              <button
                onClick={() => flagMutation.mutate(rec.id)}
                disabled={approveMutation.isPending || flagMutation.isPending || rejectMutation.isPending}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Flag"
              >
                <Flag className="h-3 w-3 mr-1" />
                Flag
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full bg-white shadow rounded-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-gray-100 text-gray-700 rounded-t-lg hover:bg-gray-200 transition-colors text-sm font-medium flex items-center justify-between border-b border-gray-300"
      >
        <span className="flex items-center gap-2">
          <span>Other Recommendations</span>
          {!isExpanded && nonApprovedRecs.length > 0 && (
            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold">
              {nonApprovedRecs.length}
            </span>
          )}
        </span>
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {isExpanded && (
        <div className="max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="p-8 text-sm text-gray-600 text-center">Loading...</div>
          ) : nonApprovedRecs.length === 0 ? (
            <div className="p-8 text-sm text-gray-600 text-center">
              No other recommendations (pending, flagged, or rejected)
            </div>
          ) : (
            <div>
              {pending.length > 0 && (
                <div>
                  <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                      <Clock size={14} />
                      Pending ({pending.length})
                    </h4>
                  </div>
                  {pending.map(renderRecommendation)}
                </div>
              )}

              {flagged.length > 0 && (
                <div>
                  <div className="px-4 py-2 bg-yellow-50 border-b border-yellow-200">
                    <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                      <Flag size={14} />
                      Flagged ({flagged.length})
                    </h4>
                  </div>
                  {flagged.map(renderRecommendation)}
                </div>
              )}

              {userRejected.length > 0 && (
                <div>
                  <div className="px-4 py-2 bg-orange-50 border-b border-orange-200">
                    <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                      <XCircle size={14} />
                      User Rejected ({userRejected.length})
                    </h4>
                  </div>
                  {userRejected.map(renderRecommendation)}
                </div>
              )}

              {adminRejected.length > 0 && (
                <div>
                  <div className="px-4 py-2 bg-red-50 border-b border-red-200">
                    <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                      <XCircle size={14} />
                      Admin Rejected ({adminRejected.length})
                    </h4>
                  </div>
                  {adminRejected.map(renderRecommendation)}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

