import { ApiStatusBanner } from './app/ApiStatusBanner'
import { AppRoot } from './app/AppRoot'
import { AuthProvider } from './auth/AuthProvider'

export default function App() {
  return (
    <AuthProvider>
      <ApiStatusBanner />
      <AppRoot />
    </AuthProvider>
  )
}
