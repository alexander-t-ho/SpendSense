interface FeatureCardProps {
  features: {
    subscriptions?: any
    savings?: any
    credit?: any
    income?: any
  }
}

export default function FeatureCard({ features }: FeatureCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Subscriptions */}
        {features.subscriptions && (
          <div className="border-l-4 border-blue-500 pl-4">
            <h3 className="font-semibold text-gray-900 mb-2">Subscriptions</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Recurring Merchants:</span>
                <span className="font-medium">{features.subscriptions.recurring_merchants || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Monthly Spend:</span>
                <span className="font-medium">
                  ${(features.subscriptions.monthly_recurring_spend || 0).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Share of Total:</span>
                <span className="font-medium">
                  {(features.subscriptions.subscription_share_of_total || 0).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Savings */}
        {features.savings && (
          <div className="border-l-4 border-green-500 pl-4">
            <h3 className="font-semibold text-gray-900 mb-2">Savings</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Growth Rate:</span>
                <span className="font-medium">
                  {(features.savings.growth_rate_percent || 0).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Monthly Inflow:</span>
                <span className="font-medium">
                  ${(features.savings.monthly_net_inflow || 0).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Emergency Fund:</span>
                <span className="font-medium">
                  {(features.savings.emergency_fund_coverage_months || 0).toFixed(1)} months
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Credit */}
        {features.credit && (
          <div className="border-l-4 border-red-500 pl-4">
            <h3 className="font-semibold text-gray-900 mb-2">Credit</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Has Credit Cards:</span>
                <span className="font-medium">
                  {features.credit.has_credit_cards ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">High Utilization (≥50%):</span>
                <span className="font-medium">
                  {features.credit.any_high_utilization_50 ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Interest Charges:</span>
                <span className="font-medium">
                  {features.credit.any_interest_charges ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Overdue:</span>
                <span className="font-medium">
                  {features.credit.any_overdue ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Income */}
        {features.income && (
          <div className="border-l-4 border-purple-500 pl-4">
            <h3 className="font-semibold text-gray-900 mb-2">Income</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Payroll Detected:</span>
                <span className="font-medium">
                  {features.income.has_payroll_detected ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Frequency:</span>
                <span className="font-medium capitalize">
                  {features.income.payment_frequency?.frequency || 'Unknown'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Cash Flow Buffer:</span>
                <span className="font-medium">
                  {(features.income.cash_flow_buffer_months || 0).toFixed(1)} months
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Variable Income:</span>
                <span className="font-medium">
                  {features.income.is_variable_income ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

