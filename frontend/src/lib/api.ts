import { config } from './config'
import { supabase } from './supabase'
import type { Analysis } from '../types'

function normalize(data: unknown): Analysis {
  const value = data as Record<string, unknown>
  const label = value.label === 'insufficient_evidence' ? 'uncertain' : value.label
  return {
    id: String(value.id ?? value.analysis_id),
    filename: String(value.filename ?? 'Uploaded file'),
    mediaType: `application/${String(value.modality ?? 'octet-stream')}`,
    createdAt: String(value.created_at ?? new Date().toISOString()),
    status: value.status === 'failed' ? 'failed' : 'complete',
    verdict: label === 'authentic' || label === 'manipulated' || label === 'synthetic' ? label : 'uncertain',
    confidence: typeof value.confidence === 'number' ? value.confidence : 0,
    summary: String(value.summary ?? value.explanation ?? 'No explanation was returned.'),
    evidence: Array.isArray(value.evidence) ? value.evidence.map((item) => {
      const evidence = item as Record<string, unknown>
      return { title: String(evidence.signal ?? 'Model signal'), detail: String(evidence.description ?? ''), severity: evidence.severity === 'low' ? 'neutral' : 'warning' }
    }) : [],
    isDemo: Boolean(value.is_development_inference),
  }
}

async function authHeaders(): Promise<HeadersInit> {
  const { data } = supabase ? await supabase.auth.getSession() : { data: { session: null } }
  return data.session?.access_token ? { Authorization: `Bearer ${data.session.access_token}` } : {}
}

export async function listAnalyses(): Promise<Analysis[]> {
  const response = await fetch(`${config.apiBaseUrl}/api/history`, { headers: await authHeaders() })
  if (!response.ok) throw new Error(`Unable to load analyses (${response.status})`)
  const data = await response.json()
  return (Array.isArray(data) ? data : data.items).map(normalize)
}

export async function getAnalysis(id: string): Promise<Analysis> {
  const response = await fetch(`${config.apiBaseUrl}/api/analysis/${encodeURIComponent(id)}`, { headers: await authHeaders() })
  if (!response.ok) throw new Error(`Unable to load analysis (${response.status})`)
  return normalize(await response.json())
}

export async function createAnalysis(file: File, context: string): Promise<Analysis> {
  const body = new FormData()
  body.append('file', file)
  if (context.trim()) body.append('context', context.trim())
  const response = await fetch(`${config.apiBaseUrl}/api/upload`, { method: 'POST', body, headers: await authHeaders() })
  if (!response.ok) throw new Error(`Analysis request failed (${response.status})`)
  const data = await response.json()
  return normalize(data.analysis_id ? await getAnalysis(data.analysis_id) : data)
}

export async function transcribeAudio(file: File): Promise<string> {
  const body = new FormData()
  body.append('file', file)
  const response = await fetch(`${config.apiBaseUrl}/api/transcribe`, { method: 'POST', body, headers: await authHeaders() })
  if (!response.ok) throw new Error(`Transcription request failed (${response.status})`)
  const data = await response.json() as { text?: string }
  return data.text || ''
}
