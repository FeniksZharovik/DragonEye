// lib/auth.ts
import { fetchFromAPI } from './api';

export interface User {
  uid: string;
  username: string;
  email: string;
}

let currentUser: User | null = null;

export async function getCurrentUser(): Promise<User | null> {
  try {
    const user = await fetchFromAPI<User>('/api/auth/me', {
      method: 'GET',
      credentials: 'include', // Ensure cookies are sent
    });
    currentUser = user;
    console.log('✅ Got current user:', user);
    return user;
  } catch (err) {
    console.warn('⚠️ getCurrentUser failed:', err instanceof Error ? err.message : err);
    currentUser = null;
    return null;
  }
}

export async function logout(): Promise<void> {
  try {
    await fetchFromAPI('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    });
    console.log('✅ Logged out successfully');
  } catch (err) {
    console.warn('⚠️ Logout API error (safe to ignore):', err);
  } finally {
    currentUser = null;
    // Clear localStorage session_id backup
    if (typeof window !== 'undefined') {
      localStorage.removeItem('session_id');
      console.log('🧹 Cleared localStorage session_id');
    }
  }
}