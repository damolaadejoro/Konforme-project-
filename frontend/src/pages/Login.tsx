import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield, LogIn, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { Card, Button, Input } from '../components/ui'

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

interface FieldErrors {
  email?: string
  password?: string
}

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const validateField = (field: string, value: string): string | undefined => {
    switch (field) {
      case 'email':
        if (!value.trim()) return 'Email is required'
        if (!EMAIL_REGEX.test(value)) return 'Please enter a valid email address'
        return undefined
      case 'password':
        if (!value) return 'Password is required'
        return undefined
      default:
        return undefined
    }
  }

  const handleBlur = (field: string, value: string) => {
    setTouched(prev => ({ ...prev, [field]: true }))
    setFieldErrors(prev => ({ ...prev, [field]: validateField(field, value) }))
  }

  const handleChange = (field: string, value: string, setter: (v: string) => void) => {
    setter(value)
    setServerError(null)
    if (touched[field]) {
      setFieldErrors(prev => ({ ...prev, [field]: validateField(field, value) }))
    }
  }

  const validate = (): boolean => {
    const errors: FieldErrors = {
      email: validateField('email', email),
      password: validateField('password', password),
    }
    setFieldErrors(errors)
    setTouched({ email: true, password: true })
    return !errors.email && !errors.password
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setServerError(null)

    if (!validate()) return

    setLoading(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setServerError(err instanceof Error ? err.message : 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500 to-cyan-700 mb-4">
            <Shield size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold font-syne text-white">Welcome back</h1>
          <p className="text-sm text-navy-400 mt-1">Sign in to your Konforme account</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <Input
              label="Email"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={e => handleChange('email', e.target.value, setEmail)}
              onBlur={() => handleBlur('email', email)}
              error={touched.email ? fieldErrors.email : undefined}
            />
            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                value={password}
                onChange={e => handleChange('password', e.target.value, setPassword)}
                onBlur={() => handleBlur('password', password)}
                error={touched.password ? fieldErrors.password : undefined}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-8 text-navy-400 hover:text-white transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            <div className="flex justify-end">
              <Link to="/reset-password" className="text-xs text-cyan-400 hover:text-cyan-300">
                Forgot password?
              </Link>
            </div>

            {serverError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                <p className="text-xs text-red-400">{serverError}</p>
              </div>
            )}

            <Button type="submit" size="lg" className="w-full" loading={loading}>
              <LogIn size={16} />
              Sign In
            </Button>
          </form>

          <p className="text-center text-sm text-navy-400 mt-4">
            Don't have an account?{' '}
            <Link to="/register" className="text-cyan-400 hover:text-cyan-300 font-medium">
              Register
            </Link>
          </p>
        </Card>
      </div>
    </div>
  )
}
