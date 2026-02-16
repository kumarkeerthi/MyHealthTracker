import { NotificationSettingsForm } from '@/components/settings/notification-settings-form';
import { getNotificationSettings } from '@/lib/api';

export default async function NotificationSettingsPage() {
  const settings =
    (await getNotificationSettings()) ??
    {
      user_id: 1,
      whatsapp_enabled: true,
      push_enabled: true,
      email_enabled: false,
      silent_mode: false,
      protein_reminders_enabled: true,
      fasting_alerts_enabled: true,
      hydration_alerts_enabled: true,
      insulin_alerts_enabled: true,
      strength_reminders_enabled: true,
      quiet_hours_start: null,
      quiet_hours_end: null,
      movement_reminder_delay_minutes: 45,
      movement_sensitivity: "balanced",
    };

  return <NotificationSettingsForm initialSettings={settings} />;
}
