import React from 'react'
import { Settings as SettingsIcon, Bell, Shield, Database, Key, Globe, User } from 'lucide-react'
import { Card, Button, Input, Select } from '../components/ui'

export default function Settings() {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-syne text-white">Settings</h1>
        <p className="text-sm text-navy-300 mt-1">Configure your Konforme workspace</p>
      </div>

      {/* Profile */}
      <Card>
        <div className="flex items-center gap-3 mb-5">
          <User size={16} className="text-cyan-400" />
          <h2 className="text-base font-bold font-syne text-white">Account</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input label="Organisation Name" defaultValue="Acme GmbH" />
          <Input label="Contact Email" defaultValue="security@acme.eu" />
        </div>
        <div className="mt-4">
          <Button size="sm">Save Changes</Button>
        </div>
      </Card>

      {/* Notifications */}
      <Card>
        <div className="flex items-center gap-3 mb-5">
          <Bell size={16} className="text-cyan-400" />
          <h2 className="text-base font-bold font-syne text-white">Notifications</h2>
        </div>
        <div className="space-y-3">
          {[
            { label: 'Critical findings alert', desc: 'Notify immediately when critical findings are detected' },
            { label: 'Weekly compliance digest', desc: 'Weekly summary of compliance status' },
            { label: 'Score below threshold', desc: 'Alert when score drops below 50%' },
          ].map(item => (
            <div key={item.label} className="flex items-center justify-between p-3 rounded-lg bg-navy-900/40 border border-navy-800">
              <div>
                <p className="text-sm font-medium text-white">{item.label}</p>
                <p className="text-xs text-navy-400 mt-0.5">{item.desc}</p>
              </div>
              <button className="w-10 h-5 rounded-full bg-cyan-500 relative cursor-pointer">
                <div className="absolute right-0.5 top-0.5 w-4 h-4 bg-white rounded-full" />
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* Compliance */}
      <Card>
        <div className="flex items-center gap-3 mb-5">
          <Shield size={16} className="text-cyan-400" />
          <h2 className="text-base font-bold font-syne text-white">Compliance Settings</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Primary Framework"
            options={[
              { value: 'nis2', label: 'NIS2 (EU 2022/2555)' },
              { value: 'iso27001', label: 'ISO 27001' },
              { value: 'soc2', label: 'SOC 2 Type II' },
            ]}
          />
          <Select
            label="Scan Schedule"
            options={[
              { value: 'daily', label: 'Daily' },
              { value: 'weekly', label: 'Weekly' },
              { value: 'monthly', label: 'Monthly' },
              { value: 'manual', label: 'Manual only' },
            ]}
          />
        </div>
      </Card>

      {/* Version */}
      <div className="text-center text-xs text-navy-600 py-4">
        Konforme v1.0.0 · Built for NIS2 compliance · © 2024 Konforme
      </div>
    </div>
  )
}
