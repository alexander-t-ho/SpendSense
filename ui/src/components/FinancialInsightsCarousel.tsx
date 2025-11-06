import { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import WeeklyRecapCard from './WeeklyRecapCard'
import SpendingAnalysisCard from './SpendingAnalysisCard'
import SuggestedBudgetCard from './SuggestedBudgetCard'
import BudgetTrackingCard from './BudgetTrackingCard'
import NetWorthRecapCard from './NetWorthRecapCard'

interface FinancialInsightsCarouselProps {
  userId: string
}

const CARDS = [
  { id: 'weekly-recap', title: 'Weekly Recap', component: WeeklyRecapCard },
  { id: 'spending-analysis', title: '6-Month Spending', component: SpendingAnalysisCard },
  { id: 'suggested-budget', title: 'Suggested Budget', component: SuggestedBudgetCard },
  { id: 'budget-tracking', title: 'Budget Tracking', component: BudgetTrackingCard },
  { id: 'net-worth', title: 'Net Worth', component: NetWorthRecapCard },
] as const

// Helper to render component with props
const renderCard = (Component: any, userId: string, props: any = {}) => {
  return <Component userId={userId} {...props} />
}

export default function FinancialInsightsCarousel({ userId }: FinancialInsightsCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0)

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? CARDS.length - 1 : prev - 1))
  }

  const goToNext = () => {
    setCurrentIndex((prev) => (prev === CARDS.length - 1 ? 0 : prev + 1))
  }

  const goToSlide = (index: number) => {
    setCurrentIndex(index)
  }

  const currentCard = CARDS[currentIndex]
  const CurrentCard = currentCard.component

  // Card-specific props
  const getCardProps = () => {
    switch (currentCard.id) {
      case 'spending-analysis':
        return { months: 6 }
      case 'net-worth':
        return { period: 'month' as const }
      case 'suggested-budget':
        return { lookbackMonths: 6 }
      default:
        return {}
    }
  }

  return (
    <div className="relative">
      {/* Card Container with Navigation */}
      <div className="relative">
        {/* Navigation Arrows - positioned over the card */}
        <button
          onClick={goToPrevious}
          className="absolute left-4 top-1/2 -translate-y-1/2 z-20 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-full p-2 text-white transition-all shadow-lg"
          aria-label="Previous insight"
        >
          <ChevronLeft size={24} />
        </button>
        <button
          onClick={goToNext}
          className="absolute right-4 top-1/2 -translate-y-1/2 z-20 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-full p-2 text-white transition-all shadow-lg"
          aria-label="Next insight"
        >
          <ChevronRight size={24} />
        </button>

        {/* Render the current card */}
        {renderCard(CurrentCard, userId, getCardProps())}
      </div>

      {/* Progress Indicators and Titles - positioned below the card */}
      <div className="mt-6">
        {/* Progress Indicators */}
        <div className="flex justify-center gap-2 mb-4">
          {CARDS.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`h-1 rounded-full transition-all ${
                index === currentIndex
                  ? 'w-8 bg-purple-600'
                  : 'w-2 bg-gray-300 hover:bg-gray-400'
              }`}
              aria-label={`Go to ${CARDS[index].title}`}
            />
          ))}
        </div>

        {/* Card Titles */}
        <div className="flex justify-center gap-4 flex-wrap">
          {CARDS.map((card, index) => (
            <button
              key={card.id}
              onClick={() => goToSlide(index)}
              className={`text-sm font-medium transition-colors px-2 py-1 rounded ${
                index === currentIndex
                  ? 'text-gray-900 bg-purple-100 font-semibold'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {card.title}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

