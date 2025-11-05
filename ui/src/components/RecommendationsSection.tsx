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
  // First try to get approved recommendations from the database
  const { data: approvedRecs, isLoading: isLoadingApproved } = useQuery({
    queryKey: ['approved-recommendations', userId],
    queryFn: async () => {
      const response = await fetch(`/api/recommendations/${userId}/approved`)
      if (!response.ok) {
        throw new Error('Failed to fetch approved recommendations')
      }
      return response.json()
    },
    enabled: !!userId,
    retry: false,
  })

  // Fallback to the original recommendation generator if no approved recommendations
  const { data: recommendations, isLoading, error, refetch } = useQuery({
    queryKey: ['recommendations', userId, windowDays],
    queryFn: () => fetchRecommendations(userId, windowDays),
    enabled: !!userId && (!approvedRecs || approvedRecs.total === 0),
    retry: false,
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

  // Use approved recommendations if available, otherwise fall back to generated ones
  const displayRecommendations = approvedRecs?.recommendations?.length > 0 
    ? { 
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
    : recommendations

  if (isLoadingApproved || isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-gray-500">Loading recommendations...</div>
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
              <p className="text-sm text-gray-600 mt-2">
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
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Your Recommendations ({educationItems.length})
          </h2>
          <div className="space-y-4">
            {educationItems.map((item: any) => (
              <ActionableRecommendation
                key={item.id}
                recommendation={item}
                userId={userId}
              />
            ))}
          </div>
        </div>
      )}

      {/* Partner Offers - HIDDEN */}
      {false && partnerOffers.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Partner Offers ({partnerOffers.length})
          </h2>
          <div className="space-y-4">
            {partnerOffers.map((offer: any) => (
              <div key={offer.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2 flex-wrap gap-2">
                      <h3 className="text-lg font-medium text-gray-900">{offer.title}</h3>
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                        {offer.type}
                      </span>
                      {offer.persona_names && offer.persona_names.length > 0 && (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          Persona: {offer.persona_names.join(', ')}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{offer.description}</p>
                    <p className="text-xs text-gray-500 mb-3">Partner: {offer.partner_name}</p>
                    {offer.benefits && offer.benefits.length > 0 && (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700 mb-1">Benefits:</p>
                        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                          {offer.benefits.map((benefit: string, idx: number) => (
                            <li key={idx}>{benefit}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {offer.rationale && (
                      <div className="bg-green-50 border-l-4 border-green-400 p-3 rounded mb-3">
                        <p className="text-sm text-gray-700">
                          <span className="font-medium">Why this might be a good fit: </span>
                          {offer.rationale}
                        </p>
                      </div>
                    )}
                    {offer.terms && (
                      <p className="text-xs text-gray-500 mb-3">
                        <span className="font-medium">Terms: </span>
                        {offer.terms}
                      </p>
                    )}
                    {offer.tags && offer.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {offer.tags.map((tag: string, idx: number) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    {offer.disclosure && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs text-gray-500 italic">{offer.disclosure}</p>
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
        <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">
          <p>No recommendations available at this time.</p>
        </div>
      )}
    </div>
  )
}

