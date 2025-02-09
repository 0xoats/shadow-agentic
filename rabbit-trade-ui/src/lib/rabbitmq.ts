import * as amqp from 'amqplib'

const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://guest:guest@localhost:5672'
const QUEUE_NAME = process.env.RABBITMQ_QUEUE || 'input_queue'

async function getConnection() {
  try {
    const connection = await amqp.connect(RABBITMQ_URL)
    return connection
  } catch (error) {
    console.error('Failed to connect to RabbitMQ:', error)
    throw error
  }
}

export async function checkRabbitMQConnection() {
  const connection = await getConnection()
  await connection.close()
}

export async function sendToRabbitMQ(message: any) {
  let connection
  try {
    connection = await getConnection()
    const channel = await connection.createChannel()
    
    await channel.assertQueue(QUEUE_NAME, {
      durable: true
    })
    
    channel.sendToQueue(
      QUEUE_NAME,
      Buffer.from(JSON.stringify(message)),
      {
        persistent: true
      }
    )
    
    await channel.close()
  } catch (error) {
    console.error('Error sending message to RabbitMQ:', error)
    throw error
  } finally {
    if (connection) {
      await connection.close()
    }
  }
}