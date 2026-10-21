import { Alert, AlertDescription } from '@/components/ui/alert'
import { cn } from '@/lib/utils'

type StatusBannerProps = {
  tone?: 'error' | 'warning'
  children: string
}

/**
 * A styled message with no live-region role. To announce it, render it inside a container that is
 * always in the DOM with role="alert" or role="status". Screen readers can miss a live region that
 * is added together with its content.
 */
export function StatusBanner({ tone = 'error', children }: StatusBannerProps) {
  return (
    <Alert
      // The shadcn Alert sets role="alert". Undefined removes it.
      role={undefined}
      variant={tone === 'error' ? 'destructive' : 'default'}
      className={cn(
        tone === 'warning' &&
          'border-warning/40 bg-warning/20 text-warning-foreground *:data-[slot=alert-description]:text-warning-foreground',
      )}
    >
      <AlertDescription>{children}</AlertDescription>
    </Alert>
  )
}
