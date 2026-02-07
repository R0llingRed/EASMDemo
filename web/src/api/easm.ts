import { apiClient } from './client'

export interface Page<T> {
  total: number
  items: T[]
}

export interface Project {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface Asset {
  id: string
  project_id: string
  asset_type: 'domain' | 'ip' | 'url'
  value: string
  source: string | null
  first_seen: string
  last_seen: string
}

export interface AssetImportResult {
  inserted: number
  skipped: number
  total: number
}

export interface ScanTask {
  id: string
  project_id: string
  scan_policy_id: string | null
  task_type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  priority: number
  progress: number
  total_targets: number
  completed_targets: number
  config: Record<string, unknown>
  result_summary: Record<string, unknown>
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface Vulnerability {
  id: string
  project_id: string
  target_url: string
  template_id: string
  severity: string
  title: string | null
  status: string
  scanner: string
  is_false_positive: boolean
  first_seen: string
  last_seen: string
}

export interface VulnerabilityStats {
  total: number
  critical: number
  high: number
  medium: number
  low: number
  info: number
  open: number
  confirmed: number
  fixed: number
  false_positive: number
}

export interface ApiRisk {
  id: string
  project_id: string
  endpoint_id: string | null
  rule_name: string
  severity: string
  title: string
  description: string | null
  evidence: Record<string, unknown>
  status: string
  updated_by: string | null
  resolution_notes: string | null
  status_history: Array<Record<string, unknown>>
  created_at: string
  updated_at: string
  resolved_at: string | null
}

export interface RiskScore {
  id: string
  project_id: string
  asset_type: string
  asset_id: string
  total_score: number
  severity_level: string
  factor_scores: Record<string, unknown>
  risk_summary: Record<string, unknown>
  calculated_at: string
  expires_at: string | null
  created_at: string
}

export interface AlertRecord {
  id: string
  project_id: string
  policy_id: string | null
  target_type: string
  title: string
  message: string
  severity: string
  status: string
  created_at: string
}

export async function getHealth(): Promise<{ status: string }> {
  const { data } = await apiClient.get('/health')
  return data
}

export async function listProjects(): Promise<Page<Project>> {
  const { data } = await apiClient.get<Page<Project>>('/projects', {
    params: { offset: 0, limit: 200 },
  })
  return data
}

export async function createProject(payload: {
  name: string
  description?: string
}): Promise<Project> {
  const { data } = await apiClient.post<Project>('/projects', payload)
  return data
}

export async function listAssets(projectId: string, params?: {
  asset_type?: 'domain' | 'ip' | 'url'
  offset?: number
  limit?: number
}): Promise<Page<Asset>> {
  const { data } = await apiClient.get<Page<Asset>>(`/projects/${projectId}/assets`, {
    params,
  })
  return data
}

export async function importAssets(
  projectId: string,
  assets: Array<{ asset_type: 'domain' | 'ip' | 'url'; value: string; source?: string }>,
): Promise<AssetImportResult> {
  const { data } = await apiClient.post<AssetImportResult>(
    `/projects/${projectId}/assets/import`,
    { assets },
  )
  return data
}

export async function listScans(projectId: string, params?: {
  task_type?: string
  status?: string
  skip?: number
  limit?: number
}): Promise<Page<ScanTask>> {
  const { data } = await apiClient.get<Page<ScanTask>>(`/projects/${projectId}/scans`, {
    params,
  })
  return data
}

export async function createScan(
  projectId: string,
  payload: {
    task_type: string
    policy_id?: string | null
    config?: Record<string, unknown>
    priority?: number
  },
): Promise<ScanTask> {
  const { data } = await apiClient.post<ScanTask>(`/projects/${projectId}/scans`, payload)
  return data
}

export async function startScan(projectId: string, taskId: string): Promise<ScanTask> {
  const { data } = await apiClient.post<ScanTask>(`/projects/${projectId}/scans/${taskId}/start`)
  return data
}

export async function listVulnerabilities(projectId: string, params?: {
  severity?: string
  status?: string
  skip?: number
  limit?: number
}): Promise<Page<Vulnerability>> {
  const { data } = await apiClient.get<Page<Vulnerability>>(
    `/projects/${projectId}/vulnerabilities`,
    { params },
  )
  return data
}

export async function getVulnerabilityStats(projectId: string): Promise<VulnerabilityStats> {
  const { data } = await apiClient.get<VulnerabilityStats>(
    `/projects/${projectId}/vulnerabilities/stats`,
  )
  return data
}

export async function listApiRisks(projectId: string, params?: {
  severity?: string
  status?: string
  skip?: number
  limit?: number
}): Promise<Page<ApiRisk>> {
  const { data } = await apiClient.get<Page<ApiRisk>>(`/projects/${projectId}/api-risks`, {
    params,
  })
  return data
}

export async function listRiskScores(projectId: string, params?: {
  severity_level?: string
  skip?: number
  limit?: number
}): Promise<Page<RiskScore>> {
  const { data } = await apiClient.get<Page<RiskScore>>(`/projects/${projectId}/risk/scores`, {
    params,
  })
  return data
}

export async function listAlerts(projectId: string, params?: {
  status?: string
  severity?: string
  skip?: number
  limit?: number
}): Promise<Page<AlertRecord>> {
  const { data } = await apiClient.get<Page<AlertRecord>>(`/projects/${projectId}/alerts`, {
    params,
  })
  return data
}
