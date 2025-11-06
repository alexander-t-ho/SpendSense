/**
 * Example Usage of FinancialTrackingFeatureTemplate
 * 
 * This file demonstrates how to use the FinancialTrackingFeatureTemplate
 * component to create various financial tracking features.
 */

import FinancialTrackingFeatureTemplate, { KeyMetric } from './FinancialTrackingFeatureTemplate'
import { TrendingUp, DollarSign, Calendar, AlertCircle, BarChart3 } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

// Example 1: Spending Analysis Feature
export function SpendingAnalysisExample() {
  const metrics: KeyMetric[] = [
    {
      label: 'Total Spending',
      value: '$12,450',
      color: 'red',
      icon: DollarSign,
      trend: 'up',
      trendValue: '5.2%'
    },
    {
      label: 'Avg Monthly',
      value: '$2,075',
      color: 'green',
      icon: TrendingUp
    },
    {
      label: 'Categories',
      value: '12',
      color: 'blue',
      icon: BarChart3
    }
  ]

  const chartData = [
    { month: 'Jan', spending: 2000 },
    { month: 'Feb', spending: 2100 },
    { month: 'Mar', spending: 1900 },
    { month: 'Apr', spending: 2200 },
    { month: 'May', spending: 2050 },
    { month: 'Jun', spending: 2300 }
  ]

  return (
    <FinancialTrackingFeatureTemplate
      title="6-Month Spending Analysis"
      icon={TrendingUp}
      iconColor="green"
      period="6 months"
      keyMetrics={metrics}
      visualizations={
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="spending" stroke="#3B82F6" />
          </LineChart>
        </ResponsiveContainer>
      }
      insights={[
        'Spending increased by 5.2% compared to last period',
        'Dining out is your top spending category',
        'You have a positive cash flow buffer of 2.5 months'
      ]}
    />
  )
}

// Example 2: Budget Tracking Feature
export function BudgetTrackingExample() {
  const metrics: KeyMetric[] = [
    {
      label: 'Budget Remaining',
      value: '$450',
      color: 'green',
      icon: DollarSign,
      trend: 'neutral'
    },
    {
      label: 'Spent This Month',
      value: '$1,550',
      color: 'blue',
      icon: Calendar
    },
    {
      label: 'Budget Limit',
      value: '$2,000',
      color: 'purple',
      icon: AlertCircle
    }
  ]

  return (
    <FinancialTrackingFeatureTemplate
      title="Monthly Budget Tracking"
      icon={Calendar}
      iconColor="purple"
      subtitle="Track your spending against your monthly budget"
      period="Current month"
      keyMetrics={metrics}
      insights={[
        'You are 77.5% through your monthly budget',
        'On track to stay within budget this month',
        'Top category: Groceries ($320)'
      ]}
      actions={
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          View Details
        </button>
      }
    />
  )
}

// Example 3: Net Worth Feature
export function NetWorthExample() {
  const metrics: KeyMetric[] = [
    {
      label: 'Current Net Worth',
      value: '$125,450',
      color: 'green',
      icon: TrendingUp,
      trend: 'up',
      trendValue: '12.5%'
    },
    {
      label: 'Total Assets',
      value: '$150,000',
      color: 'blue',
      icon: DollarSign
    },
    {
      label: 'Total Liabilities',
      value: '$24,550',
      color: 'red',
      icon: AlertCircle
    }
  ]

  return (
    <FinancialTrackingFeatureTemplate
      title="Net Worth Overview"
      icon={TrendingUp}
      iconColor="green"
      subtitle="Your financial position at a glance"
      keyMetrics={metrics}
      insights={[
        'Net worth increased by $13,950 this month',
        'Your assets are growing faster than liabilities',
        'You have a healthy debt-to-asset ratio of 16.4%'
      ]}
      footer={
        <p className="text-xs text-gray-500">
          Last updated: {new Date().toLocaleDateString()}
        </p>
      }
    />
  )
}

// Example 4: Custom Content Feature
export function CustomContentExample() {
  return (
    <FinancialTrackingFeatureTemplate
      title="Custom Feature"
      icon={BarChart3}
      iconColor="orange"
      subtitle="Example with custom content"
    >
      {/* Custom content goes here */}
      <div className="bg-gray-50 rounded-lg p-4">
        <p className="text-sm text-gray-600">
          You can add any custom content here using the children prop.
        </p>
      </div>
    </FinancialTrackingFeatureTemplate>
  )
}

