export type CurationStatus = 'ok' | 'failed'

export interface Dataset {
  id: string
  name: string
  owner: string
  description: string
  tags: string[]
  summary: string
  curation_status: CurationStatus
}

export interface DatasetInput {
  name: string
  owner: string
  description: string
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}
