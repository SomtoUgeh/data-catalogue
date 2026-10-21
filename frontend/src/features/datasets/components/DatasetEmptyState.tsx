import { Card, CardContent } from '@/components/ui/card'

export function DatasetEmptyState() {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center gap-1 py-12 text-center">
        <p className="font-medium">No datasets registered yet.</p>
        <p className="text-sm text-muted-foreground">
          Add a name and description on the left to create the first entry.
        </p>
      </CardContent>
    </Card>
  )
}
