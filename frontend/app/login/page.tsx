'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

import { useAuth } from '@/context/auth-provider';
import { login } from '@/lib/api';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const { setToken } = useAuth();

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      const response = await login(email, password);
      setToken(response.access_token);
      router.replace('/');
    } catch {
      setError('Login failed. Check your credentials.');
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center justify-center p-6">
      <form className="w-full space-y-4 rounded-lg border border-slate-700 p-6" onSubmit={onSubmit}>
        <h1 className="text-xl font-semibold">Login</h1>
        <input
          className="w-full rounded border border-slate-600 bg-slate-900 p-2"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="w-full rounded border border-slate-600 bg-slate-900 p-2"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
        <button className="w-full rounded bg-blue-600 p-2 font-medium hover:bg-blue-500" type="submit">
          Sign in
        </button>
      </form>
    </main>
  );
}
