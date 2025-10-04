import React, { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'https://fitnessapp-yynz.onrender.com'

interface ChatResponse {
  answer: string
  trace_id: string
  plan: any
  tool_calls: any[]
  tokens_in: number
  tokens_out: number
}

export default function App() {
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversation, setConversation] = useState<Array<{type: 'user' | 'bot', text: string}>>([])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return
    
    setLoading(true)
    const userMessage = message
    setMessage('')
    
    // Add user message to conversation
    setConversation(prev => [...prev, { type: 'user', text: userMessage }])
    
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'demo_user',
          text: userMessage
        }),
      })
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }
      
      const data: ChatResponse = await res.json()
      const botResponse = data.answer || 'No response received'
      
      // Add bot response to conversation
      setConversation(prev => [...prev, { type: 'bot', text: botResponse }])
      setResponse(botResponse)
    } catch (error) {
      const errorMsg = `Error: ${error}`
      setConversation(prev => [...prev, { type: 'bot', text: errorMsg }])
      setResponse(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const clearConversation = () => {
    setConversation([])
    setResponse('')
  }

  const quickActions = [
    { label: 'Single Meal', text: 'I had breakfast: 2 eggs scrambled with butter and toast' },
    { label: 'Whole Day', text: 'Today I had breakfast: eggs and toast, lunch: chicken salad, dinner: salmon' },
    { label: 'Daily Summary', text: 'daily summary' },
  ]

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <div style={{ background: '#007AFF', color: 'white', padding: '20px', borderRadius: '8px', marginBottom: '20px', textAlign: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '24px' }}>🍽️ Fitness App</h1>
        <p style={{ margin: '4px 0 0 0', opacity: 0.8 }}>AI-Powered Nutrition Logging</p>
      </div>

      {conversation.length === 0 && (
        <div style={{ background: '#f0f0f0', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
          <h3 style={{ marginTop: 0 }}>Try these examples:</h3>
          {quickActions.map((action, index) => (
            <div key={index} style={{ background: 'white', padding: '12px', borderRadius: '8px', marginBottom: '8px', cursor: 'pointer' }} onClick={() => setMessage(action.text)}>
              <div style={{ fontWeight: '600', color: '#007AFF', marginBottom: '4px' }}>{action.label}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>{action.text}</div>
            </div>
          ))}
        </div>
      )}
      
      <div style={{ marginBottom: '20px', maxHeight: '400px', overflowY: 'auto' }}>
        {conversation.map((msg, index) => (
          <div key={index} style={{ marginBottom: '12px', display: 'flex', justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              background: msg.type === 'user' ? '#007AFF' : 'white',
              color: msg.type === 'user' ? 'white' : '#333',
              padding: '12px',
              borderRadius: '18px',
              maxWidth: '85%',
              border: msg.type === 'bot' ? '1px solid #e0e0e0' : 'none',
              whiteSpace: 'pre-wrap'
            }}>
              {msg.text}
            </div>
          </div>
        ))}
        
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ background: 'white', padding: '12px', borderRadius: '18px', border: '1px solid #e0e0e0', fontStyle: 'italic', color: '#666' }}>
              Processing...
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} style={{ background: 'white', padding: '16px', borderRadius: '8px', border: '1px solid #e0e0e0' }}>
        <div style={{ marginBottom: '12px' }}>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Describe your meal or ask for a daily summary..."
            style={{
              width: '100%',
              height: '100px',
              padding: '12px',
              border: '1px solid #ddd',
              borderRadius: '8px',
              fontSize: '16px',
              resize: 'vertical',
              boxSizing: 'border-box'
            }}
            required
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
          <button
            type="button"
            onClick={clearConversation}
            style={{
              background: '#f0f0f0',
              color: '#666',
              border: '1px solid #ddd',
              padding: '12px 24px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            Clear
          </button>
          <button
            type="submit"
            disabled={loading || !message.trim()}
            style={{
              background: loading || !message.trim() ? '#ccc' : '#007AFF',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '8px',
              cursor: loading || !message.trim() ? 'not-allowed' : 'pointer',
              fontWeight: '600'
            }}
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  )
}
