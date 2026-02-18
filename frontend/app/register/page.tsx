'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

import { useAuth } from '@/context/auth-provider';
import { register } from '@/lib/api';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const { setToken } = useAuth();

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    try {
      const response = await register(email, password);
      setToken(response.access_token);
      router.replace('/');
    } catch {
      setError('Registration failed. Please use a stronger password and valid email.');
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center justify-center p-6">
      <form className="w-full space-y-4 rounded-lg border border-slate-700 p-6" onSubmit={onSubmit}>
        <h1 className="text-xl font-semibold">Register</h1>
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
        <input
          className="w-full rounded border border-slate-600 bg-slate-900 p-2"
          type="password"
          placeholder="Confirm password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
        <button className="w-full rounded bg-blue-600 p-2 font-medium hover:bg-blue-500" type="submit">
          Create account
        </button>
      </form>
    </main>
  );
}
