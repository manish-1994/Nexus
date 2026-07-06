import { useRef, useState, useEffect, useCallback } from 'react'

/**
 * Auto-scroll hook for the chat message list.
 *
 * Smoothly scrolls to the newest content when:
 *   - the user sends a message
 *   - the first streamed token arrives
 *   - new streamed tokens arrive
 *   - generation completes
 *
 * Never jumps (always `behavior: 'smooth'`) and never overscrolls — it scrolls
 * to the bottom sentinel, not past it. If the user has manually scrolled up to
 * read history, auto-scroll is suspended until they either scroll back down or
 * click the scroll-to-bottom button.
 *
 * @param dependencies - Values that, when changed, trigger an auto-scroll
 *                       check (e.g. the messages array or its length).
 */
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

  // Smooth scroll to the bottom sentinel. Uses `block: 'end'` so the sentinel
  // aligns to the bottom of the scrollport without overshooting.
  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    userHasScrolledUp.current = false
    setShowScrollButton(false)
  }, [])

  // Trigger an auto-scroll check whenever the dependencies change. This fires
  // on send, on each streamed token (messages array mutates), and on
  // completion. We only scroll if the user hasn't scrolled away from the
  // bottom, preserving their reading position.
  useEffect(() => {
    if (!userHasScrolledUp.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies)

  return {
    containerRef,
    bottomRef,
    handleScroll,
    showScrollButton,
    scrollToBottom,
  }
}
