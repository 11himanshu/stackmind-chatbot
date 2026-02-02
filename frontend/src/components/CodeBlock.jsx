import React, { useEffect, useRef, useState } from 'react'
import Prism from 'prismjs'

import 'prismjs/themes/prism-tomorrow.css'

import 'prismjs/components/prism-python'
import 'prismjs/components/prism-javascript'
import 'prismjs/components/prism-bash'
import 'prismjs/components/prism-json'
import 'prismjs/components/prism-yaml'
import 'prismjs/components/prism-docker'

import '../styles/code.css'

const normalizeLanguage = (lang) => {
  if (!lang) return 'text'
  const l = lang.toLowerCase()

  if (l === 'js') return 'javascript'
  if (l === 'shell' || l === 'sh') return 'bash'
  if (l === 'dockerfile') return 'docker'

  return l
}

const CodeBlock = ({ language, code }) => {
  const codeRef = useRef(null)
  const [copied, setCopied] = useState(false)

  const lang = normalizeLanguage(language)

  useEffect(() => {
    if (codeRef.current) {
      Prism.highlightElement(codeRef.current)
    }
  }, [code, lang])

  const handleCopy = async () => {
    if (!code) return
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1200)
  }

  return (
    <div className="code-wrapper">
      <div className="code-header">
        <span className="code-lang">{lang}</span>

        <button
          type="button"
          aria-label="Copy code"
          className={`copy-btn ${copied ? 'copied' : ''}`}
          onClick={handleCopy}
        >
          {copied ? 'Copied ✓' : 'Copy'}
        </button>
      </div>

      <pre>
        <code
          ref={codeRef}
          className={`language-${lang}`}
        >
          {code || ''}
        </code>
      </pre>
    </div>
  )
}

export default CodeBlock