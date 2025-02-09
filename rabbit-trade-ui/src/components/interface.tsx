'use client'

import React, { useState, useEffect } from 'react'
import { MessageSquare, Send, RefreshCw } from 'lucide-react'
// import { Alert, AlertDescription } from '@/components/ui/alert'

interface Message {
  wallet: string
  preferences: string
  timestamp: string
}

export default function RabbitMQInterface() {
  const [walletAddress, setWalletAddress] = useState('')
  const [preferences, setPreferences] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [error, setError] = useState('')
  const [status, setStatus] = useState('Checking...')
  const [isLoading, setIsLoading] = useState(false)

  const validateWallet = (address: string) => {
    const pattern = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/
    return pattern.test(address)
  }

  const checkStatus = async () => {
    try {
      const response = await fetch('/api/status')
      const data = await response.json()
      setStatus(data.status)
    } catch (err) {
      setStatus('Disconnected')
      setError('Failed to check status')
    }
  }

  useEffect(() => {
    checkStatus()
    const interval = setInterval(checkStatus, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    if (!validateWallet(walletAddress)) {
      setError('Invalid wallet address format')
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch('/api/send-message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wallet: walletAddress,
          preferences: preferences || 'default',
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      setMessages(prev => [{
        wallet: walletAddress,
        preferences,
        timestamp: new Date().toISOString()
      }, ...prev])
      
      setWalletAddress('')
      setPreferences('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Shadow Agentic</h1>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${
            status === 'Connected' ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
          <span>{status}</span>
          <button 
            onClick={checkStatus}
            className="ml-2 p-2 rounded-full hover:bg-gray-100"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )} */}

      <form onSubmit={handleSubmit} className="space-y-4 mb-8">
        <div>
          <label className="block text-sm font-medium mb-1">
            Wallet Address
          </label>
          <input
            type="text"
            value={walletAddress}
            onChange={(e) => setWalletAddress(e.target.value)}
            className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 text-black"
            placeholder="Enter Solana wallet address"
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Trading Preferences
          </label>
          <textarea
            value={preferences}
            onChange={(e) => setPreferences(e.target.value)}
            className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 text-black"
            placeholder="Enter trading preferences (optional)"
            rows={3}
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          disabled={isLoading}
        >
          {isLoading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
          {isLoading ? 'Sending...' : 'Send Request'}
        </button>
      </form>

      <div>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <MessageSquare className="w-5 h-5" />
          Recent Requests
        </h2>
        <div className="space-y-4 text-black">
          {messages.map((msg, idx) => (
            <div key={idx} className="p-4 border rounded bg-gray-50">
              <div className="text-sm text-gray-500">
                {new Date(msg.timestamp).toLocaleString()}
              </div>
              <div className="font-mono text-sm mt-1">{msg.wallet}</div>
              {msg.preferences && (
                <div className="text-sm mt-1">
                  Preferences: {msg.preferences}
                </div>
              )}
            </div>
          ))}
          {messages.length === 0 && (
            <div className="text-gray-500 text-center py-4">
              No requests yet
            </div>
          )}
        </div>
      </div>
    </div>
  )
}