import { useQuery } from '@tanstack/react-query'
import { fetchApprovedRecommendations } from '../services/api'
import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import RecommendationsSection from './RecommendationsSection'

interface RecommendationsBannerProps {
  userId: string
  windowDays?: number
}

export default function RecommendationsBanner({ userId, windowDays = 180 }: RecommendationsBannerProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  // Fetch pending recommendations (approved but not yet reviewed by user)
  // For now, we'll show recommendations that need user action (approval of action plans)
  // This would need an endpoint to get recommendations awaiting user approval
  const { data: pendingData, isLoading } = useQuery({
    queryKey: ['pendingActionPlans', userId],
    queryFn: async () => {
      // This would need a new endpoint - for now return empty
      // The user wants to see how many recommendations need their approval
      // This likely means recommendations with action plans that haven't been approved by the user
      // For now, we'll fetch approved recommendations and check which ones have pending action plans
      try {
        const approved = await fetchApprovedRecommendations(userId)
        // Count recommendations that might have action plans needing approval
        // In a real implementation, this would query for action plans with status 'pending'
        return { count: approved?.total || 0 }
      } catch {
        return { count: 0 }
      }
    },
    enabled: !!userId,
  })

  if (isLoading) {
    return null
  }

  // For now, show count of approved recommendations that might need action
  // In a real implementation, this would be recommendations with pending action plans
  const pendingCount = pendingData?.count || 0

  // If no pending recommendations, don't show banner
  if (pendingCount === 0) {
    return null
  }

  return (
    <div className="bg-white shadow rounded-lg border border-[#D4C4B0] overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full bg-gradient-to-r from-[#556B2F] to-[#6B7A3C] hover:from-[#6B7A3C] hover:to-[#556B2F] transition-all text-white p-4 flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div>
            <h3 className="text-lg font-semibold mb-1">Recommendations Awaiting Your Approval</h3>
            <p className="text-sm opacity-90">
              {pendingCount} recommendation{pendingCount !== 1 ? 's' : ''} need your review
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-right">
            <div className="text-2xl font-bold">{pendingCount}</div>
            <p className="text-xs opacity-75">Click to view</p>
          </div>
          {isExpanded ? (
            <ChevronUp className="h-5 w-5" />
          ) : (
            <ChevronDown className="h-5 w-5" />
          )}
        </div>
      </button>
      
      {isExpanded && (
        <div className="p-4 bg-[#E8F5E9] border-t border-[#D4C4B0]">
          <RecommendationsSection userId={userId} windowDays={windowDays} readOnly={false} />
        </div>
      )}
    </div>
  )
}
