import { useState, useEffect, useCallback } from 'react'
import type { AssessmentVersionSummary } from '../types/assessment'
import { getAssessmentHistory, getAssessmentVersion, getStoredAuth, isConnected } from '../services/api'

export function useAssessmentHistory() {
  const [versions, setVersions] = useState<AssessmentVersionSummary[]>([])
  const [loading, setLoading] = useState(true)

  const fetchHistory = useCallback(async () => {
    if (!isConnected()) {
      setLoading(false)
      return
    }

    const { accountId } = getStoredAuth()
    if (!accountId) {
      setLoading(false)
      return
    }

    try {
      const data = await getAssessmentHistory(accountId)
      setVersions(data.versions)
    } catch (err) {
      console.error('Failed to fetch assessment history:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory])

  const loadVersion = useCallback(async (versionId: string) => {
    const { accountId } = getStoredAuth()
    if (!accountId) return null

    try {
      return await getAssessmentVersion(accountId, versionId)
    } catch (err) {
      console.error('Failed to load version:', err)
      return null
    }
  }, [])

  return {
    versions,
    loading,
    fetchHistory,
    loadVersion,
  }
}
