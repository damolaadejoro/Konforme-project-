import { useState, useCallback, useRef } from 'react'
import { ScanCheckProgress, ScanStatus, AWSCredentials } from '../types'
import { mockScanChecks, checkResults } from '../data/mockData'

export function useScan() {
  const [status, setStatus] = useState<ScanStatus>('idle')
  const [checks, setChecks] = useState<ScanCheckProgress[]>([])
  const [currentCheckIndex, setCurrentCheckIndex] = useState(-1)
  const [progress, setProgress] = useState(0)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const startScan = useCallback((_credentials: AWSCredentials) => {
    setStatus('scanning')
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

      // Set current check to "scanning"
      setCurrentCheckIndex(index)
      setChecks(prev =>
        prev.map((c, i) =>
          i === index ? { ...c, status: 'scanning' as const } : c
        )
      )

      // Simulate scan duration (600-1800ms)
      const duration = 600 + Math.random() * 1200

      timeoutRef.current = setTimeout(() => {
        const result = checkResults[checkId]
        setChecks(prev =>
          prev.map((c, i) =>
            i === index
              ? {
                  ...c,
                  status: result.status,
                  severity: result.severity,
                  duration: Math.round(duration),
                }
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

  const resetScan = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    setStatus('idle')
    setChecks([])
    setCurrentCheckIndex(-1)
    setProgress(0)
  }, [])

  return { status, checks, currentCheckIndex, progress, startScan, resetScan }
}
