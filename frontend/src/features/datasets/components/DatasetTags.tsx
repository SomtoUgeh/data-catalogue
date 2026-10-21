import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

type DatasetTagsProps = {
  tags: string[]
}

function isPiiTag(tag: string): boolean {
  return tag.toLowerCase() === 'pii'
}

export function DatasetTags({ tags }: DatasetTagsProps) {
  if (tags.length === 0) return null
  return (
    <p className="flex flex-wrap gap-1.5">
      <span className="sr-only">Tags: {tags.join(', ')}</span>
      {tags.map((tag) => (
        <Badge
          key={tag}
          variant="secondary"
          className={cn(isPiiTag(tag) && 'bg-warning text-warning-foreground')}
        >
          {tag}
        </Badge>
      ))}
    </p>
  )
}
