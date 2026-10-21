export type Dataset = {
  id: string
  name: string
  owner: string
  description: string
  tags: string[]
  summary: string
  curation_status: 'ok' | 'failed'
}

export type NewDataset = Pick<Dataset, 'name' | 'owner' | 'description'>
