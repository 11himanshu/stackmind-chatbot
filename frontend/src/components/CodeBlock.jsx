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

/* --------------------------------------------------
   Language normalization (unchanged logic)
-------------------------------------------------- */
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
  const copyBtnRef = useRef(null) // ADDED: accessibility focus restore
  const [copied, setCopied] = useState(false)
  const [mounted, setMounted] = useState(false) // ADDED: render polish

  const lang = normalizeLanguage(language)

  /* --------------------------------------------------
     Prism highlight (safer timing, no behavior change)
  -------------------------------------------------- */
  useEffect(() => {
    if (!codeRef.current) return

    // ADDED: ensure DOM paint before Prism runs
    requestAnimationFrame(() => {
      Prism.highlightElement(codeRef.current)
      setMounted(true)
    })
  }, [code, lang])

  /* --------------------------------------------------
     Copy handler (logic unchanged, polish added)
  -------------------------------------------------- */
  const handleCopy = async () => {
    if (!code) return

    await navigator.clipboard.writeText(code)
    setCopied(true)

    // ADDED: return focus for keyboard users
    if (copyBtnRef.current) {
      copyBtnRef.current.focus()
    }

    setTimeout(() => setCopied(false), 1200)
  }

  return (
    <div
      className={`code-wrapper ${mounted ? 'code-mounted' : ''}`} // ADDED: fade-in hook
    >
      <div className="code-header">
        <span className="code-lang">{lang}</span>

        <button
          ref={copyBtnRef}
          type="button"
          aria-label="Copy code"
          className={`copy-btn ${copied ? 'copied' : ''}`}
          onClick={handleCopy}
        >
          {copied ? 'Copied' : 'Copy'}
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