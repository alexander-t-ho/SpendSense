/**
 * Color Palette Constants
 * 
 * Based on the provided color palette:
 * 1. Muted olive green (dark) - Primary dark accent
 * 2. Light pastel green - Light accent/secondary
 * 3. Pure white - Clean backgrounds
 * 4. Light warm tan/beige - Primary background
 * 5. Dark rich brown - Dark text/accents
 */

export const colors = {
  // Primary palette
  oliveGreen: {
    dark: '#556B2F',      // Muted olive green (dark)
    DEFAULT: '#6B7A3C',   // Medium olive green
    light: '#8B9A5B',     // Light olive green
  },
  pastelGreen: {
    dark: '#C8E6C9',      // Medium pastel green
    DEFAULT: '#E8F5E9',   // Light pastel green
    light: '#F1F8E9',     // Very light pastel green
  },
  white: '#FFFFFF',
  beige: {
    dark: '#D4C4B0',      // Medium beige
    DEFAULT: '#F5E6D3',   // Light warm tan/beige
    light: '#FAF5F0',     // Very light beige
  },
  brown: {
    light: '#8B6F47',     // Medium brown
    DEFAULT: '#5D4037',   // Dark rich brown
    dark: '#3E2723',      // Very dark brown
  },
}

// Tailwind class mappings for consistency
export const tailwindColors = {
  // Backgrounds
  bgPrimary: 'bg-[#F5E6D3]',           // Light warm tan/beige
  bgSecondary: 'bg-white',              // Pure white
  bgAccent: 'bg-[#E8F5E9]',            // Light pastel green
  bgDark: 'bg-[#556B2F]',              // Muted olive green (dark)
  bgBrown: 'bg-[#5D4037]',             // Dark rich brown
  
  // Text colors
  textPrimary: 'text-[#5D4037]',       // Dark rich brown
  textSecondary: 'text-[#556B2F]',     // Muted olive green
  textLight: 'text-[#8B6F47]',         // Medium brown
  textWhite: 'text-white',
  
  // Borders
  borderPrimary: 'border-[#D4C4B0]',   // Medium beige
  borderAccent: 'border-[#556B2F]',    // Muted olive green
  borderLight: 'border-[#F5E6D3]',     // Light beige
  
  // Accent colors
  accentPrimary: '#556B2F',            // Muted olive green
  accentSecondary: '#E8F5E9',          // Light pastel green
  accentBrown: '#5D4037',              // Dark rich brown
}



