interface CreditCardBrandLogoProps {
  brand: 'visa' | 'mastercard' | 'amex' | 'discover' | null
  className?: string
}

export default function CreditCardBrandLogo({ brand, className = '' }: CreditCardBrandLogoProps) {
  if (!brand) return null

  switch (brand) {
    case 'visa':
      return (
        <div className={`flex items-center justify-center ${className}`}>
          <svg width="40" height="24" viewBox="0 0 40 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="40" height="24" rx="4" fill="#1434CB"/>
            <path d="M17.5 8.5L15 15.5H13L11.5 9.5H13.5L14.5 13.5L15.5 8.5H17.5ZM22.5 8.5L20.5 15.5H18.5L20.5 8.5H22.5ZM28.5 8.5C29.5 8.5 30 8.8 30.5 9.5L32.5 15.5H30.5L30 13.5H27.5L27 15.5H25L27.5 8.5H28.5ZM28 11.5L29 12.5L29.5 11.5H28Z" fill="white"/>
          </svg>
        </div>
      )
    case 'mastercard':
      return (
        <div className={`flex items-center justify-center ${className}`}>
          <svg width="40" height="24" viewBox="0 0 40 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="40" height="24" rx="4" fill="white"/>
            <circle cx="16" cy="12" r="6.5" fill="#EB001B"/>
            <circle cx="24" cy="12" r="6.5" fill="#F79E1B"/>
            <path d="M20 7.5C21.2 8.2 22 9.5 22 11C22 12.5 21.2 13.8 20 14.5C18.8 13.8 18 12.5 18 11C18 9.5 18.8 8.2 20 7.5Z" fill="#FF5F00"/>
          </svg>
        </div>
      )
    case 'amex':
      return (
        <div className={`flex items-center justify-center ${className}`}>
          <svg width="40" height="24" viewBox="0 0 40 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="40" height="24" rx="4" fill="#006FCF"/>
            <path d="M12 9L10 15H11L11.5 13H13.5L14 15H15L13 9H12ZM11.5 11.5L12.5 10L13.5 11.5H11.5ZM18 9V15H19.5L21 11.5L22.5 15H24V9H22.5V12.5L21.5 9H20.5L19.5 12.5V9H18ZM26 9L24.5 12L23 9H21.5V15H23V12L24.5 15H26L27.5 12V15H29V9H26Z" fill="white"/>
          </svg>
        </div>
      )
    case 'discover':
      return (
        <div className={`flex items-center justify-center ${className}`}>
          <svg width="40" height="24" viewBox="0 0 40 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="40" height="24" rx="4" fill="#FF6000"/>
            <path d="M12 9H16L14 12L16 15H12L13.5 12L12 9ZM20 9H24L22 12L24 15H20L21.5 12L20 9ZM28 9H32L30 12L32 15H28L29.5 12L28 9Z" fill="white"/>
          </svg>
        </div>
      )
    default:
      return null
  }
}

// Helper function to detect credit card brand from account name or account_id
export function detectCreditCardBrand(accountName?: string, accountId?: string): 'visa' | 'mastercard' | 'amex' | 'discover' | null {
  const name = (accountName || '').toLowerCase()
  const id = accountId || ''
  
  // Check account name first
  if (name.includes('visa')) return 'visa'
  if (name.includes('mastercard') || name.includes('master card')) return 'mastercard'
  if (name.includes('amex') || name.includes('american express')) return 'amex'
  if (name.includes('discover')) return 'discover'
  
  // Check account_id first digit (BIN - Bank Identification Number)
  if (id.length > 0) {
    const firstDigit = id[0]
    const firstTwo = id.substring(0, 2)
    const firstFour = id.substring(0, 4)
    
    // Visa: starts with 4
    if (firstDigit === '4') return 'visa'
    
    // Mastercard: starts with 51-55 or 2221-2720
    if (firstTwo >= '51' && firstTwo <= '55') return 'mastercard'
    if (firstFour >= '2221' && firstFour <= '2720') return 'mastercard'
    
    // Amex: starts with 34 or 37
    if (firstTwo === '34' || firstTwo === '37') return 'amex'
    
    // Discover: starts with 6011, 65, or 644-649
    if (firstFour === '6011') return 'discover'
    if (firstTwo === '65') return 'discover'
    if (firstTwo >= '64' && firstTwo <= '64') {
      const thirdDigit = id[2] || '0'
      if (thirdDigit >= '4' && thirdDigit <= '9') return 'discover'
    }
  }
  
  return null
}

