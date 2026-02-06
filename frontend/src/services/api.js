/*
  API Service Layer
  -----------------
  Responsibilities:
  - Centralize all HTTP calls
  - Automatically attach JWT auth headers
  - Support JSON + streaming endpoints
  - Prevent duplicate / hanging requests
*/

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

/* =========================================================
   Helper: Auth headers
   ========================================================= */
const authHeaders = () => {
  const token = localStorage.getItem('token')

  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  }
}

/* =========================================================
   In-flight request control (STRICT)
   ========================================================= */
const inflight = new Map()

const inflightKey = (url, method = 'GET') =>
  `${method.toUpperCase()}::${url}`

const fetchJSON = async (url, options = {}) => {
  const method = options.method || 'GET'
  const key = inflightKey(url, method)

  // Abort previous identical request
  if (inflight.has(key)) {
    inflight.get(key).abort()
  }

  const controller = new AbortController()
  inflight.set(key, controller)

  try {
    const response = await fetch(url, {
      headers: authHeaders(),
      signal: controller.signal,
      ...options
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP error ${response.status}`)
    }

    return await response.json()
  } finally {
    inflight.delete(key)
  }
}

/* ========================= AUTH ========================= */

export const register = async (username, password) => {
  return fetchJSON(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    body: JSON.stringify({ username, password })
  })
}

export const login = async (username, password) => {
  return fetchJSON(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    body: JSON.stringify({ username, password })
  })
}

/* ===================== CHAT (STREAM) ===================== */

let activeChatController = null

export const chatStream = async (
  message,
  conversationId = null,
  onChunk,
  onMeta
) => {
  // Abort any existing stream
  if (activeChatController) {
    activeChatController.abort()
  }

  const controller = new AbortController()
  activeChatController = controller

  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: authHeaders(),
    signal: controller.signal,
    body: JSON.stringify({
      message,
      conversation_id: conversationId
    })
  })

  if (!response.ok || !response.body) {
    activeChatController = null
    throw new Error('Chat stream failed')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')

  let buffer = ''

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      while (buffer.length) {
        // META frame
        if (buffer.startsWith('__META__')) {
          const metaEnd = buffer.indexOf('\n')
          if (metaEnd === -1) break

          const metaRaw = buffer.slice(8, metaEnd)
          buffer = buffer.slice(metaEnd + 1)

          try {
            onMeta?.(JSON.parse(metaRaw))
          } catch {
            console.error('Invalid META chunk', metaRaw)
          }
          continue
        }

        // TEXT frame
        const nextMeta = buffer.indexOf('__META__')

        if (nextMeta === -1) {
          const text = buffer
          buffer = ''
          if (text.trim()) onChunk?.(text)
        } else {
          const text = buffer.slice(0, nextMeta)
          buffer = buffer.slice(nextMeta)
          if (text.trim()) onChunk?.(text)
        }
      }
    }

    // flush remaining buffer
    if (buffer.trim()) {
      onChunk?.(buffer)
    }
  } finally {
    activeChatController = null
  }
}

/* ===================== CONVERSATIONS ===================== */

export const fetchConversations = async () => {
  return fetchJSON(`${API_BASE_URL}/conversations`)
}

export const fetchConversationHistory = async (conversationId) => {
  return fetchJSON(`${API_BASE_URL}/conversations/${conversationId}`)
}

export const deleteConversation = async (conversationId) => {
  return fetchJSON(
    `${API_BASE_URL}/conversations/${conversationId}`,
    { method: 'DELETE' }
  )
}