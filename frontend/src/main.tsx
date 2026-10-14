import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { App } from './app/App'
import { AppProviders } from './app/providers'
import { AuthProvider } from './app/auth'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><BrowserRouter><AppProviders><AuthProvider><App /></AuthProvider></AppProviders></BrowserRouter></React.StrictMode>)
