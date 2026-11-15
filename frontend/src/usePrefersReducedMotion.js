import { useEffect, useState } from 'react'

const QUERY = '(prefers-reduced-motion: reduce)'

export default function usePrefersReducedMotion() {
  const [reducedMotion, setReducedMotion] = useState(() => (
    typeof window !== 'undefined' && window.matchMedia?.(QUERY).matches === true
  ))

  useEffect(() => {
    if (!window.matchMedia) return undefined
    const mediaQuery = window.matchMedia(QUERY)
    const updatePreference = (event) => setReducedMotion(event.matches)
    mediaQuery.addEventListener?.('change', updatePreference)
    return () => mediaQuery.removeEventListener?.('change', updatePreference)
  }, [])

  return reducedMotion
}
