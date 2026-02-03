'use client';

import { useState, useEffect } from 'react';
import MainLayout from '@/components/layout/MainLayout';
import { apiFetch } from '@/lib/api';
import { TrashIcon, PlusIcon, BellIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

interface AlertSettings {
  setting_id: number;
  schedule_frequency: 'immediate' | 'hourly' | 'daily' | 'weekly';
  schedule_time: string;
  schedule_day: number | null;
  enabled: boolean;
  last_alert_sent_at: string | null;
  created_at: string;
  updated_at: string;
}

interface AlertEmail {
  email_id: number;
  email: string;
  verified: boolean;
  created_at: string;
}

export default function PriceChangePage() {
  // State
  const [settings, setSettings] = useState<AlertSettings | null>(null);
  const [emails, setEmails] = useState<AlertEmail[]>([]);
  const [newEmail, setNewEmail] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSendingTest, setIsSendingTest] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [emailError, setEmailError] = useState('');

  // Fetch data on mount
  useEffect(() => {
    fetchSettings();
    fetchEmails();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await apiFetch('/api/price-alerts/settings');
      if (!response.ok) throw new Error('Failed to fetch settings');
      const data = await response.json();
      setSettings(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchEmails = async () => {
    try {
      const response = await apiFetch('/api/price-alerts/emails');
      if (!response.ok) throw new Error('Failed to fetch emails');
      const data = await response.json();
      setEmails(data);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleScheduleChange = (field: keyof AlertSettings, value: any) => {
    if (settings) {
      setSettings({ ...settings, [field]: value });
    }
  };

  const handleSaveSettings = async () => {
    if (!settings) return;

    setIsSaving(true);
    setError('');
    setSuccess('');

    try {
      const response = await apiFetch('/api/price-alerts/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schedule_frequency: settings.schedule_frequency,
          schedule_time: settings.schedule_time,
          schedule_day: settings.schedule_day,
          enabled: settings.enabled,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to save settings');
      }

      setSuccess('Settings saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddEmail = async () => {
    const trimmedEmail = newEmail.trim().toLowerCase();

    // Validate email
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(trimmedEmail)) {
      setEmailError('Please enter a valid email address');
      return;
    }

    // Check for duplicates
    if (emails.some(e => e.email === trimmedEmail)) {
      setEmailError('This email is already added');
      return;
    }

    setEmailError('');

    try {
      const response = await apiFetch('/api/price-alerts/emails', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: trimmedEmail }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to add email');
      }

      const newEmailData = await response.json();
      setEmails([...emails, newEmailData]);
      setNewEmail('');
      setSuccess('Email added successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setEmailError(err.message);
    }
  };

  const handleRemoveEmail = async (emailId: number) => {
    if (!confirm('Are you sure you want to remove this email?')) {
      return;
    }

    try {
      const response = await apiFetch(`/api/price-alerts/emails/${emailId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to remove email');
      }

      setEmails(emails.filter(e => e.email_id !== emailId));
      setSuccess('Email removed successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleSendTest = async () => {
    if (emails.length === 0) {
      setError('Please add at least one email address first');
      return;
    }

    const testEmail = emails[0].email;

    setIsSendingTest(true);
    setError('');
    setSuccess('');

    try {
      const response = await apiFetch('/api/price-alerts/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: testEmail }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to send test email');
      }

      setSuccess(`Test email sent to ${testEmail}! Check your inbox.`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSendingTest(false);
    }
  };

  const calculateNextAlert = () => {
    if (!settings || !settings.enabled) {
      return 'Alerts disabled';
    }

    const { schedule_frequency, schedule_time, schedule_day, last_alert_sent_at } = settings;

    if (!last_alert_sent_at) {
      return 'Next check (never sent before)';
    }

    const now = new Date();
    const lastSent = new Date(last_alert_sent_at);

    if (schedule_frequency === 'immediate') {
      const nextTime = new Date(lastSent.getTime() + 60000); // +1 minute
      return nextTime.toLocaleString();
    } else if (schedule_frequency === 'hourly') {
      const nextTime = new Date(lastSent.getTime() + 3600000); // +1 hour
      return nextTime.toLocaleString();
    } else if (schedule_frequency === 'daily') {
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      const [hours, minutes] = schedule_time.split(':');
      tomorrow.setHours(parseInt(hours), parseInt(minutes), 0, 0);
      return tomorrow.toLocaleString();
    } else if (schedule_frequency === 'weekly' && schedule_day !== null) {
      const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
      const [hours, minutes] = schedule_time.split(':');
      return `Every ${daysOfWeek[schedule_day]} at ${hours}:${minutes}`;
    }

    return 'Unknown';
  };

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="p-6 max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <BellIcon className="w-8 h-8 text-cyan-500" />
            <h1 className="text-3xl font-bold text-gray-900">Price Change Alerts</h1>
          </div>
          <p className="text-gray-600">
            Configure email notifications for price changes. Get notified when any product price changes.
          </p>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 flex items-center gap-2">
            <CheckCircleIcon className="w-5 h-5" />
            {success}
          </div>
        )}

        <div className="space-y-8">
          {/* Schedule Section */}
          <section className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Alert Schedule</h2>

            <div className="space-y-4">
              {/* Frequency Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Alert Frequency
                </label>
                <select
                  value={settings?.schedule_frequency || 'daily'}
                  onChange={(e) => handleScheduleChange('schedule_frequency', e.target.value)}
                  className="block w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                >
                  <option value="immediate">Immediate (1 min after price change)</option>
                  <option value="hourly">Every Hour</option>
                  <option value="daily">Daily at specific time</option>
                  <option value="weekly">Weekly on specific day</option>
                </select>
              </div>

              {/* Time Picker for Daily/Weekly */}
              {settings && (settings.schedule_frequency === 'daily' || settings.schedule_frequency === 'weekly') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Time of Day
                  </label>
                  <input
                    type="time"
                    value={settings.schedule_time || '09:00:00'}
                    onChange={(e) => handleScheduleChange('schedule_time', e.target.value + ':00')}
                    className="block w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                  />
                </div>
              )}

              {/* Day Picker for Weekly */}
              {settings && settings.schedule_frequency === 'weekly' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Day of Week
                  </label>
                  <select
                    value={settings.schedule_day ?? 0}
                    onChange={(e) => handleScheduleChange('schedule_day', parseInt(e.target.value))}
                    className="block w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                  >
                    <option value="0">Monday</option>
                    <option value="1">Tuesday</option>
                    <option value="2">Wednesday</option>
                    <option value="3">Thursday</option>
                    <option value="4">Friday</option>
                    <option value="5">Saturday</option>
                    <option value="6">Sunday</option>
                  </select>
                </div>
              )}

              {/* Enable/Disable Toggle */}
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={settings?.enabled || false}
                  onChange={(e) => handleScheduleChange('enabled', e.target.checked)}
                  className="w-5 h-5 text-cyan-500 border-gray-300 rounded focus:ring-2 focus:ring-cyan-500"
                />
                <label htmlFor="enabled" className="text-sm font-medium text-gray-700">
                  Enable price change alerts
                </label>
              </div>

              {/* Save Button */}
              <div className="pt-2">
                <button
                  onClick={handleSaveSettings}
                  disabled={isSaving}
                  className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {isSaving ? 'Saving...' : 'Save Schedule'}
                </button>
              </div>
            </div>
          </section>

          {/* Email List Section */}
          <section className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Email Recipients</h2>
            <p className="text-sm text-gray-600 mb-4">
              Add email addresses to receive price change alerts. All addresses will receive the same notifications.
            </p>

            {/* Email List */}
            <div className="space-y-2 mb-4">
              {emails.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No email addresses added yet. Add one below to get started.
                </div>
              ) : (
                emails.map((email) => (
                  <div
                    key={email.email_id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-cyan-100 rounded-full flex items-center justify-center">
                        <BellIcon className="w-5 h-5 text-cyan-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{email.email}</p>
                        <p className="text-sm text-gray-500">
                          Added {new Date(email.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemoveEmail(email.email_id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Remove email"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </button>
                  </div>
                ))
              )}
            </div>

            {/* Add Email Form */}
            <div className="border-t border-gray-200 pt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Add Email Address
              </label>
              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="Enter email address"
                  value={newEmail}
                  onChange={(e) => {
                    setNewEmail(e.target.value);
                    setEmailError('');
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleAddEmail();
                    }
                  }}
                  className={`flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 ${
                    emailError ? 'border-red-300' : 'border-gray-300'
                  }`}
                />
                <button
                  onClick={handleAddEmail}
                  className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 font-medium flex items-center gap-2"
                >
                  <PlusIcon className="w-5 h-5" />
                  Add
                </button>
              </div>
              {emailError && (
                <p className="mt-2 text-sm text-red-600">{emailError}</p>
              )}
            </div>

            {/* Test Email Button */}
            <div className="border-t border-gray-200 pt-4 mt-4">
              <button
                onClick={handleSendTest}
                disabled={isSendingTest || emails.length === 0}
                className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {isSendingTest ? 'Sending...' : 'Send Test Email'}
              </button>
              {emails.length > 0 && (
                <p className="mt-2 text-sm text-gray-500">
                  Test email will be sent to: {emails[0].email}
                </p>
              )}
            </div>
          </section>

          {/* Status Section */}
          <section className="bg-gradient-to-r from-cyan-50 to-blue-50 rounded-lg border border-cyan-200 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Alert Status</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Last Alert Sent</p>
                <p className="text-lg font-semibold text-gray-900">
                  {settings?.last_alert_sent_at
                    ? new Date(settings.last_alert_sent_at).toLocaleString()
                    : 'Never'}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Next Alert</p>
                <p className="text-lg font-semibold text-gray-900">
                  {calculateNextAlert()}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Recipients</p>
                <p className="text-lg font-semibold text-gray-900">
                  {emails.length} {emails.length === 1 ? 'email' : 'emails'}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Status</p>
                <p className={`text-lg font-semibold ${settings?.enabled ? 'text-green-600' : 'text-gray-500'}`}>
                  {settings?.enabled ? '✓ Enabled' : '○ Disabled'}
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </MainLayout>
  );
}
