import { useState } from 'react'
import { Building2 } from 'lucide-react'

interface CompanyLogoProps {
  companyName: string
  size?: number
  className?: string
}

/**
 * Company Logo Component
 * Displays company logos using Clearbit Logo API with fallback to icon
 */
export default function CompanyLogo({ companyName, size = 40, className = '' }: CompanyLogoProps) {
  const [imageError, setImageError] = useState(false)
  
  // Clean company name for logo API (remove common suffixes, normalize)
  const cleanName = companyName
    .replace(/\s+(Inc|LLC|Corp|Corporation|Ltd|Limited|Co|Company|Pharmacy|App|Music|Company)$/i, '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '')
  
  // Use Clearbit Logo API (free tier, no API key needed for basic usage)
  // Format: https://logo.clearbit.com/{domain}
  // We'll try to construct domain from company name
  const logoUrl = `https://logo.clearbit.com/${cleanName}.com`
  
  // Common company domain mappings for better accuracy
  const domainMap: Record<string, string> = {
    'applemusic': 'apple.com',
    'apple': 'apple.com',
    'shell': 'shell.com',
    'mobil': 'exxonmobil.com',
    'exxon': 'exxonmobil.com',
    'walgreens': 'walgreens.com',
    'cvs': 'cvs.com',
    'amtrak': 'amtrak.com',
    'netflix': 'netflix.com',
    'spotify': 'spotify.com',
    'amazon': 'amazon.com',
    'youtube': 'youtube.com',
    'hbo': 'hbo.com',
    'disney': 'disney.com',
    'disneyplus': 'disney.com',
    'hulu': 'hulu.com',
    'peacock': 'peacocktv.com',
    'paramount': 'paramount.com',
    'microsoft': 'microsoft.com',
    'adobe': 'adobe.com',
    'adobecreativecloud': 'adobe.com',
    'office365': 'microsoft.com',
    'google': 'google.com',
    'googleone': 'google.com',
    'dropbox': 'dropbox.com',
    'icloud': 'apple.com',
    'onedrive': 'microsoft.com',
  }
  
  const mappedDomain = domainMap[cleanName]
  const finalLogoUrl = mappedDomain ? `https://logo.clearbit.com/${mappedDomain}` : logoUrl
  
  if (imageError) {
    // Fallback to icon if image fails to load
    return (
      <div 
        className={`flex items-center justify-center bg-gray-200 rounded-lg flex-shrink-0 ${className}`}
        style={{ width: size, height: size }}
      >
        <Building2 size={size * 0.6} className="text-gray-500" />
      </div>
    )
  }
  
  return (
    <img
      src={finalLogoUrl}
      alt={companyName}
      className={`rounded-lg flex-shrink-0 ${className}`}
      style={{ width: size, height: size, objectFit: 'contain' }}
      onError={() => setImageError(true)}
      onLoad={() => setImageError(false)}
    />
  )
}

