import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

import { firebaseConfig } from '../config/env'

export const firebaseApp = initializeApp(firebaseConfig)
export const auth = getAuth(firebaseApp)
