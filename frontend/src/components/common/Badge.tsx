interface BadgeProps {
  children: React.ReactNode
  color?: 'gray' | 'red' | 'yellow' | 'green' | 'blue' | 'indigo' | 'purple' | 'pink'
}

const colorClasses: Record<string, string> = {
  gray: 'badge-neutral',
  red: 'badge-danger',
  yellow: 'badge-warning',
  green: 'badge-success',
  blue: 'badge-accent',
  indigo: 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 inline-flex items-center px-2 py-0.5 rounded-button text-xs font-medium',
  purple: 'badge-secondary',
  pink: 'bg-pink-500/15 text-pink-300 border border-pink-500/30 inline-flex items-center px-2 py-0.5 rounded-button text-xs font-medium',
}

export function Badge({ children, color = 'gray' }: BadgeProps) {
  return (
    <span className={colorClasses[color]}>
      {children}
    </span>
  )
}