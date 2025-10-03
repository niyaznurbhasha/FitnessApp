import { useState } from 'react';
import Head from 'next/head';

export default function Home() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'demo_user',
          text: message
        }),
      });
      
      const data = await res.json();
      setResponse(data.answer || 'No response received');
    } catch (error) {
      setResponse(`Error: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <Head>
        <title>Fitness App - Nutrition Logging</title>
        <meta name="description" content="AI-powered nutrition tracking" />
      </Head>

      <h1>🍽️ Fitness App - Nutrition Logging</h1>
      
      <div style={{ 
        background: '#f0f0f0', 
        padding: '15px', 
        borderRadius: '8px', 
        marginBottom: '20px' 
      }}>
        <h3>Try these examples:</h3>
        <ul>
          <li><strong>Single meal:</strong> "I had breakfast: 2 eggs scrambled with butter and toast"</li>
          <li><strong>Whole day:</strong> "Today I had breakfast: eggs and toast, lunch: chicken salad, dinner: salmon"</li>
          <li><strong>Daily summary:</strong> "daily summary" or "process meals"</li>
        </ul>
      </div>

      <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
        <div style={{ marginBottom: '10px' }}>
          <label htmlFor="message" style={{ display: 'block', marginBottom: '5px' }}>
            What did you eat?
          </label>
          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Describe your meal or ask for a daily summary..."
            style={{
              width: '100%',
              height: '100px',
              padding: '10px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '16px'
            }}
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          style={{
            background: loading ? '#ccc' : '#0070f3',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '4px',
            fontSize: '16px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Processing...' : 'Send'}
        </button>
      </form>

      {response && (
        <div style={{
          background: '#f9f9f9',
          padding: '15px',
          borderRadius: '8px',
          border: '1px solid #ddd',
          whiteSpace: 'pre-wrap'
        }}>
          <h3>Response:</h3>
          <p>{response}</p>
        </div>
      )}

      <div style={{ 
        marginTop: '30px', 
        padding: '15px', 
        background: '#e8f4fd', 
        borderRadius: '8px',
        fontSize: '14px'
      }}>
        <h4>API Endpoints:</h4>
        <ul>
          <li><code>POST /chat</code> - Main chat interface</li>
          <li><code>POST /meals/quick-log</code> - Log single meal</li>
          <li><code>POST /meals/daily-summary</code> - Process daily summary</li>
          <li><code>GET /health</code> - Health check</li>
        </ul>
      </div>
    </div>
  );
}
