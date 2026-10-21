type DatasetOwnerProps = {
  owner: string
}

export function DatasetOwner({ owner }: DatasetOwnerProps) {
  return (
    <p className="flex flex-col gap-0.5">
      <span className="text-xs text-muted-foreground">Owner</span>
      <span className="text-sm">{owner || 'Unassigned'}</span>
    </p>
  )
}
