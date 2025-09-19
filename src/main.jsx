import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'
import MainApp from './MainApp.jsx'
import { AuthProvider } from './contexts/AuthContext.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  </StrictMode>,
)