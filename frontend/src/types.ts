export type Verdict = 'authentic' | 'manipulated' | 'synthetic' | 'uncertain'
export type AnalysisStatus = 'queued' | 'processing' | 'complete' | 'failed'

export interface Evidence { title: string; detail: string; severity: 'positive' | 'warning' | 'neutral' }
export interface Analysis {
  id: string
  filename: string
  mediaType: string
  createdAt: string
  status: AnalysisStatus
  verdict: Verdict
  confidence: number
  summary: string
  evidence: Evidence[]
  durationMs?: number
  isDemo?: boolean
  score?: number
  metadata?: Record<string, unknown>
}
