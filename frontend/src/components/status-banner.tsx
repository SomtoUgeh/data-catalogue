import { Alert, AlertDescription } from '@/components/ui/alert'
import { cn } from '@/lib/utils'

type StatusBannerProps = {
  tone?: 'error' | 'warning'
  children: string
}

export function StatusBanner({ tone = 'error', children }: StatusBannerProps) {
  return (
    <Alert
      variant={tone === 'error' ? 'destructive' : 'default'}
      role={tone === 'error' ? 'alert' : 'status'}
      aria-live="polite"
      className={cn(
        tone === 'warning' &&
          'border-warning/40 bg-warning/20 text-warning-foreground *:data-[slot=alert-description]:text-warning-foreground',
      )}
    >
      <AlertDescription>{children}</AlertDescription>
    </Alert>
  )
}
