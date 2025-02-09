import json
import re
import os
import pika
from dotenv import load_dotenv

# Import the recommendation chain
from chains.rag_recommendation_chain import RAGRecommendationChain

# Load environment variables from .env
load_dotenv()

# RabbitMQ connection configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')
INPUT_QUEUE = os.getenv('INPUT_QUEUE', 'input_queue')
OUTPUT_QUEUE = os.getenv('OUTPUT_QUEUE', 'output_queue')

# Regex pattern for a Solana wallet address
SOLANA_ADDRESS_REGEX = r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"

def get_rabbitmq_connection():
    """Create and return a RabbitMQ connection"""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials
    )
    return pika.BlockingConnection(parameters)

def process_message(ch, method, properties, body):
    """Callback function that processes each incoming message."""
    try:
        message_text = body.decode('utf-8')
        print(f"Received message: {message_text}")

        # Extract Solana wallet address
        match = re.search(SOLANA_ADDRESS_REGEX, message_text)
        if not match:
            error_message = ("Essential information missing: please provide a valid Solana wallet address "
                           "along with any trade preferences.")
            print(error_message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        wallet_address = match.group(0)
        print(f"Extracted wallet address: {wallet_address}")

        # Extract preferences
        user_preferences = message_text.replace(wallet_address, "").strip()
        if not user_preferences:
            user_preferences = "default"
        print(f"Extracted user preferences: {user_preferences}")

        # Here you would typically instantiate and run your recommendation chain
        # For now, we'll just print that we would process it
        print(f"Would process recommendation chain for wallet {wallet_address} with preferences {user_preferences}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"Error processing message: {e}")
        # Negative acknowledgment in case of error
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def run_consumer():
    """Main function to run the RabbitMQ consumer."""
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    # Declare the input queue
    channel.queue_declare(queue=INPUT_QUEUE, durable=True)
    print(f"Listening for messages on queue '{INPUT_QUEUE}'...")

    # Configure consumer
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=INPUT_QUEUE, on_message_callback=process_message)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Consumer interrupted. Shutting down.")
        channel.stop_consuming()
    finally:
        if connection and not connection.is_closed:
            connection.close()
