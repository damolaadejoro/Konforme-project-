import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { KeyRound, Eye, EyeOff, CheckCircle } from 'lucide-react'
import { resetPassword } from '../services/api'
import { Card, Button, Input } from '../components/ui'
import Logo from '../components/layout/Logo'

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

interface FieldErrors {
  email?: string
  newPassword?: string
  confirmPassword?: string
}

export default function ResetPassword() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const validateField = (field: string, value: string): string | undefined => {
    switch (field) {
      case 'email':
        if (!value.trim()) return 'Email is required'
        if (!EMAIL_REGEX.test(value)) return 'Please enter a valid email address'
        return undefined
      case 'newPassword':
        if (!value) return 'New password is required'
        if (value.length < 8) return 'Password must be at least 8 characters'
        if (!/[A-Z]/.test(value)) return 'Password must include an uppercase letter'
        if (!/[a-z]/.test(value)) return 'Password must include a lowercase letter'
        if (!/[0-9]/.test(value)) return 'Password must include a number'
        return undefined
      case 'confirmPassword':
        if (!value) return 'Please confirm your new password'
        if (value !== newPassword) return 'Passwords do not match'
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
    if (field === 'newPassword' && touched.confirmPassword && confirmPassword) {
      setFieldErrors(prev => ({
        ...prev,
        confirmPassword: value !== confirmPassword ? 'Passwords do not match' : undefined,
      }))
    }
  }

  const validate = (): boolean => {
    const errors: FieldErrors = {
      email: validateField('email', email),
      newPassword: validateField('newPassword', newPassword),
      confirmPassword: validateField('confirmPassword', confirmPassword),
    }
    setFieldErrors(errors)
    setTouched({ email: true, newPassword: true, confirmPassword: true })
    return !errors.email && !errors.newPassword && !errors.confirmPassword
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setServerError(null)

    if (!validate()) return

    setLoading(true)
    try {
      await resetPassword(email, newPassword)
      setSuccess(true)
    } catch (err) {
      setServerError(err instanceof Error ? err.message : 'Failed to reset password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-navy-950 flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <Card>
            <div className="text-center py-4">
              <CheckCircle size={48} className="text-emerald-400 mx-auto mb-4" />
              <h2 className="text-lg font-bold font-syne text-white mb-2">Password Reset</h2>
              <p className="text-sm text-navy-400 mb-6">
                If an account with that email exists, the password has been updated. You can now sign in with your new password.
              </p>
              <Button onClick={() => navigate('/login')} size="lg" className="w-full">
                Go to Sign In
              </Button>
            </div>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center mb-4">
            <Logo size="lg" showText={false} />
          </div>
          <h1 className="text-2xl font-bold font-syne text-white">Reset Password</h1>
          <p className="text-sm text-navy-400 mt-1">Enter your email and a new password</p>
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
                label="New Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="At least 8 characters"
                value={newPassword}
                onChange={e => handleChange('newPassword', e.target.value, setNewPassword)}
                onBlur={() => handleBlur('newPassword', newPassword)}
                error={touched.newPassword ? fieldErrors.newPassword : undefined}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-8 text-navy-400 hover:text-white transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <div className="relative">
              <Input
                label="Confirm New Password"
                type={showConfirm ? 'text' : 'password'}
                placeholder="Repeat your new password"
                value={confirmPassword}
                onChange={e => handleChange('confirmPassword', e.target.value, setConfirmPassword)}
                onBlur={() => handleBlur('confirmPassword', confirmPassword)}
                error={touched.confirmPassword ? fieldErrors.confirmPassword : undefined}
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-3 top-8 text-navy-400 hover:text-white transition-colors"
              >
                {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {serverError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                <p className="text-xs text-red-400">{serverError}</p>
              </div>
            )}

            <Button type="submit" size="lg" className="w-full" loading={loading}>
              <KeyRound size={16} />
              Reset Password
            </Button>
          </form>

          <p className="text-center text-sm text-navy-400 mt-4">
            Remember your password?{' '}
            <Link to="/login" className="text-cyan-400 hover:text-cyan-300 font-medium">
              Sign in
            </Link>
          </p>
        </Card>
      </div>
    </div>
  )
}
