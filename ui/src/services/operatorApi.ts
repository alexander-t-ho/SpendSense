/**
 * API service for operator endpoints
 */

// Use environment variable for production, fallback to relative path for local dev (Vite proxy)
const API_BASE_URL = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL.replace(/\/+$/, '')}/api` : '/api'

export interface OperatorRecommendation {
  id: string
  user_id: string
  user_name: string
  user_email: string
  recommendation_type: string
  title: string
  description: string | null
  rationale: string
  content_id: string | null
  persona_id: string | null
  persona_name: string | null  // Human-readable persona name
  persona_info: {
    primary_persona: string
    risk: string
    risk_level: string
  } | null
  action_items?: string[]
  expected_impact?: string | null
  priority?: string | null
  approved: boolean
  approved_at: string | null
  flagged: boolean
  rejected?: boolean
  rejected_at?: string | null
  rejected_by?: string | null  // User ID who rejected (if user rejected)
  created_at: string
  updated_at: string
}

export interface RecommendationQueue {
  recommendations: OperatorRecommendation[]
  total: number
  status: string
}

export async function fetchRecommendationQueue(
  status: string = 'pending',
  userId?: string,
  limit: number = 50
): Promise<RecommendationQueue> {
  const params = new URLSearchParams({
    status,
    limit: limit.toString(),
  })
  if (userId) {
    params.append('user_id', userId)
  }
  const response = await fetch(`${API_BASE_URL}/operator/recommendations?${params}`)
  if (!response.ok) {
    throw new Error('Failed to fetch recommendation queue')
  }
  return response.json()
}

export async function approveRecommendation(recommendationId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/operator/recommendations/${recommendationId}/approve`,
    {
      method: 'PUT',
    }
  )
  if (!response.ok) {
    throw new Error('Failed to approve recommendation')
  }
}

export async function flagRecommendation(recommendationId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/operator/recommendations/${recommendationId}/flag`,
    {
      method: 'PUT',
    }
  )
  if (!response.ok) {
    throw new Error('Failed to flag recommendation')
  }
}

export async function rejectRecommendation(recommendationId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/operator/recommendations/${recommendationId}/reject`,
    {
      method: 'PUT',
    }
  )
  if (!response.ok) {
    throw new Error('Failed to reject recommendation')
  }
}

export interface UserSignals {
  user_id: string
  window_days: number
  signals: Record<string, any>
  timestamp: string
}

export async function fetchUserSignals(
  userId: string,
  windowDays: number = 180
): Promise<UserSignals> {
  const params = new URLSearchParams({
    window_days: windowDays.toString(),
  })
  const response = await fetch(
    `${API_BASE_URL}/operator/signals/${userId}?${params}`
  )
  if (!response.ok) {
    throw new Error('Failed to fetch user signals')
  }
  return response.json()
}

export interface DecisionTrace {
  user_id: string
  timestamp: string
  assigned_personas: string[]
  primary_persona: string
  matching_results: Record<string, any>
  features_snapshot: Record<string, any>
  rationale: string
}

export interface UserTraces {
  user_id: string
  traces: DecisionTrace[]
  total: number
}

export async function fetchUserTraces(userId: string): Promise<UserTraces> {
  const response = await fetch(`${API_BASE_URL}/operator/traces/${userId}`)
  if (!response.ok) {
    throw new Error('Failed to fetch decision traces')
  }
  return response.json()
}

