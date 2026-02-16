'use client';

import { useState } from 'react';

import type { NotificationSettings } from '@/lib/api';
import { updateNotificationSettings } from '@/lib/api';

type Props = {
  initialSettings: NotificationSettings;
};

export function NotificationSettingsForm({ initialSettings }: Props) {
  const [settings, setSettings] = useState(initialSettings);
  const [status, setStatus] = useState<string>('');

  async function onToggle(key: keyof Omit<NotificationSettings, 'user_id'>) {
    const next = { ...settings, [key]: !settings[key] };
    setSettings(next);
    try {
      const saved = await updateNotificationSettings({ [key]: next[key] });
      setSettings(saved);
      setStatus('Saved');
    } catch {
      setStatus('Failed to save');
      setSettings(settings);
    }
  }

  const options: Array<{ key: keyof Omit<NotificationSettings, 'user_id'>; label: string; helper: string }> = [
    { key: 'whatsapp_enabled', label: 'WhatsApp', helper: 'Enable coaching and alerts over WhatsApp.' },
    { key: 'push_enabled', label: 'Push', helper: 'Receive mobile push alerts for insulin/protein thresholds.' },
    { key: 'email_enabled', label: 'Email', helper: 'Enable daily summary and coaching over email.' },
    { key: 'silent_mode', label: 'Silent mode', helper: 'Mute all channels temporarily.' },
  ];

  return (
    <main className="mx-auto max-w-md space-y-4 px-4 py-8 text-white">
      <h1 className="text-xl font-semibold">Notification Settings</h1>
      <p className="text-sm text-slate-400">Control WhatsApp, push, email, and silent mode.</p>
      {options.map((option) => (
        <section key={option.key} className="glass-card flex items-center justify-between gap-4 p-4">
          <div>
            <p className="font-medium">{option.label}</p>
            <p className="text-xs text-slate-400">{option.helper}</p>
          </div>
          <button
            type="button"
            className={`rounded-lg px-3 py-1 text-sm ${settings[option.key] ? 'bg-emerald-500/30 text-emerald-200' : 'bg-white/10 text-slate-300'}`}
            onClick={() => onToggle(option.key)}
          >
            {settings[option.key] ? 'On' : 'Off'}
          </button>
        </section>
      ))}
      {status ? <p className="text-xs text-slate-400">{status}</p> : null}
    </main>
  );
}
