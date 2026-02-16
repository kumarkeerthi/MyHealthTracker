'use client';

import { useEffect, useState } from 'react';

import { getPushPublicKey, subscribePush } from '@/lib/api';

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
};

function urlBase64ToUint8Array(base64String: string) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}

export function PwaClient() {
  const [installEvt, setInstallEvt] = useState<BeforeInstallPromptEvent | null>(null);
  const [installVisible, setInstallVisible] = useState(false);
  const [pushStatus, setPushStatus] = useState('');

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js');
    }

    const handler = (event: Event) => {
      event.preventDefault();
      setInstallEvt(event as BeforeInstallPromptEvent);
      setInstallVisible(true);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  async function requestPush() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      setPushStatus('Push unavailable on this device/browser.');
      return;
    }

    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      setPushStatus('Permission denied.');
      return;
    }

    const key = await getPushPublicKey();
    if (!key || !key.public_key) {
      setPushStatus('Push key unavailable. Configure VAPID keys.');
      return;
    }

    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(key.public_key),
    });

    await subscribePush({
      user_id: 1,
      endpoint: subscription.endpoint,
      expirationTime: subscription.expirationTime,
      keys: {
        p256dh: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('p256dh') || new ArrayBuffer(0)))),
        auth: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('auth') || new ArrayBuffer(0)))),
      },
      user_agent: navigator.userAgent,
    });
    setPushStatus('Push notifications enabled.');
  }

  async function installNow() {
    if (!installEvt) return;
    await installEvt.prompt();
    setInstallVisible(false);
  }

  return (
    <div className="space-y-2">
      {installVisible ? (
        <section className="glass-card p-4 text-sm">
          <p className="font-medium">Install Metabolic OS for full experience.</p>
          <p className="mt-1 text-xs text-slate-300">Tap install for one-step setup on your home screen.</p>
          <button className="mt-2 rounded bg-emerald-600 px-3 py-2 text-xs" onClick={installNow}>Install</button>
        </section>
      ) : null}
      <button className="rounded border border-white/20 px-3 py-2 text-xs" onClick={requestPush}>Enable Push Notifications</button>
      {pushStatus ? <p className="text-xs text-slate-400">{pushStatus}</p> : null}
    </div>
  );
}
