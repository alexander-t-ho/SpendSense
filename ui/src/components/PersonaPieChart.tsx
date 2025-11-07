import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface PersonaData {
  persona_id: string
  persona_name: string
  matched_criteria: number
  total_criteria: number
  percentage: number
  points_per_criterion: number
  total_points: number
  matched_reasons?: string[]
}

interface PersonaPieChartProps {
  personas: PersonaData[]
}

// Color palette for personas
const PERSONA_COLORS: { [key: string]: string } = {
  'high_utilization': '#ef4444',      // Red
  'variable_income_budgeter': '#f97316', // Orange
  'subscription_heavy': '#eab308',      // Yellow
  'fee_accumulator': '#a855f7',        // Purple
  'savings_builder': '#3b82f6',         // Blue
}

const getPersonaColor = (personaId: string): string => {
  return PERSONA_COLORS[personaId] || '#6b7280' // Default gray
}

export default function PersonaPieChart({ personas }: PersonaPieChartProps) {
  // Calculate criteria ratio for each persona (matched_criteria / total_criteria)
  const totalCriteriaRatio = personas.reduce((sum, p) => {
    const ratio = p.total_criteria > 0 ? p.matched_criteria / p.total_criteria : 0
    return sum + ratio
  }, 0)
  
  // Prepare data for pie chart based on criteria ratio instead of points
  const chartData = personas.map((persona) => {
    const criteriaRatio = persona.total_criteria > 0 ? persona.matched_criteria / persona.total_criteria : 0
    const ratioPercentage = totalCriteriaRatio > 0 ? (criteriaRatio / totalCriteriaRatio) * 100 : 0
    
    return {
      name: persona.persona_name,
      value: criteriaRatio, // Use criteria ratio instead of points
      percentage: Math.round(ratioPercentage), // Percentage based on criteria ratio
      matchedCriteria: `${persona.matched_criteria}/${persona.total_criteria}`,
      criteriaRatio: criteriaRatio,
      pointsPerCriterion: persona.points_per_criterion,
      totalPoints: persona.total_points,
      fill: getPersonaColor(persona.persona_id),
    }
  })

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0]
      return (
        <div className="bg-white p-3 border border-[#D4C4B0] rounded-lg shadow-lg">
          <p className="font-semibold text-[#5D4037]">{data.payload.name}</p>
          <p className="text-sm text-[#556B2F]">
            Criteria Ratio: {data.payload.matchedCriteria} ({data.payload.percentage}%)
          </p>
          <p className="text-sm text-[#556B2F]">
            Criteria Match: {(data.payload.criteriaRatio * 100).toFixed(1)}%
          </p>
          <p className="text-sm text-[#556B2F]">
            Points: {data.payload.totalPoints.toFixed(2)} (per criterion: {data.payload.pointsPerCriterion})
          </p>
        </div>
      )
    }
    return null
  }

  const CustomLegend = ({ payload }: any) => {
    return (
      <ul className="flex flex-wrap justify-center gap-4 mt-4">
        {payload.map((entry: any, index: number) => (
          <li key={`legend-${index}`} className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm text-[#556B2F]">
              {entry.value} ({entry.payload.percentage}%)
            </span>
          </li>
        ))}
      </ul>
    )
  }

  if (personas.length === 0) {
    return (
      <div className="text-center py-8 text-[#8B6F47]">
        <p>No matching personas found</p>
      </div>
    )
  }

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percentage }) => `${name} (${percentage}%)`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend content={<CustomLegend />} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

