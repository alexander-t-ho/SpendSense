import { motion } from 'framer-motion'

interface CircularBudgetDialProps {
  spent: number
  total: number
  size?: number
  strokeWidth?: number
}

export default function CircularBudgetDial({ 
  spent, 
  total, 
  size = 280, 
  strokeWidth = 28 
}: CircularBudgetDialProps) {
  const percentage = total > 0 ? Math.min((spent / total) * 100, 100) : 0
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius // Full circle circumference
  // Calculate offset: when offset = circumference, nothing is visible
  // When offset = 0, full circle is visible
  // For percentage, we want: visible = percentage% of circumference
  // So offset = circumference - (percentage / 100) * circumference
  const offset = circumference - (percentage / 100) * circumference

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="overflow-visible"
          style={{ transform: 'rotate(-90deg)' }}
        >
          {/* Background circle (grey) */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#D4C4B0"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          {/* Progress circle (green) - fills clockwise from top */}
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#556B2F"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.5, ease: "easeOut" }}
          />
        </svg>
        {/* Text content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-4xl font-bold text-white drop-shadow-lg">
            {Math.round(percentage)}%
          </div>
          <div className="text-5xl font-bold text-white drop-shadow-lg mt-2">
            {formatCurrency(spent)}
          </div>
          <div className="text-sm text-white/90 drop-shadow mt-1">
            {formatCurrency(total)} budget
          </div>
        </div>
      </div>
    </div>
  )
}

