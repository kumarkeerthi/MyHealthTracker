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
    };

  return <NotificationSettingsForm initialSettings={settings} />;
}
