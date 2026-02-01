import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'

import ChatLayout from './layouts/ChatLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import RequireAuth from './components/RequireAuth'

import './App.css'

/*
  App Router
  ----------
  - Public routes: login, register
  - Protected routes: chat
  - Auth guard ensures session persistence
*/

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route
            path="/chat"
            element={
              <RequireAuth>
                <ChatLayout />
              </RequireAuth>
            }
          />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/login" replace />} />

        </Routes>
      </div>
    </Router>
  )
}

export default App