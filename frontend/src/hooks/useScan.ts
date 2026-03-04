import { useState, useCallback, useRef } from 'react'
import { ScanCheckProgress, ScanStatus } from '../types'
import { mockScanChecks, checkResults } from '../data/mockData'
import {
  startScan as apiStartScan,
  getScan as apiGetScan,
  getStoredAuth,
  type ScanResponse,
} from '../services/api'

const POLL_INTERVAL = 2000

export function useScan() {
  const [status, setStatus] = useState<ScanStatus>('idle')
  const [checks, setChecks] = useState<ScanCheckProgress[]>([])
  const [currentCheckIndex, setCurrentCheckIndex] = useState(-1)
  const [progress, setProgress] = useState(0)
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Real API scan
  const startApiScan = useCallback(async (awsAccountId?: string) => {
    const { accountId, selectedAwsAccountId } = getStoredAuth()
    const targetAwsId = awsAccountId || selectedAwsAccountId
    if (!accountId) {
      setError('No connected account. Please connect your AWS account first.')
      return
    }
    if (!targetAwsId) {
      setError('No AWS account selected. Please select an AWS account to scan.')
      return
    }

    setStatus('scanning')
    setError(null)
    setProgress(0)
    setChecks([])
    setScanResult(null)

    try {
      const { scan_id } = await apiStartScan(accountId, targetAwsId)

      // Poll for results
      pollingRef.current = setInterval(async () => {
        try {
          const scan = await apiGetScan(scan_id)

          if (scan.status === 'complete') {
            if (pollingRef.current) clearInterval(pollingRef.current)
            setScanResult(scan)
            setStatus('complete')
            setProgress(100)

            // Map findings to check progress format
            const mappedChecks: ScanCheckProgress[] = scan.findings.map((f) => ({
              id: f.id,
              checkName: f.checkName,
              resource: f.resource,
              status: f.status === 'pass' ? 'pass' as const
                    : f.status === 'info' ? 'info' as const
                    : f.status === 'review' ? 'warn' as const
                    : 'fail' as const,
              severity: f.severity as ScanCheckProgress['severity'],
              duration: Math.round(Math.random() * 1200 + 600),
            }))
            setChecks(mappedChecks)
            setCurrentCheckIndex(-1)

            // Store for findings page
            localStorage.setItem('konforme_last_scan', JSON.stringify(scan))
          } else if (scan.status === 'error') {
            if (pollingRef.current) clearInterval(pollingRef.current)
            setStatus('error')
            setError('Scan failed. Check your IAM role permissions.')
          } else {
            // Still running — animate progress
            setProgress(prev => Math.min(prev + 5, 90))
          }
        } catch (err) {
          if (pollingRef.current) clearInterval(pollingRef.current)
          setStatus('error')
          setError(err instanceof Error ? err.message : 'Failed to poll scan status')
        }
      }, POLL_INTERVAL)
    } catch (err) {
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Failed to start scan')
    }
  }, [])

  // Demo mock scan (no backend needed)
  const startDemoScan = useCallback(() => {
    setStatus('scanning')
    setError(null)
    setScanResult(null)
    setChecks(mockScanChecks.map(c => ({ ...c, status: 'pending' as const })))
    setCurrentCheckIndex(0)
    setProgress(0)

    let index = 0
    const total = mockScanChecks.length

    const runNextCheck = () => {
      if (index >= total) {
        setStatus('complete')
        setProgress(100)
        setCurrentCheckIndex(-1)
        return
      }

      const checkId = mockScanChecks[index].id
      setCurrentCheckIndex(index)
      setChecks(prev =>
        prev.map((c, i) => (i === index ? { ...c, status: 'scanning' as const } : c))
      )

      const duration = 600 + Math.random() * 1200
      timeoutRef.current = setTimeout(() => {
        const result = checkResults[checkId]
        setChecks(prev =>
          prev.map((c, i) =>
            i === index
              ? { ...c, status: result.status, severity: result.severity, duration: Math.round(duration) }
              : c
          )
        )
        setProgress(Math.round(((index + 1) / total) * 100))
        index++
        runNextCheck()
      }, duration)
    }
    runNextCheck()
  }, [])

  const startScan = useCallback(
    (mode: 'api' | 'demo' = 'api', awsAccountId?: string) => {
      if (mode === 'demo') {
        startDemoScan()
      } else {
        startApiScan(awsAccountId)
      }
    },
    [startApiScan, startDemoScan]
  )

  const resetScan = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    if (pollingRef.current) clearInterval(pollingRef.current)
    setStatus('idle')
    setChecks([])
    setCurrentCheckIndex(-1)
    setProgress(0)
    setScanResult(null)
    setError(null)
  }, [])

  return {
    status,
    checks,
    currentCheckIndex,
    progress,
    scanResult,
    error,
    startScan,
    resetScan,
  }
}
