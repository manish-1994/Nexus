interface ErrorMessageProps {
  message: string
  className?: string
}

function ErrorMessage({ message, className = '' }: ErrorMessageProps) {
  return (
    <div className={`rounded-card bg-danger/10 border border-danger/30 p-4 ${className}`}>
      <div className="flex">
        <div className="ml-3">
          <h3 className="text-sm font-medium text-danger">Error</h3>
          <div className="mt-2 text-sm text-danger/80">
            <p>{message}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ErrorMessage