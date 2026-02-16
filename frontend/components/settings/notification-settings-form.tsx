'use client';

import { useState } from 'react';

import type { NotificationSettings } from '@/lib/api';
import { updateNotificationSettings } from '@/lib/api';

type Props = {
  initialSettings: NotificationSettings;
};

type ToggleKey =
  | 'protein_reminders_enabled'
  | 'fasting_alerts_enabled'
  | 'hydration_alerts_enabled'
  | 'insulin_alerts_enabled'
  | 'strength_reminders_enabled'
  | 'push_enabled'
  | 'silent_mode';

export function NotificationSettingsForm({ initialSettings }: Props) {
  const [settings, setSettings] = useState(initialSettings);
  const [status, setStatus] = useState<string>('');

  async function onToggle(key: ToggleKey) {
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

  async function saveField(
    payload: Partial<Pick<NotificationSettings, 'quiet_hours_start' | 'quiet_hours_end' | 'movement_reminder_delay_minutes' | 'movement_sensitivity'>>,
  ) {
    const next = { ...settings, ...payload };
    setSettings(next);
    const saved = await updateNotificationSettings(payload);
    setSettings(saved);
  }

  const options: Array<{ key: ToggleKey; label: string; helper: string }> = [
    { key: 'protein_reminders_enabled', label: 'Protein reminders', helper: 'Protein first nudges.' },
    { key: 'fasting_alerts_enabled', label: 'Fasting alerts', helper: 'Window-start fasting reminders.' },
    { key: 'hydration_alerts_enabled', label: 'Hydration alerts', helper: 'Water adherence prompts.' },
    { key: 'insulin_alerts_enabled', label: 'Insulin alerts', helper: 'High insulin load walk recommendation.' },
    { key: 'strength_reminders_enabled', label: 'Strength reminders', helper: 'Grip stimulus reminders.' },
    { key: 'push_enabled', label: 'Push channel', helper: 'Allow mobile push delivery.' },
    { key: 'silent_mode', label: 'Silent mode', helper: 'Mute all channels temporarily.' },
  ];

  return (
    <main className="mx-auto max-w-md space-y-4 px-4 py-8 text-white">
      <h1 className="text-xl font-semibold">Notification Settings</h1>
      <p className="text-sm text-slate-400">Control coaching reminders and quiet hours.</p>
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

      <section className="glass-card space-y-3 p-4">
        <p className="font-medium">Movement Intelligence</p>
        <label className="block space-y-1 text-xs">
          <span className="text-slate-400">Reminder delay (minutes)</span>
          <input
            type="number"
            min={15}
            max={90}
            value={settings.movement_reminder_delay_minutes}
            onChange={(event) => saveField({ movement_reminder_delay_minutes: Number(event.target.value) })}
            className="w-full rounded bg-white/10 px-2 py-1"
          />
        </label>
        <label className="block space-y-1 text-xs">
          <span className="text-slate-400">Sensitivity</span>
          <select
            value={settings.movement_sensitivity}
            onChange={(event) => saveField({ movement_sensitivity: event.target.value })}
            className="w-full rounded bg-white/10 px-2 py-1"
          >
            <option value="strict">Strict</option>
            <option value="balanced">Balanced</option>
            <option value="relaxed">Relaxed</option>
          </select>
        </label>
      </section>

      <section className="glass-card space-y-2 p-4">
        <p className="font-medium">Quiet hours</p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <label className="space-y-1">
            <span className="text-slate-400">Start</span>
            <input
              type="time"
              value={settings.quiet_hours_start ?? ''}
              onChange={(event) => saveField({ quiet_hours_start: event.target.value })}
              className="w-full rounded bg-white/10 px-2 py-1"
            />
          </label>
          <label className="space-y-1">
            <span className="text-slate-400">End</span>
            <input
              type="time"
              value={settings.quiet_hours_end ?? ''}
              onChange={(event) => saveField({ quiet_hours_end: event.target.value })}
              className="w-full rounded bg-white/10 px-2 py-1"
            />
          </label>
        </div>
      </section>

      {status ? <p className="text-xs text-slate-400">{status}</p> : null}
    </main>
  );
}
