import React, { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'https://fitnessapp-yynz.onrender.com'

interface ChatResponse {
  answer: string
  trace_id: string
  plan: any
  tool_calls: any[]
  tokens_in: number
  tokens_out: number
}

interface LogEntry {
  id: string
  date: string
  input: string
  output: string
  type: 'single_meal' | 'whole_day' | 'summary'
  isFinalMeal?: boolean
  macros?: {
    protein: number
    carbs: number
    fat: number
    calories: number
  }
}

type Screen = 'summary' | 'browse' | 'nutrient_logging' | 'chat'

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [password, setPassword] = useState('')
  const [currentScreen, setCurrentScreen] = useState<Screen>('summary')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [apiCallsUsed, setApiCallsUsed] = useState(0)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [currentMealType, setCurrentMealType] = useState<'single_meal' | 'whole_day'>('single_meal')

  const handleLogin = () => {
    const correctPassword = import.meta.env.VITE_APP_PASSWORD || 'localtestpass'
    if (password === correctPassword) {
      setIsAuthenticated(true)
    } else {
      alert('Incorrect password')
    }
  }

  const handleSubmit = async (input: string, type: 'single_meal' | 'whole_day') => {
    if (apiCallsUsed >= 10) {
      alert('Maximum API calls reached for this session (10). Please refresh the browser to reset.')
      return
    }

    setLoading(true)
    
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'demo_user',
          text: input
        }),
      })
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }
      
      const data: ChatResponse = await res.json()
      const response = data.answer || 'No response received'
      
      // Check if this is a final meal
      const isFinalMeal = input.toLowerCase().includes('final meal') || type === 'whole_day'
      
      // Add to logs
      const newLog: LogEntry = {
        id: Date.now().toString(),
        date: new Date().toISOString().split('T')[0],
        input,
        output: response,
        type,
        isFinalMeal
      }
      
      setLogs(prev => [newLog, ...prev])
      setApiCallsUsed(prev => prev + 1)
      setCurrentScreen('summary')
      setMessage('')
    } catch (error) {
      console.error('Error:', error)
      alert('Error processing your request. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getTodaysLogs = () => {
    const today = new Date().toISOString().split('T')[0]
    return logs.filter(log => log.date === today)
  }

  const getTodaysDate = () => {
    return new Date().toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  }

  const renderSummary = () => {
    const todaysLogs = getTodaysLogs()
    const hasFinalMeal = todaysLogs.some(log => log.isFinalMeal)
    
    return (
      <div style={{ padding: '20px', maxWidth: '400px', margin: '0 auto', minHeight: '100vh', background: '#1c1c1e' }}>
        <div style={{ background: '#8B4513', padding: '20px', marginBottom: '20px', borderRadius: '0 0 20px 20px' }}>
          <h1 style={{ color: 'white', margin: 0, fontSize: '28px', fontWeight: 'bold' }}>Summary</h1>
        </div>
        
        <div style={{ marginBottom: '20px' }}>
          <h2 style={{ color: 'white', marginBottom: '15px' }}>Today's Activity</h2>
          <div style={{ color: '#8e8e93', fontSize: '14px', marginBottom: '20px' }}>
            {getTodaysDate()}
          </div>
          
          {todaysLogs.length === 0 ? (
            <div style={{ 
              background: '#2c2c2e', 
              padding: '20px', 
              borderRadius: '12px', 
              textAlign: 'center',
              border: '1px solid #3a3a3c'
            }}>
              <div style={{ color: '#8e8e93', fontSize: '16px' }}>
                No meals logged today
              </div>
              <div style={{ color: '#8e8e93', fontSize: '12px', marginTop: '8px' }}>
                Go to Browse → Nutrition to log your first meal
              </div>
            </div>
          ) : (
            <>
              {todaysLogs.map((log) => (
                <div key={log.id} style={{ 
                  background: '#2c2c2e', 
                  padding: '15px', 
                  borderRadius: '12px', 
                  marginBottom: '10px',
                  border: '1px solid #3a3a3c'
                }}>
                  <div style={{ color: '#8e8e93', fontSize: '12px', marginBottom: '5px' }}>
                    {log.type === 'single_meal' ? 'Single Meal' : 'Whole Day'}
                    {log.isFinalMeal && ' • Final Meal'}
                  </div>
                  <div style={{ color: 'white', fontSize: '14px', marginBottom: '8px' }}>
                    {log.input}
                  </div>
                  <div style={{ color: '#8e8e93', fontSize: '12px' }}>
                    {log.output}
                  </div>
                </div>
              ))}
              
              {!hasFinalMeal && todaysLogs.some(log => log.type === 'single_meal') && (
                <div style={{ 
                  background: '#FF9500', 
                  padding: '15px', 
                  borderRadius: '12px', 
                  marginTop: '10px',
                  textAlign: 'center'
                }}>
                  <div style={{ color: 'white', fontSize: '14px', fontWeight: '600' }}>
                    ⚠️ Incomplete Day
                  </div>
                  <div style={{ color: 'white', fontSize: '12px', marginTop: '5px' }}>
                    Add "final meal" to your next entry to calculate daily totals
                  </div>
                </div>
              )}
            </>
          )}
        </div>
        
        <div style={{ 
          background: '#2c2c2e', 
          padding: '15px', 
          borderRadius: '12px', 
          border: '1px solid #3a3a3c',
          textAlign: 'center'
        }}>
          <div style={{ color: '#8e8e93', fontSize: '12px' }}>
            API Calls Used: {apiCallsUsed}/10
          </div>
        </div>
      </div>
    )
  }

  const renderBrowse = () => (
    <div style={{ padding: '20px', maxWidth: '400px', margin: '0 auto', minHeight: '100vh', background: '#1c1c1e' }}>
      <div style={{ background: '#8B4513', padding: '20px', marginBottom: '20px', borderRadius: '0 0 20px 20px' }}>
        <h1 style={{ color: 'white', margin: 0, fontSize: '28px', fontWeight: 'bold' }}>Browse</h1>
      </div>
      
      <div>
        <h2 style={{ color: 'white', marginBottom: '15px' }}>Health Categories</h2>
        <div style={{ 
          background: '#2c2c2e', 
          padding: '15px', 
          borderRadius: '12px', 
          marginBottom: '10px',
          border: '1px solid #3a3a3c',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }} onClick={() => setCurrentScreen('nutrient_logging')}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ 
              width: '30px', 
              height: '30px', 
              background: '#34C759', 
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '12px'
            }}>
              🍎
            </div>
            <span style={{ color: 'white', fontSize: '16px' }}>Nutrition</span>
          </div>
          <div style={{ color: '#8e8e93' }}>›</div>
        </div>
      </div>
    </div>
  )

  const renderNutrientLogging = () => (
    <div style={{ padding: '20px', maxWidth: '400px', margin: '0 auto', minHeight: '100vh', background: '#1c1c1e' }}>
      <div style={{ background: '#8B4513', padding: '20px', marginBottom: '20px', borderRadius: '0 0 20px 20px' }}>
        <h1 style={{ color: 'white', margin: 0, fontSize: '28px', fontWeight: 'bold' }}>Nutrition</h1>
      </div>
      
      <div style={{ textAlign: 'center', marginTop: '40px' }}>
        <h2 style={{ color: 'white', marginBottom: '30px' }}>What would you like to log?</h2>
        
        <div style={{ marginBottom: '20px' }}>
          <button
            onClick={() => {
              setCurrentMealType('single_meal')
              setCurrentScreen('chat')
            }}
            style={{
              background: '#007AFF',
              color: 'white',
              border: 'none',
              padding: '20px 40px',
              borderRadius: '12px',
              fontSize: '18px',
              fontWeight: '600',
              cursor: 'pointer',
              width: '100%',
              marginBottom: '15px'
            }}
          >
            Single Meal
          </button>
          
          <button
            onClick={() => {
              setCurrentMealType('whole_day')
              setCurrentScreen('chat')
            }}
            style={{
              background: '#007AFF',
              color: 'white',
              border: 'none',
              padding: '20px 40px',
              borderRadius: '12px',
              fontSize: '18px',
              fontWeight: '600',
              cursor: 'pointer',
              width: '100%'
            }}
          >
            Whole Day
          </button>
        </div>
      </div>
    </div>
  )

  const renderChat = () => (
    <div style={{ padding: '20px', maxWidth: '400px', margin: '0 auto', minHeight: '100vh', background: '#1c1c1e' }}>
      <div style={{ background: '#8B4513', padding: '20px', marginBottom: '20px', borderRadius: '0 0 20px 20px' }}>
        <h1 style={{ color: 'white', margin: 0, fontSize: '28px', fontWeight: 'bold' }}>Nutrition Logging</h1>
        <div style={{ color: '#FFD700', fontSize: '12px', marginTop: '8px' }}>
          {currentMealType === 'single_meal' ? '💡 Tip: Add "final meal" to your text to calculate daily totals' : 'Logging your whole day\'s nutrition'}
        </div>
      </div>
      
      <div style={{ marginBottom: '20px' }}>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Describe what you ate..."
          style={{
            width: '100%',
            height: '120px',
            padding: '15px',
            border: '1px solid #3a3a3c',
            borderRadius: '12px',
            fontSize: '16px',
            background: '#2c2c2e',
            color: 'white',
            resize: 'vertical',
            boxSizing: 'border-box'
          }}
        />
      </div>
      
      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={() => setCurrentScreen('nutrient_logging')}
          style={{
            background: '#3a3a3c',
            color: 'white',
            border: 'none',
            padding: '15px 20px',
            borderRadius: '12px',
            fontSize: '16px',
            cursor: 'pointer',
            flex: 1
          }}
        >
          Back
        </button>
        
        <button
          onClick={() => handleSubmit(message, currentMealType)}
          disabled={loading || !message.trim() || apiCallsUsed >= 10}
          style={{
            background: loading || !message.trim() || apiCallsUsed >= 10 ? '#3a3a3c' : '#007AFF',
            color: 'white',
            border: 'none',
            padding: '15px 20px',
            borderRadius: '12px',
            fontSize: '16px',
            cursor: loading || !message.trim() || apiCallsUsed >= 10 ? 'not-allowed' : 'pointer',
            flex: 1
          }}
        >
          {loading ? 'Processing...' : apiCallsUsed >= 10 ? 'Limit Reached' : 'Submit'}
        </button>
      </div>
    </div>
  )

  if (!isAuthenticated) {
    return (
      <div style={{ 
        fontFamily: 'Arial, sans-serif', 
        background: '#1c1c1e', 
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}>
        <div style={{ 
          background: '#2c2c2e', 
          padding: '40px', 
          borderRadius: '20px',
          border: '1px solid #3a3a3c',
          maxWidth: '400px',
          width: '100%'
        }}>
          <h1 style={{ color: 'white', textAlign: 'center', marginBottom: '30px' }}>
            🔒 Fitness App
          </h1>
          <p style={{ color: '#8e8e93', textAlign: 'center', marginBottom: '30px' }}>
            Enter password to access
          </p>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            style={{
              width: '100%',
              padding: '15px',
              border: '1px solid #3a3a3c',
              borderRadius: '12px',
              fontSize: '16px',
              background: '#1c1c1e',
              color: 'white',
              marginBottom: '20px',
              boxSizing: 'border-box'
            }}
            onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
          />
          <button
            onClick={handleLogin}
            style={{
              width: '100%',
              background: '#007AFF',
              color: 'white',
              border: 'none',
              padding: '15px',
              borderRadius: '12px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Access App
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', background: '#1c1c1e', minHeight: '100vh' }}>
      {currentScreen === 'summary' && renderSummary()}
      {currentScreen === 'browse' && renderBrowse()}
      {currentScreen === 'nutrient_logging' && renderNutrientLogging()}
      {currentScreen === 'chat' && renderChat()}
      
      {/* Bottom Navigation */}
      <div style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        background: '#2c2c2e',
        borderTop: '1px solid #3a3a3c',
        display: 'flex',
        justifyContent: 'space-around',
        padding: '10px 0',
        maxWidth: '400px',
        margin: '0 auto'
      }}>
        <button
          onClick={() => setCurrentScreen('summary')}
          style={{
            background: 'none',
            border: 'none',
            color: currentScreen === 'summary' ? '#007AFF' : '#8e8e93',
            fontSize: '12px',
            cursor: 'pointer',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          <div style={{ fontSize: '20px' }}>📊</div>
          <span>Summary</span>
        </button>
        
        <button
          onClick={() => setCurrentScreen('browse')}
          style={{
            background: 'none',
            border: 'none',
            color: currentScreen === 'browse' ? '#007AFF' : '#8e8e93',
            fontSize: '12px',
            cursor: 'pointer',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          <div style={{ fontSize: '20px' }}>⊞</div>
          <span>Browse</span>
        </button>
      </div>
    </div>
  )
}
