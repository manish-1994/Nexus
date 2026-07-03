import ReactMarkdown from 'react-markdown'

interface StreamingBubbleProps {
  content: string
}

export function StreamingBubble({ content }: StreamingBubbleProps) {
  return (
    <div className="whitespace-pre-wrap break-words leading-relaxed prose prose-sm max-w-none">
      <ReactMarkdown>{content}</ReactMarkdown>
      <span className="inline-block w-2 h-4 ml-1 bg-gray-800 streaming-cursor align-middle" />
    </div>
  )
}
