import { memo, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface StreamingBubbleProps {
  content: string;
}

/**
 * Renders streamed assistant text with a blinking cursor at the end.
 *
 * The content is rendered through ReactMarkdown so partial markdown still
 * formats correctly. A blinking cursor element is appended after the markdown
 * output and disappears once streaming completes (handled by the parent
 * switching away from the `generating` status).
 *
 * Performance: memoized so it only re-renders when `content` actually changes.
 * No internal timers that would cause unnecessary re-renders — the cursor
 * blink is pure CSS.
 */
export const StreamingBubble = memo(function StreamingBubble({ content }: StreamingBubbleProps) {
  const prevLenRef = useRef(0);
  const [justAppended, setJustAppended] = useState(false);

  // Briefly highlight newly appended characters without re-animating the
  // whole bubble. Only flags when content grows; resets on the next tick.
  useEffect(() => {
    if (content.length > prevLenRef.current) {
      setJustAppended(true);
      const t = setTimeout(() => setJustAppended(false), 120);
      prevLenRef.current = content.length;
      return () => clearTimeout(t);
    }
    prevLenRef.current = content.length;
  }, [content]);

  return (
    <div className="whitespace-pre-wrap break-words leading-relaxed prose prose-invert prose-sm max-w-none">
      <span
        style={
          justAppended
            ? { animation: 'fade-in 0.12s ease-out both' }
            : undefined
        }
      >
        <ReactMarkdown>{content}</ReactMarkdown>
      </span>
      <span className="streaming-cursor" aria-hidden="true" />
    </div>
  );
});
