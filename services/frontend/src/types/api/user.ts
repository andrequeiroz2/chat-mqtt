/**
 * Contrato HTTP de perfil — espelha `UserProfileResponse` / `UserProfileUpdateRequest`.
 */

export type UserProfile = {
  user_id: string
  email: string | null
  display_name: string
  photo_url: string | null
  auth_providers: string[]
  created_at: string
  updated_at: string
}

export type UserProfileUpdateRequest = {
  display_name: string
}
