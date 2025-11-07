import { useState, useRef, useEffect } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import WeeklyRecapCard from './WeeklyRecapCard'
import SpendingAnalysisCard from './SpendingAnalysisCard'
import SuggestedBudgetCard from './SuggestedBudgetCard'
import BudgetTrackingCard from './BudgetTrackingCard'
import NetWorthRecapCard from './NetWorthRecapCard'

interface FinancialInsightsCarouselProps {
  userId: string
  isAdmin?: boolean
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

export default function FinancialInsightsCarousel({ userId, isAdmin = false }: FinancialInsightsCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [touchStart, setTouchStart] = useState<number | null>(null)
  const [touchEnd, setTouchEnd] = useState<number | null>(null)
  const [isHovered, setIsHovered] = useState(false)

  // Minimum swipe distance (in px)
  const minSwipeDistance = 50

  // Card-specific props
  const getCardProps = (cardId: string) => {
    switch (cardId) {
      case 'spending-analysis':
        return { months: 6 }
      case 'net-worth':
        return { period: 'month' as const }
      case 'suggested-budget':
        return { lookbackMonths: 6, isAdmin }
      default:
        return {}
    }
  }

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? CARDS.length - 1 : prev - 1))
  }

  const goToNext = () => {
    setCurrentIndex((prev) => (prev === CARDS.length - 1 ? 0 : prev + 1))
  }

  // Handle wrapping at boundaries
  const handlePrevious = () => {
    if (currentIndex === 0) {
      // Wrap to end
      setCurrentIndex(CARDS.length - 1)
      // Scroll to end smoothly
      setTimeout(() => {
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollTo({
            left: scrollContainerRef.current.scrollWidth,
            behavior: 'auto'
          })
        }
      }, 0)
    } else {
      goToPrevious()
    }
  }

  const handleNext = () => {
    if (currentIndex === CARDS.length - 1) {
      // Wrap to beginning
      setCurrentIndex(0)
      // Scroll to start smoothly
      setTimeout(() => {
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollTo({
            left: 0,
            behavior: 'auto'
          })
        }
      }, 0)
    } else {
      goToNext()
    }
  }

  const goToSlide = (index: number) => {
    setCurrentIndex(index)
  }

  // Scroll to the current card
  useEffect(() => {
    if (scrollContainerRef.current) {
      const cardWidth = scrollContainerRef.current.offsetWidth / getCardsPerView()
      const scrollPosition = currentIndex * cardWidth
      
      // Handle wrapping - if scrolling from end to start, jump to end first
      if (currentIndex === 0 && scrollContainerRef.current.scrollLeft > cardWidth * 2) {
        // We're wrapping from end to start
        scrollContainerRef.current.scrollLeft = scrollContainerRef.current.scrollWidth
        setTimeout(() => {
          if (scrollContainerRef.current) {
            scrollContainerRef.current.scrollTo({
              left: 0,
              behavior: 'smooth'
            })
          }
        }, 50)
      } else if (currentIndex === CARDS.length - 1 && scrollContainerRef.current.scrollLeft < cardWidth) {
        // We're wrapping from start to end
        scrollContainerRef.current.scrollLeft = 0
        setTimeout(() => {
          if (scrollContainerRef.current) {
            scrollContainerRef.current.scrollTo({
              left: scrollContainerRef.current.scrollWidth,
              behavior: 'smooth'
            })
          }
        }, 50)
      } else {
        scrollContainerRef.current.scrollTo({
          left: scrollPosition,
          behavior: 'smooth'
        })
      }
    }
  }, [currentIndex])

  // Calculate how many cards to show per view based on screen size
  const getCardsPerView = () => {
    if (typeof window === 'undefined') return 1
    const width = window.innerWidth
    if (width < 640) return 1 // Mobile: 1 card
    if (width < 1024) return 1.5 // Tablet: 1.5 cards (show partial next)
    return 1 // Desktop: 1 card at a time for better focus
  }

  // Touch handlers for swipe gestures
  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null)
    setTouchStart(e.targetTouches[0].clientX)
  }

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX)
  }

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return
    const distance = touchStart - touchEnd
    const isLeftSwipe = distance > minSwipeDistance
    const isRightSwipe = distance < -minSwipeDistance
    if (isLeftSwipe) {
      handleNext()
    } else if (isRightSwipe) {
      handlePrevious()
    }
  }

  return (
    <div 
      className="relative w-full"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Progress Indicators and Titles - MOVED TO TOP */}
      <div className="mb-6">
        {/* Progress Indicators */}
        <div className="flex justify-center gap-2 mb-4">
          {CARDS.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`h-1.5 rounded-full transition-all ${
                index === currentIndex
                  ? 'w-8 bg-[#556B2F]'
                  : 'w-2 bg-[#D4C4B0] hover:bg-[#C8E6C9]'
              }`}
              aria-label={`Go to ${CARDS[index].title}`}
            />
          ))}
        </div>

        {/* Card Titles - Horizontal Scrollable on Mobile */}
        <div className="flex justify-center gap-2 sm:gap-4 overflow-x-auto pb-2 scrollbar-hide">
          {CARDS.map((card, index) => (
            <button
              key={card.id}
              onClick={() => goToSlide(index)}
              className={`text-xs sm:text-sm font-medium transition-all whitespace-nowrap px-3 py-1.5 rounded-md ${
                index === currentIndex
                  ? 'text-[#5D4037] bg-[#E8F5E9] font-semibold shadow-sm'
                  : 'text-[#556B2F] hover:text-[#5D4037] hover:bg-[#F5E6D3]'
              }`}
            >
              {card.title}
            </button>
          ))}
        </div>
      </div>

      {/* Horizontal Scrolling Container */}
      <div className="relative">
        <div
          ref={scrollContainerRef}
          className="flex overflow-x-auto snap-x snap-mandatory scrollbar-hide gap-4 pb-4 scroll-smooth"
          style={{
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
            WebkitOverflowScrolling: 'touch'
          }}
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
        >
          {CARDS.map((card, index) => {
            const CardComponent = card.component
            const isCurrentCard = index === currentIndex
            return (
              <div
                key={card.id}
                className="relative flex-shrink-0 w-full sm:w-[calc(100%-2rem)] md:w-full snap-center"
                style={{ minWidth: '100%' }}
              >
                {/* Left Navigation Arrow - Positioned in middle of each card */}
                {isCurrentCard && (
                  <button
                    onClick={handlePrevious}
                    className={`absolute left-4 top-1/2 z-30 bg-white hover:bg-[#E8F5E9] border-2 border-[#556B2F] rounded-full p-3.5 text-[#556B2F] transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-110 ${
                      isHovered ? 'opacity-100' : 'opacity-90'
                    }`}
                    aria-label="Previous insight"
                    style={{
                      transform: `translateY(-50%) ${isHovered ? 'translateX(0) scale(1)' : 'translateX(4px) scale(0.95)'}`
                    }}
                  >
                    <ChevronLeft size={28} strokeWidth={2.5} />
                  </button>
                )}

                {/* Right Navigation Arrow - Positioned in middle of each card */}
                {isCurrentCard && (
                  <button
                    onClick={handleNext}
                    className={`absolute right-4 top-1/2 z-30 bg-white hover:bg-[#E8F5E9] border-2 border-[#556B2F] rounded-full p-3.5 text-[#556B2F] transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-110 ${
                      isHovered ? 'opacity-100' : 'opacity-90'
                    }`}
                    aria-label="Next insight"
                    style={{
                      transform: `translateY(-50%) ${isHovered ? 'translateX(0) scale(1)' : 'translateX(-4px) scale(0.95)'}`
                    }}
                  >
                    <ChevronRight size={28} strokeWidth={2.5} />
                  </button>
                )}

                {renderCard(CardComponent, userId, getCardProps(card.id))}
              </div>
            )
          })}
        </div>
      </div>

      {/* Hide scrollbar for webkit browsers */}
      <style dangerouslySetInnerHTML={{
        __html: `
          .scrollbar-hide::-webkit-scrollbar {
            display: none;
          }
        `
      }} />
    </div>
  )
}

