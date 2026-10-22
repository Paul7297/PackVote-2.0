export function Notice({
  children,
  tone = 'error',
}: {
  children: string
  tone?: 'error' | 'success' | 'info'
}) {
  return (
    <div className={`notice notice--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  )
}
