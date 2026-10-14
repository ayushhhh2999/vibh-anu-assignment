import { Check, CircleDot, Clock3 } from 'lucide-react'
import { cn } from '../../lib/utils'
import { statusLabel } from '../../lib/utils'

export function StatusBadge({ status }: { status?: string | null }) {
  const normalized = status ?? 'unknown'
  const tone = normalized === 'claimed' ? 'status-claimed' : normalized === 'sales' ? 'status-sales' : normalized === 'support' ? 'status-support' : normalized === 'vigilance' ? 'status-vigilance' : 'status-communication'
  return <span className={cn('status-badge', tone)}><CircleDot size={11} strokeWidth={2.6} />{statusLabel(status)}</span>
}

export function WorkflowRail({ current }: { current?: string | null }) {
  const steps = ['communication', 'vigilance', 'support', 'sales', 'claimed']
  const currentIndex = Math.max(0, steps.indexOf(current ?? 'communication'))
  return <div className="workflow-rail" aria-label="Lead workflow progress">{steps.map((step, index) => <div className={cn('workflow-step', index <= currentIndex && 'workflow-step-active')} key={step}><span className="workflow-dot">{index < currentIndex ? <Check size={11} /> : <span>{index + 1}</span>}</span><span>{statusLabel(step)}</span>{index < steps.length - 1 && <span className="workflow-connector" />}</div>)}</div>
}
