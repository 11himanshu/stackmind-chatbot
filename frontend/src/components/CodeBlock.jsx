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

const CodeBlock = ({ language, code }) => {
  const ref = useRef(null)

  useEffect(() => {
    Prism.highlightAllUnder(ref.current)
  }, [code])

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
  }

  return (
    <div className="code-wrapper">
      <div className="code-header">
        <span className="code-lang">{language || 'text'}</span>
        <button onClick={handleCopy}>Copy</button>
      </div>

      <pre ref={ref}>
        <code className={`language-${language || 'text'}`}>
          {code}
        </code>
      </pre>
    </div>
  )
}

export default CodeBlock
