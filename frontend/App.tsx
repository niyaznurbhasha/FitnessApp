import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  Platform,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Constants from 'expo-constants';

const API_BASE = Constants.expoConfig?.extra?.apiBase || 'https://your-staging-api-url.onrender.com';

interface ChatResponse {
  answer: string;
  trace_id: string;
  plan: any;
  tool_calls: any[];
  tokens_in: number;
  tokens_out: number;
}

export default function App() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversation, setConversation] = useState<Array<{type: 'user' | 'bot', text: string}>>([]);

  const handleSubmit = async () => {
    if (!message.trim()) return;
    
    setLoading(true);
    const userMessage = message;
    setMessage('');
    
    // Add user message to conversation
    setConversation(prev => [...prev, { type: 'user', text: userMessage }]);
    
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
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data: ChatResponse = await res.json();
      const botResponse = data.answer || 'No response received';
      
      // Add bot response to conversation
      setConversation(prev => [...prev, { type: 'bot', text: botResponse }]);
      setResponse(botResponse);
    } catch (error) {
      const errorMsg = `Error: ${error}`;
      setConversation(prev => [...prev, { type: 'bot', text: errorMsg }]);
      setResponse(errorMsg);
      Alert.alert('Error', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const clearConversation = () => {
    setConversation([]);
    setResponse('');
  };

  const quickActions = [
    { label: 'Single Meal', text: 'I had breakfast: 2 eggs scrambled with butter and toast' },
    { label: 'Whole Day', text: 'Today I had breakfast: eggs and toast, lunch: chicken salad, dinner: salmon' },
    { label: 'Daily Summary', text: 'daily summary' },
  ];

  return (
    <View style={styles.container}>
      <StatusBar style="auto" />
      
      <View style={styles.header}>
        <Text style={styles.title}>🍽️ Fitness App</Text>
        <Text style={styles.subtitle}>AI-Powered Nutrition Logging</Text>
      </View>

      <ScrollView style={styles.conversationContainer}>
        {conversation.length === 0 && (
          <View style={styles.welcomeContainer}>
            <Text style={styles.welcomeTitle}>Try these examples:</Text>
            {quickActions.map((action, index) => (
              <TouchableOpacity
                key={index}
                style={styles.quickAction}
                onPress={() => setMessage(action.text)}
              >
                <Text style={styles.quickActionLabel}>{action.label}</Text>
                <Text style={styles.quickActionText}>{action.text}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
        
        {conversation.map((msg, index) => (
          <View key={index} style={[
            styles.messageContainer,
            msg.type === 'user' ? styles.userMessage : styles.botMessage
          ]}>
            <Text style={[
              styles.messageText,
              msg.type === 'user' ? styles.userMessageText : styles.botMessageText
            ]}>
              {msg.text}
            </Text>
          </View>
        ))}
        
        {loading && (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Processing...</Text>
          </View>
        )}
      </ScrollView>

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          value={message}
          onChangeText={setMessage}
          placeholder="Describe your meal or ask for a daily summary..."
          multiline
          maxLength={500}
        />
        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[styles.button, styles.clearButton]}
            onPress={clearConversation}
          >
            <Text style={styles.clearButtonText}>Clear</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, styles.sendButton, loading && styles.disabledButton]}
            onPress={handleSubmit}
            disabled={loading || !message.trim()}
          >
            <Text style={styles.sendButtonText}>
              {loading ? 'Sending...' : 'Send'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    paddingTop: Platform.OS === 'web' ? 0 : 50,
  },
  header: {
    backgroundColor: '#007AFF',
    padding: 20,
    paddingTop: Platform.OS === 'web' ? 20 : 60,
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
  },
  conversationContainer: {
    flex: 1,
    padding: 16,
  },
  welcomeContainer: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  welcomeTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
    color: '#333',
  },
  quickAction: {
    backgroundColor: '#f0f0f0',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  quickActionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
    marginBottom: 4,
  },
  quickActionText: {
    fontSize: 12,
    color: '#666',
  },
  messageContainer: {
    marginBottom: 12,
    maxWidth: '85%',
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#007AFF',
    padding: 12,
    borderRadius: 18,
    borderBottomRightRadius: 4,
  },
  botMessage: {
    alignSelf: 'flex-start',
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 18,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  messageText: {
    fontSize: 16,
    lineHeight: 20,
  },
  userMessageText: {
    color: 'white',
  },
  botMessageText: {
    color: '#333',
  },
  loadingContainer: {
    alignSelf: 'flex-start',
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 18,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    fontStyle: 'italic',
  },
  inputContainer: {
    backgroundColor: 'white',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 12,
    padding: 12,
    fontSize: 16,
    maxHeight: 100,
    marginBottom: 12,
    backgroundColor: '#f9f9f9',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  button: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  clearButton: {
    backgroundColor: '#f0f0f0',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  clearButtonText: {
    color: '#666',
    fontWeight: '500',
  },
  sendButton: {
    backgroundColor: '#007AFF',
  },
  sendButtonText: {
    color: 'white',
    fontWeight: '600',
  },
  disabledButton: {
    backgroundColor: '#ccc',
  },
});
