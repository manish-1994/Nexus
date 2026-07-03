import { useRef, useState, useEffect, useCallback } from 'react'

export function useAutoScroll(dependencies: unknown[]) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const userHasScrolledUp = useRef(false)
  const [showScrollButton, setShowScrollButton] = useState(false)

  const handleScroll = useCallback(() => {
    const el = containerRef.current
    if (!el) return
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    userHasScrolledUp.current = distanceFromBottom > 150
    setShowScrollButton(distanceFromBottom > 300)
  }, [])

  useEffect(() => {
    if (!userHasScrolledUp.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies)

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    userHasScrolledUp.current = false
    setShowScrollButton(false)
  }, [])

  return {
    containerRef,
    bottomRef,
    handleScroll,
    showScrollButton,
    scrollToBottom
  }
}
