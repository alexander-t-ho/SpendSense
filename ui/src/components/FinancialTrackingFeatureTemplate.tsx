import { ReactNode } from 'react'
import { LucideIcon } from 'lucide-react'

/**
 * Financial Tracking Feature Template Component
 * 
 * Origin-inspired reusable template for financial tracking features.
 * Provides consistent structure and styling for all financial feature cards.
 * 
 * Usage:
 * ```tsx
 * <FinancialTrackingFeatureTemplate
 *   title="Feature Name"
 *   icon={IconComponent}
 *   iconColor="blue"
 *   subtitle="Optional subtitle"
 *   keyMetrics={[
 *     { label: "Metric 1", value: "$1,234", color: "blue" },
 *     { label: "Metric 2", value: "12%", color: "green" }
 *   ]}
 *   visualizations={<ChartComponent />}
 *   insights={["Insight 1", "Insight 2"]}
 *   actions={<Button>Action</Button>}
 * />
 * ```
 */

export interface KeyMetric {
  label: string
  value: string | number
  color?: 'blue' | 'green' | 'red' | 'purple' | 'orange' | 'yellow'
  icon?: LucideIcon
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
}

export interface FinancialTrackingFeatureTemplateProps {
  /** Main title of the feature */
  title: string
  
  /** Icon component from lucide-react */
  icon?: LucideIcon
  
  /** Icon color theme */
  iconColor?: 'blue' | 'green' | 'red' | 'purple' | 'orange' | 'yellow'
  
  /** Optional subtitle or description */
  subtitle?: string
  
  /** Period indicator (e.g., "6 months", "Last 30 days") */
  period?: string
  
  /** Key metrics to display in colored boxes */
  keyMetrics?: KeyMetric[]
  
  /** Main visualization (chart, graph, etc.) */
  visualizations?: ReactNode
  
  /** List of insights to display */
  insights?: string[]
  
  /** Additional action buttons or controls */
  actions?: ReactNode
  
  /** Custom content section (for flexibility) */
  children?: ReactNode
  
  /** Loading state */
  isLoading?: boolean
  
  /** Error state */
  error?: string | Error | null
  
  /** Optional footer content */
  footer?: ReactNode
  
  /** Optional header actions (e.g., filters, settings) */
  headerActions?: ReactNode
}

const colorClasses = {
  blue: {
    bg: 'bg-blue-50',
    text: 'text-blue-900',
    icon: 'text-[#556B2F]',
    border: 'border-[#556B2F]'
  },
  green: {
    bg: 'bg-green-50',
    text: 'text-green-900',
    icon: 'text-green-600',
    border: 'border-green-500'
  },
  red: {
    bg: 'bg-red-50',
    text: 'text-red-900',
    icon: 'text-red-600',
    border: 'border-red-500'
  },
  purple: {
    bg: 'bg-purple-50',
    text: 'text-purple-900',
    icon: 'text-purple-600',
    border: 'border-purple-500'
  },
  orange: {
    bg: 'bg-orange-50',
    text: 'text-orange-900',
    icon: 'text-orange-600',
    border: 'border-orange-500'
  },
  yellow: {
    bg: 'bg-yellow-50',
    text: 'text-yellow-900',
    icon: 'text-yellow-600',
    border: 'border-yellow-500'
  }
}

export default function FinancialTrackingFeatureTemplate({
  title,
  icon: Icon,
  iconColor = 'blue',
  subtitle,
  period,
  keyMetrics = [],
  visualizations,
  insights = [],
  actions,
  children,
  isLoading = false,
  error = null,
  footer,
  headerActions
}: FinancialTrackingFeatureTemplateProps) {
  
  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-5 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-6"></div>
          <div className="grid grid-cols-3 gap-4 mb-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    const errorMessage = error instanceof Error ? error.message : error
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center space-x-2 text-red-500">
          <span>⚠️</span>
          <p className="text-sm">{errorMessage || 'Failed to load data'}</p>
        </div>
      </div>
    )
  }

  const colorTheme = colorClasses[iconColor]

  return (
    <div className="bg-white shadow rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          {Icon && (
            <Icon className={`h-5 w-5 ${colorTheme.icon}`} />
          )}
          <div>
            <h3 className="text-lg font-semibold text-[#5D4037]">{title}</h3>
            {subtitle && (
              <p className="text-sm text-[#8B6F47] mt-0.5">{subtitle}</p>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {period && (
            <span className="text-sm text-[#8B6F47]">{period}</span>
          )}
          {headerActions}
        </div>
      </div>

      {/* Key Metrics */}
      {keyMetrics.length > 0 && (
        <div className={`grid gap-4 mb-6 ${
          keyMetrics.length === 1 ? 'grid-cols-1' :
          keyMetrics.length === 2 ? 'grid-cols-2' :
          keyMetrics.length === 3 ? 'grid-cols-3' :
          'grid-cols-4'
        }`}>
          {keyMetrics.map((metric, index) => {
            const metricColor = metric.color || iconColor
            const metricTheme = colorClasses[metricColor]
            const MetricIcon = metric.icon
            
            return (
              <div
                key={index}
                className={`${metricTheme.bg} rounded-lg p-4 border-l-4 ${metricTheme.border}`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  {MetricIcon && (
                    <MetricIcon className={`h-4 w-4 ${metricTheme.icon}`} />
                  )}
                  <span className={`text-sm ${metricTheme.text} opacity-80`}>
                    {metric.label}
                  </span>
                </div>
                <div className="flex items-baseline space-x-2">
                  <p className={`text-2xl font-bold ${metricTheme.text}`}>
                    {typeof metric.value === 'number'
                      ? metric.value.toLocaleString('en-US', { maximumFractionDigits: 0 })
                      : metric.value}
                  </p>
                  {metric.trend && metric.trendValue && (
                    <span
                      className={`text-xs font-medium ${
                        metric.trend === 'up'
                          ? 'text-green-600'
                          : metric.trend === 'down'
                          ? 'text-red-600'
                          : 'text-[#556B2F]'
                      }`}
                    >
                      {metric.trend === 'up' ? '↑' : metric.trend === 'down' ? '↓' : '→'} {metric.trendValue}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Visualizations */}
      {visualizations && (
        <div className="mb-6">
          {visualizations}
        </div>
      )}

      {/* Custom Children Content */}
      {children && (
        <div className="mb-6">
          {children}
        </div>
      )}

      {/* Insights */}
      {insights.length > 0 && (
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-[#556B2F] mb-3">Insights</h4>
          <ul className="space-y-2">
            {insights.map((insight, index) => (
              <li key={index} className="text-sm text-[#556B2F] flex items-start">
                <span className={`${colorTheme.icon} mr-2 mt-0.5`}>•</span>
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      {actions && (
        <div className="mt-4 pt-4 border-t">
          {actions}
        </div>
      )}

      {/* Footer */}
      {footer && (
        <div className="mt-4 pt-4 border-t">
          {footer}
        </div>
      )}
    </div>
  )
}

