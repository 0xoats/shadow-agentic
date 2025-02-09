import { NextResponse } from 'next/server'
import { checkRabbitMQConnection } from '@/lib/rabbitmq'

export async function GET() {
  try {
    await checkRabbitMQConnection()
    return NextResponse.json({ status: 'Connected' })
  } catch (error) {
    return NextResponse.json({ status: 'Disconnected' })
  }
}