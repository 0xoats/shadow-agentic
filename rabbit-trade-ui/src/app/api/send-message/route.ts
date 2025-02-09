// src/app/api/send-message/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { sendToRabbitMQ } from '@/lib/rabbitmq'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    if (!body.wallet) {
      return NextResponse.json(
        { error: 'Wallet address is required' },
        { status: 400 }
      )
    }

    await sendToRabbitMQ(body)
    return NextResponse.json({ status: 'success' })
  } catch (error) {
    console.error('Error sending message:', error)
    return NextResponse.json(
      { error: 'Failed to send message' },
      { status: 500 }
    )
  }
}