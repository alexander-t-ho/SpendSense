# Financial Tracking Feature Template

A reusable Origin-inspired template component for building consistent financial tracking features.

## Overview

The `FinancialTrackingFeatureTemplate` component provides a standardized structure and styling for all financial feature cards in the application. It ensures visual consistency and reduces code duplication.

## Features

- ✅ Consistent header with icon and title
- ✅ Flexible key metrics display (1-4 metrics)
- ✅ Support for visualizations (charts, graphs)
- ✅ Insights list with bullet points
- ✅ Action buttons/controls section
- ✅ Custom content area via children prop
- ✅ Built-in loading and error states
- ✅ Color themes (blue, green, red, purple, orange, yellow)
- ✅ Trend indicators for metrics

## Basic Usage

```tsx
import FinancialTrackingFeatureTemplate, { KeyMetric } from './FinancialTrackingFeatureTemplate'
import { TrendingUp, DollarSign } from 'lucide-react'

function MyFeature() {
  const metrics: KeyMetric[] = [
    {
      label: 'Total Spending',
      value: '$12,450',
      color: 'red',
      icon: DollarSign,
      trend: 'up',
      trendValue: '5.2%'
    }
  ]

  return (
    <FinancialTrackingFeatureTemplate
      title="My Feature"
      icon={TrendingUp}
      iconColor="green"
      subtitle="Optional description"
      period="Last 30 days"
      keyMetrics={metrics}
      insights={['Insight 1', 'Insight 2']}
    />
  )
}
```

## Props

### Required Props

- **`title`** (string): Main title of the feature

### Optional Props

- **`icon`** (LucideIcon): Icon component from lucide-react
- **`iconColor`** ('blue' | 'green' | 'red' | 'purple' | 'orange' | 'yellow'): Color theme (default: 'blue')
- **`subtitle`** (string): Optional subtitle or description
- **`period`** (string): Period indicator (e.g., "6 months", "Last 30 days")
- **`keyMetrics`** (KeyMetric[]): Array of key metrics to display
- **`visualizations`** (ReactNode): Main visualization (chart, graph, etc.)
- **`insights`** (string[]): List of insights to display
- **`actions`** (ReactNode): Additional action buttons or controls
- **`children`** (ReactNode): Custom content section
- **`isLoading`** (boolean): Loading state
- **`error`** (string | Error | null): Error state
- **`footer`** (ReactNode): Optional footer content
- **`headerActions`** (ReactNode): Optional header actions (filters, settings)

## KeyMetric Interface

```tsx
interface KeyMetric {
  label: string                    // Metric label
  value: string | number           // Metric value (formatted string or number)
  color?: 'blue' | 'green' | ...   // Color theme (defaults to iconColor)
  icon?: LucideIcon                // Optional icon for the metric
  trend?: 'up' | 'down' | 'neutral'  // Trend direction
  trendValue?: string              // Trend value (e.g., "5.2%")
}
```

## Examples

### Example 1: Simple Feature with Metrics

```tsx
<FinancialTrackingFeatureTemplate
  title="Spending Overview"
  icon={TrendingUp}
  iconColor="green"
  keyMetrics={[
    { label: 'Total', value: '$5,000', color: 'blue' },
    { label: 'Average', value: '$1,250', color: 'green' }
  ]}
  insights={['Spending is up 10% this month']}
/>
```

### Example 2: Feature with Chart

```tsx
<FinancialTrackingFeatureTemplate
  title="Monthly Trends"
  icon={BarChart3}
  iconColor="purple"
  keyMetrics={metrics}
  visualizations={
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={chartData}>
        <Line dataKey="value" stroke="#8884d8" />
      </LineChart>
    </ResponsiveContainer>
  }
  insights={insights}
/>
```

### Example 3: Feature with Custom Content

```tsx
<FinancialTrackingFeatureTemplate
  title="Custom Feature"
  icon={Calendar}
  iconColor="orange"
>
  <div className="custom-content">
    {/* Your custom content here */}
  </div>
</FinancialTrackingFeatureTemplate>
```

### Example 4: Feature with Actions

```tsx
<FinancialTrackingFeatureTemplate
  title="Budget Tracking"
  icon={DollarSign}
  iconColor="blue"
  keyMetrics={metrics}
  actions={
    <div className="flex gap-2">
      <button className="btn-primary">Edit Budget</button>
      <button className="btn-secondary">View Details</button>
    </div>
  }
/>
```

## Color Themes

The template supports 6 color themes:

- **blue**: Blue theme (default)
- **green**: Green theme
- **red**: Red theme
- **purple**: Purple theme
- **orange**: Orange theme
- **yellow**: Yellow theme

Each theme provides:
- Background color for metric boxes
- Text color for values
- Icon color
- Border color for accent

## Refactoring Existing Components

To refactor an existing component to use this template:

1. Import the template component
2. Extract key metrics into the `KeyMetric[]` format
3. Move visualizations to the `visualizations` prop
4. Move insights to the `insights` array
5. Replace the component structure with the template

**Before:**
```tsx
<div className="bg-white shadow rounded-lg p-6">
  <h3>My Feature</h3>
  <div className="metrics">...</div>
  <div className="chart">...</div>
</div>
```

**After:**
```tsx
<FinancialTrackingFeatureTemplate
  title="My Feature"
  icon={MyIcon}
  keyMetrics={metrics}
  visualizations={<Chart />}
/>
```

## Best Practices

1. **Consistent Icons**: Use lucide-react icons for consistency
2. **Color Coding**: Use colors meaningfully (green for positive, red for negative, etc.)
3. **Metric Limits**: Keep key metrics to 4 or fewer for better UX
4. **Loading States**: Always handle loading states
5. **Error Handling**: Provide user-friendly error messages
6. **Responsive Design**: The template is responsive by default
7. **Accessibility**: Include proper ARIA labels and semantic HTML

## See Also

- `FinancialTrackingFeatureTemplate.example.tsx` - Complete usage examples
- Existing components using this template:
  - `SpendingAnalysisCard.tsx`
  - `BudgetTrackingCard.tsx`
  - `NetWorthRecapCard.tsx`

