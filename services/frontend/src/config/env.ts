import type { FirebaseOptions } from 'firebase/app'

/**
 * Variáveis de ambiente Vite (Firebase Web + URL da API).
 * Tipagem: `src/vite-env.d.ts`.
 */

function required(name: keyof ImportMetaEnv, value: string | undefined): string {
  if (!value?.trim()) {
    throw new Error(`Missing environment variable: ${name}`)
  }
  return value.trim()
}

export const apiBaseUrl: string =
  import.meta.env.VITE_API_BASE_URL?.trim() || 'http://127.0.0.1:8000'

export const firebaseConfig: FirebaseOptions = {
  apiKey: required('VITE_FIREBASE_API_KEY', import.meta.env.VITE_FIREBASE_API_KEY),
  authDomain: required(
    'VITE_FIREBASE_AUTH_DOMAIN',
    import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  ),
  projectId: required('VITE_FIREBASE_PROJECT_ID', import.meta.env.VITE_FIREBASE_PROJECT_ID),
  storageBucket: required(
    'VITE_FIREBASE_STORAGE_BUCKET',
    import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  ),
  messagingSenderId: required(
    'VITE_FIREBASE_MESSAGING_SENDER_ID',
    import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  ),
  appId: required('VITE_FIREBASE_APP_ID', import.meta.env.VITE_FIREBASE_APP_ID),
}
