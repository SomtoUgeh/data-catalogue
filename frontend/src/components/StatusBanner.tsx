type StatusBannerProps = {
  tone?: 'error' | 'warning'
  children: string
}

export function StatusBanner({ tone = 'error', children }: StatusBannerProps) {
  return (
    <p className={`banner banner-${tone}`} role={tone === 'error' ? 'alert' : 'status'} aria-live="polite">
      {children}
    </p>
  )
}
