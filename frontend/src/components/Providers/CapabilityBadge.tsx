import { Badge } from '../common/Badge';

interface CapabilityBadgeProps {
  capability: string;
  supported: boolean;
}

const CAPABILITY_LABELS: Record<string, string> = {
  streaming: 'Streaming',
  vision: 'Vision',
  embeddings: 'Embeddings',
  tools: 'Tools',
  images: 'Images',
  audio: 'Audio',
  reasoning: 'Reasoning',
};

export function CapabilityBadge({ capability, supported }: CapabilityBadgeProps) {
  const label = CAPABILITY_LABELS[capability] || capability;
  return <Badge color={supported ? 'green' : 'gray'}>{label}</Badge>;
}
