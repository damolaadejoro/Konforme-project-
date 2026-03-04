import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import {
  register as apiRegister,
  login as apiLogin,
  logout as apiLogout,
  getMe,
  addAwsAccount as apiAddAwsAccount,
  removeAwsAccount as apiRemoveAwsAccount,
  getAccountInfo,
  getStoredAuth,
  clearAuth,
  isAuthenticated as checkAuth,
  type AwsAccountInfo,
} from '../services/api'

interface AuthState {
  accountId: string | null
  accountName: string | null
  email: string | null
  isAuthenticated: boolean
  loading: boolean
  awsAccounts: AwsAccountInfo[]
  selectedAwsAccountId: string | null
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
  addAwsAccount: (alias: string, accessKeyId: string, secretAccessKey: string, sessionToken: string | null, region: string) => Promise<AwsAccountInfo>
  removeAwsAccount: (awsAccountId: string) => Promise<void>
  selectAwsAccount: (awsAccountId: string) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState>(() => {
    const stored = getStoredAuth()
    return {
      accountId: stored.accountId,
      accountName: stored.accountName,
      email: stored.email,
      isAuthenticated: checkAuth(),
      loading: true,
      awsAccounts: stored.awsAccounts,
      selectedAwsAccountId: stored.selectedAwsAccountId,
    }
  })

  // On init, verify session by calling /auth/me (uses httpOnly cookie)
  useEffect(() => {
    getMe()
      .then(info => {
        localStorage.setItem('konforme_account_id', info.account_id)
        localStorage.setItem('konforme_account_name', info.account_name)
        localStorage.setItem('konforme_email', info.email)
        setAuth(prev => ({
          ...prev,
          accountId: info.account_id,
          accountName: info.account_name,
          email: info.email,
          isAuthenticated: true,
          loading: false,
        }))
        // Hydrate AWS accounts
        getAccountInfo()
          .then(acctInfo => {
            const awsAccounts: AwsAccountInfo[] = acctInfo.aws_accounts.map(a => ({
              id: a.id,
              alias: a.alias,
              awsAccountId: a.aws_account_id,
              awsRegion: a.aws_region,
              isActive: a.is_active,
              addedAt: a.added_at,
            }))
            localStorage.setItem('konforme_aws_accounts', JSON.stringify(awsAccounts))
            setAuth(prev => ({
              ...prev,
              awsAccounts,
              selectedAwsAccountId: prev.selectedAwsAccountId && awsAccounts.some(a => a.id === prev.selectedAwsAccountId)
                ? prev.selectedAwsAccountId
                : awsAccounts.length > 0 ? awsAccounts[0].id : null,
            }))
          })
          .catch(() => { /* ignore */ })
      })
      .catch(() => {
        // No valid session — clear local state
        clearAuth()
        setAuth({
          accountId: null, accountName: null, email: null,
          isAuthenticated: false, loading: false, awsAccounts: [], selectedAwsAccountId: null,
        })
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const loginFn = useCallback(async (email: string, password: string) => {
    const previousAccountId = auth.accountId
    const data = await apiLogin(email, password)

    if (previousAccountId && previousAccountId !== data.account_id) {
      window.location.href = '/'
      return
    }

    setAuth({
      accountId: data.account_id,
      accountName: data.account_name,
      email: data.email,
      isAuthenticated: true,
      loading: false,
      awsAccounts: [],
      selectedAwsAccountId: null,
    })
    // Hydrate AWS accounts
    try {
      const info = await getAccountInfo()
      const awsAccounts: AwsAccountInfo[] = info.aws_accounts.map(a => ({
        id: a.id, alias: a.alias, awsAccountId: a.aws_account_id,
        awsRegion: a.aws_region, isActive: a.is_active, addedAt: a.added_at,
      }))
      localStorage.setItem('konforme_aws_accounts', JSON.stringify(awsAccounts))
      setAuth(prev => ({
        ...prev,
        awsAccounts,
        selectedAwsAccountId: awsAccounts.length > 0 ? awsAccounts[0].id : null,
      }))
    } catch { /* ignore */ }
  }, [auth.accountId])

  const registerFn = useCallback(async (name: string, email: string, password: string) => {
    const previousAccountId = auth.accountId
    const data = await apiRegister(name, email, password)

    if (previousAccountId && previousAccountId !== data.account_id) {
      window.location.href = '/'
      return
    }

    setAuth({
      accountId: data.account_id,
      accountName: data.account_name,
      email: data.email,
      isAuthenticated: true,
      loading: false,
      awsAccounts: [],
      selectedAwsAccountId: null,
    })
  }, [auth.accountId])

  const logoutFn = useCallback(async () => {
    await apiLogout()
    window.location.href = '/login'
  }, [])

  const addAwsAccount = useCallback(async (alias: string, accessKeyId: string, secretAccessKey: string, sessionToken: string | null, region: string) => {
    const newAcc = await apiAddAwsAccount(alias, accessKeyId, secretAccessKey, sessionToken, region)
    setAuth(prev => ({
      ...prev,
      awsAccounts: [...prev.awsAccounts, newAcc],
      selectedAwsAccountId: prev.selectedAwsAccountId || newAcc.id,
    }))
    return newAcc
  }, [])

  const removeAwsAccount = useCallback(async (awsAccountId: string) => {
    await apiRemoveAwsAccount(awsAccountId)
    setAuth(prev => {
      const updated = prev.awsAccounts.filter(a => a.id !== awsAccountId)
      return {
        ...prev,
        awsAccounts: updated,
        selectedAwsAccountId: prev.selectedAwsAccountId === awsAccountId
          ? (updated.length > 0 ? updated[0].id : null)
          : prev.selectedAwsAccountId,
      }
    })
  }, [])

  const selectAwsAccount = useCallback((awsAccountId: string) => {
    localStorage.setItem('konforme_selected_aws_account_id', awsAccountId)
    setAuth(prev => ({ ...prev, selectedAwsAccountId: awsAccountId }))
  }, [])

  return (
    <AuthContext.Provider value={{
      ...auth,
      login: loginFn,
      register: registerFn,
      logout: logoutFn,
      addAwsAccount,
      removeAwsAccount,
      selectAwsAccount,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
