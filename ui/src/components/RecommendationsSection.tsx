import { useQuery } from '@tanstack/react-query'
import { fetchRecommendations, getConsentStatus } from '../services/api'
import ConsentBanner from './ConsentBanner'
import ActionableRecommendation from './ActionableRecommendation'
import React from 'react'

interface RecommendationsSectionProps {
  userId: string
  windowDays?: number
  readOnly?: boolean  // If true, consent banner will be read-only (for admin views)
}

export default function RecommendationsSection({ userId, windowDays = 180, readOnly = false }: RecommendationsSectionProps) {
  // For admin/readOnly view, fetch all recommendations (pending, approved, etc.)
  // For regular users, only fetch approved recommendations
  const { data: allRecs, isLoading: isLoadingAll } = useQuery({
    queryKey: ['all-recommendations', userId],
    queryFn: async () => {
      const response = await fetch(`/api/operator/recommendations?status=all&user_id=${userId}&limit=100`)
      if (!response.ok) {
        throw new Error('Failed to fetch recommendations')
      }
      return response.json()
    },
    enabled: !!userId && readOnly,
    retry: false,
    staleTime: 30000, // Cache for 30 seconds
    cacheTime: 300000, // Keep in cache for 5 minutes
  })

  // For regular users, get approved recommendations
  const { data: approvedRecs, isLoading: isLoadingApproved } = useQuery({
    queryKey: ['approved-recommendations', userId],
    queryFn: async () => {
      const response = await fetch(`/api/recommendations/${userId}/approved`)
      if (!response.ok) {
        throw new Error('Failed to fetch approved recommendations')
      }
      return response.json()
    },
    enabled: !!userId && !readOnly,
    retry: false,
    staleTime: 30000, // Cache for 30 seconds
    cacheTime: 300000, // Keep in cache for 5 minutes
    refetchOnWindowFocus: false, // Don't refetch on window focus
  })

  // Fallback to the original recommendation generator if no approved recommendations
  // Only enable if we've confirmed there are no approved recommendations
  const hasApprovedRecs = approvedRecs && approvedRecs.total > 0
  const { data: recommendations, isLoading, error, refetch } = useQuery({
    queryKey: ['recommendations', userId, windowDays],
    queryFn: () => fetchRecommendations(userId, windowDays),
    enabled: !!userId && !readOnly && !isLoadingApproved && !hasApprovedRecs,
    retry: false,
    staleTime: 60000, // Cache for 1 minute (generated recommendations are expensive)
    cacheTime: 600000, // Keep in cache for 10 minutes
  })

  // Listen for consent changes and refetch recommendations
  const { data: consent } = useQuery({
    queryKey: ['consent', userId],
    queryFn: () => getConsentStatus(userId),
    enabled: !!userId,
  })

  // Refetch recommendations when consent changes
  React.useEffect(() => {
    if (consent?.consented === true) {
      refetch()
    }
  }, [consent?.consented, refetch])

  // For admin view, show only approved recommendations (what users can see)
  // For regular users, also show only approved recommendations
  let displayRecommendations: any = null
  
  if (readOnly && allRecs?.recommendations) {
    // Admin view: show only approved recommendations (what users can see)
    // Also ensure we only show recommendations for this specific user (backend should filter, but double-check)
    const approvedOnly = allRecs.recommendations.filter((rec: any) => 
      rec.approved === true && rec.user_id === userId
    )
    displayRecommendations = {
      education_items: approvedOnly.map((rec: any) => ({
        id: rec.id,
        title: rec.title,
        recommendation_text: rec.description || rec.recommendation_text,
        action_items: rec.action_items || [],
        expected_impact: rec.expected_impact,
        priority: rec.priority,
        content_id: rec.content_id,
        type: rec.recommendation_type || 'actionable_recommendation',
        persona_names: rec.persona_id ? [rec.persona_id] : [],
        approved: rec.approved,
        flagged: rec.flagged,
        rejected: rec.rejected,
        created_at: rec.created_at,
        approved_at: rec.approved_at,
      })),
      partner_offers: []
    }
  } else if (!readOnly && approvedRecs?.recommendations?.length > 0) {
    // Regular user view: only approved recommendations
    displayRecommendations = { 
      education_items: approvedRecs.recommendations.map((rec: any) => ({
        id: rec.id,
        title: rec.title,
        recommendation_text: rec.recommendation_text || rec.description,
        action_items: rec.action_items || [],
        expected_impact: rec.expected_impact,
        priority: rec.priority,
        content_id: rec.content_id,
        type: rec.type || 'actionable_recommendation',
        persona_names: rec.persona_id ? [rec.persona_id] : [],
      })),
      partner_offers: []
    }
  } else if (!readOnly) {
    // Fallback to generated recommendations for regular users
    displayRecommendations = recommendations
  }

  // Show loading state only if we're still loading the primary query
  // Don't block UI for fallback query
  if (readOnly && isLoadingAll) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-[#8B6F47]">Loading recommendations...</div>
      </div>
    )
  }
  
  if (!readOnly && isLoadingApproved) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-[#8B6F47]">Loading recommendations...</div>
      </div>
    )
  }
  
  // Show loading state for fallback only if we have no approved recommendations
  if (!readOnly && !hasApprovedRecs && isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-[#8B6F47]">Generating personalized recommendations...</div>
        <p className="text-sm text-[#8B6F47] mt-2">This may take a moment...</p>
      </div>
    )
  }

  // Check if error is due to consent
  const errorObj = error as any
  const isConsentError = error && (
    (errorObj?.message?.includes('consent')) || 
    (errorObj?.response?.status === 403)
  )

  if (isConsentError || (!displayRecommendations && error)) {
    return (
      <div className="space-y-4">
        <ConsentBanner userId={userId} readOnly={readOnly} />
        {isConsentError && (
          <div className="bg-white shadow rounded-lg p-6">
            <div className="text-center">
              <p className="text-red-600 font-medium">Consent Required</p>
              <p className="text-sm text-[#556B2F] mt-2">
                {readOnly ? 'User must grant consent to view personalized recommendations.' : 'Please grant consent above to view personalized recommendations.'}
              </p>
            </div>
          </div>
        )}
      </div>
    )
  }

  if (!displayRecommendations) {
    return null
  }

  const educationItems = (displayRecommendations as any).education_items || []
  const partnerOffers = (displayRecommendations as any).partner_offers || []

  return (
    <div className="space-y-6">
      {/* Consent Banner */}
      <ConsentBanner userId={userId} readOnly={readOnly} />

      {/* Actionable Recommendations */}
      {educationItems.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-[#5D4037] mb-4">
            {readOnly ? 'User Recommendations' : 'Your Recommendations'} ({educationItems.length})
          </h2>
          {readOnly && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Admin View:</strong> Showing approved recommendations (what users can see). 
                Other recommendations (pending, flagged, rejected) are available in the dropdown under "Create Custom Recommendation".
              </p>
            </div>
          )}
          <div className="space-y-4">
            {educationItems.map((item: any) => (
              <div key={item.id} className="relative">
                {readOnly && (
                  <div className="mb-2 flex gap-2">
                    {item.approved && (
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800 border border-green-300">
                        ✓ Approved
                      </span>
                    )}
                    {item.flagged && (
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-300">
                        ⚠ Flagged
                      </span>
                    )}
                    {item.rejected && (
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800 border border-red-300">
                        ✗ Rejected
                      </span>
                    )}
                    {!item.approved && !item.flagged && !item.rejected && (
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800 border border-gray-300">
                        ⏳ Pending
                      </span>
                    )}
                  </div>
                )}
                <ActionableRecommendation
                  recommendation={item}
                  userId={userId}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Partner Offers - HIDDEN */}
      {false && partnerOffers.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-[#5D4037] mb-4">
            Partner Offers ({partnerOffers.length})
          </h2>
          <div className="space-y-4">
            {partnerOffers.map((offer: any) => (
              <div key={offer.id} className="border border-[#D4C4B0] rounded-lg p-4 hover:bg-[#E8F5E9]">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2 flex-wrap gap-2">
                      <h3 className="text-lg font-medium text-[#5D4037]">{offer.title}</h3>
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                        {offer.type}
                      </span>
                      {offer.persona_names && offer.persona_names.length > 0 && (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          Persona: {offer.persona_names.join(', ')}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-[#556B2F] mb-2">{offer.description}</p>
                    <p className="text-xs text-[#8B6F47] mb-3">Partner: {offer.partner_name}</p>
                    {offer.benefits && offer.benefits.length > 0 && (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-[#556B2F] mb-1">Benefits:</p>
                        <ul className="list-disc list-inside text-sm text-[#556B2F] space-y-1">
                          {offer.benefits.map((benefit: string, idx: number) => (
                            <li key={idx}>{benefit}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {offer.rationale && (
                      <div className="bg-green-50 border-l-4 border-green-400 p-3 rounded mb-3">
                        <p className="text-sm text-[#556B2F]">
                          <span className="font-medium">Why this might be a good fit: </span>
                          {offer.rationale}
                        </p>
                      </div>
                    )}
                    {offer.terms && (
                      <p className="text-xs text-[#8B6F47] mb-3">
                        <span className="font-medium">Terms: </span>
                        {offer.terms}
                      </p>
                    )}
                    {offer.tags && offer.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {offer.tags.map((tag: string, idx: number) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-[#F5E6D3] text-[#556B2F]"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    {offer.disclosure && (
                      <div className="mt-3 pt-3 border-t border-[#D4C4B0]">
                        <p className="text-xs text-[#8B6F47] italic">{offer.disclosure}</p>
                      </div>
                    )}
                  </div>
                </div>
                <a
                  href={offer.url}
                  className="mt-3 inline-flex items-center text-sm font-medium text-green-600 hover:text-green-800"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View offer →
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {educationItems.length === 0 && partnerOffers.length === 0 && (
        <div className="bg-white shadow rounded-lg p-6 text-center text-[#8B6F47]">
          <p>No recommendations available at this time.</p>
        </div>
      )}
    </div>
  )
}

