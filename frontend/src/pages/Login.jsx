import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../services/api'
import './Auth.css'

/*
  Login Page
  ----------
  Responsibilities:
  - Authenticate user
  - Store token + user in localStorage
  - Redirect authenticated users
*/

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const navigate = useNavigate()

  // =========================================================
  // Redirect if already logged in
  // =========================================================
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      navigate('/chat', { replace: true })
    }
  }, [navigate])

  // =========================================================
  // Handle login
  // =========================================================
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!username || !password) {
      setError('Both fields are required')
      return
    }

    setLoading(true)

    try {
      const res = await login(username, password)

      // 🔑 STORE AUTH DATA (CRITICAL)
      localStorage.setItem('token', res.token)
      localStorage.setItem(
        'user',
        JSON.stringify({
          id: res.user_id,
          username: res.username
        })
      )

      navigate('/chat', { replace: true })

    } catch (err) {
      setError(err.message || 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">

        {/* ================= Header ================= */}
        <div className="auth-header">
          <div className="auth-logo">
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
              <defs>
                <linearGradient id="authCube" x1="0" y1="0" x2="36" y2="36">
                  <stop offset="0%" stopColor="#141e30" />
                  <stop offset="100%" stopColor="#243b55" />
                </linearGradient>
              </defs>
              <path d="M18 4L30 10L18 16L6 10L18 4Z" fill="url(#authCube)" />
              <path d="M30 10V22L18 28V16L30 10Z" fill="#1f2f46" />
              <path d="M6 10V22L18 28V16L6 10Z" fill="#2c3e5a" />
            </svg>
          </div>

          <h1>StackMind</h1>
          <p className="auth-subtitle">Sign in to your workspace</p>
        </div>

        {error && <div className="auth-error">{error}</div>}

        {/* ================= Form ================= */}
        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Username
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="your username"
              autoComplete="username"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="your password"
              autoComplete="current-password"
            />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        {/* ================= Footer ================= */}
        <div className="auth-footer">
          <span>New to StackMind?</span>
          <Link to="/register">Create an account</Link>
        </div>

      </div>
    </div>
  )
}

export default Login