import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronUp, Clock, Flag, XCircle, CheckCircle } from 'lucide-react'

interface RecommendationsDropdownProps {
  userId: string
}

export default function RecommendationsDropdown({ userId }: RecommendationsDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)

  const { data: allRecs, isLoading } = useQuery({
    queryKey: ['all-recommendations-dropdown', userId],
    queryFn: async () => {
      const response = await fetch(`/api/operator/recommendations?status=all&user_id=${userId}&limit=100`)
      if (!response.ok) {
        throw new Error('Failed to fetch recommendations')
      }
      return response.json()
    },
    enabled: !!userId && isOpen,
    retry: false,
  })

  // Filter out approved recommendations (those are shown in main view)
  const nonApprovedRecs = allRecs?.recommendations?.filter((rec: any) => !rec.approved) || []

  // Group by status
  const pending = nonApprovedRecs.filter((rec: any) => !rec.approved && !rec.flagged && !rec.rejected)
  const flagged = nonApprovedRecs.filter((rec: any) => rec.flagged)
  const rejected = nonApprovedRecs.filter((rec: any) => rec.rejected)

  const getStatusBadge = (rec: any) => {
    if (rec.flagged) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-300">
          <Flag size={12} />
          Flagged
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

  return (
    <div className="relative w-full">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm font-medium flex items-center justify-between border border-gray-300"
      >
        <span className="flex items-center gap-2">
          <span>Other Recommendations</span>
          <span className="px-2 py-0.5 bg-gray-300 text-gray-700 rounded-full text-xs font-semibold">
            {nonApprovedRecs.length}
          </span>
        </span>
        {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-300 rounded-lg shadow-xl z-50 max-h-96 overflow-y-auto">
          <div className="p-4 space-y-4">
            {isLoading ? (
              <div className="text-sm text-gray-600 text-center py-4">Loading...</div>
            ) : (
              <>
                {pending.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <Clock size={14} />
                      Pending ({pending.length})
                    </h4>
                    <div className="space-y-2">
                      {pending.map((rec: any) => (
                        <div key={rec.id} className="p-3 bg-gray-50 border border-gray-200 rounded-md">
                          <div className="flex items-start justify-between mb-2">
                            <h5 className="text-sm font-medium text-gray-900">{rec.title}</h5>
                            {getStatusBadge(rec)}
                          </div>
                          <p className="text-xs text-gray-600 line-clamp-2">
                            {rec.description || rec.recommendation_text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {flagged.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <Flag size={14} />
                      Flagged ({flagged.length})
                    </h4>
                    <div className="space-y-2">
                      {flagged.map((rec: any) => (
                        <div key={rec.id} className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                          <div className="flex items-start justify-between mb-2">
                            <h5 className="text-sm font-medium text-gray-900">{rec.title}</h5>
                            {getStatusBadge(rec)}
                          </div>
                          <p className="text-xs text-gray-600 line-clamp-2">
                            {rec.description || rec.recommendation_text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {rejected.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <XCircle size={14} />
                      Rejected ({rejected.length})
                    </h4>
                    <div className="space-y-2">
                      {rejected.map((rec: any) => (
                        <div key={rec.id} className="p-3 bg-red-50 border border-red-200 rounded-md">
                          <div className="flex items-start justify-between mb-2">
                            <h5 className="text-sm font-medium text-gray-900">{rec.title}</h5>
                            {getStatusBadge(rec)}
                          </div>
                          <p className="text-xs text-gray-600 line-clamp-2">
                            {rec.description || rec.recommendation_text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {nonApprovedRecs.length === 0 && !isLoading && (
                  <div className="text-sm text-gray-600 text-center py-4">
                    No other recommendations (pending, flagged, or rejected)
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

