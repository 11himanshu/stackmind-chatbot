import React, { useEffect, useRef } from 'react'
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
  if (l === 'shell') return 'bash'
  if (l === 'sh') return 'bash'
  if (l === 'dockerfile') return 'docker'

  return l
}

const CodeBlock = ({ language, code }) => {
  const codeRef = useRef(null)
  const lang = normalizeLanguage(language)

  useEffect(() => {
    if (!codeRef.current) return

    // 🔥 Highlight ONLY this block — no page reflow
    Prism.highlightElement(codeRef.current)
  }, [code, lang])

  const handleCopy = () => {
    if (!code) return
    navigator.clipboard.writeText(code)
  }

  return (
    <div className="code-wrapper">
      <div className="code-header">
        <span className="code-lang">{lang}</span>
        <button onClick={handleCopy}>Copy</button>
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