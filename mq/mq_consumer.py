# mq/mq_consumer.py
import json
import re
import os
import pika
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Import the recommendation chain (assumed to have been updated to accept user preferences)
from chains.rag_recommendation_chain import RAGRecommendationChain

# RabbitMQ connection configuration (set these in your .env file or use defaults)
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')
INPUT_QUEUE = os.getenv('INPUT_QUEUE', 'input_queue')
OUTPUT_QUEUE = os.getenv('OUTPUT_QUEUE', 'output_queue')  # Optional for results

# Create connection credentials and parameters
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
parameters = pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    port=RABBITMQ_PORT,
    credentials=credentials
)

# Regex pattern for a Solana wallet address (typically Base58, 32-44 characters)
SOLANA_ADDRESS_REGEX = r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"

def process_message(ch, method, properties, body):
    """Callback function that processes each incoming message."""
    message_text = body.decode('utf-8')
    print(f"Received message: {message_text}")

    # Try to extract a Solana wallet address using regex
    match = re.search(SOLANA_ADDRESS_REGEX, message_text)
    if not match:
        # Essential information missing: reply with a prompt (here we simply log it)
        error_message = ("Essential information missing: please provide a valid Solana wallet address "
                         "along with any trade preferences.")
        print(error_message)
        # Optionally, you might publish this error message to an output queue or notify the user
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Extract the wallet address
    wallet_address = match.group(0)
    print(f"Extracted wallet address: {wallet_address}")

    # Remove the wallet address from the message text to capture remaining preferences
    user_preferences = message_text.replace(wallet_address, "").strip()
    if not user_preferences:
        user_preferences = "default"  # or leave empty if no specific preferences were provided
    print(f"Extracted user preferences: {user_preferences}")

    # Instantiate the recommendation chain (pipeline) and pass the parameters
    chain = RAGRecommendationChain(wallet_address, user_preferences)
    try:
        print("Invoking pipeline...")
        # Here we assume the generate_recommendations method is updated to accept user_preferences.
        result = chain.generate_recommendations()
        print("Pipeline result:")
        print(json.dumps(result, indent=2))
        
        # Optional: publish the result to an output queue
        # channel.basic_publish(exchange='', routing_key=OUTPUT_QUEUE, body=json.dumps(result))
    except Exception as e:
        print(f"Error processing pipeline: {e}")
    
    # Acknowledge that the message has been processed
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    """Main function to set up the RabbitMQ consumer."""
    # Establish connection to RabbitMQ
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Declare the input queue (durable for persistence)
    channel.queue_declare(queue=INPUT_QUEUE, durable=True)
    print(f"Listening for messages on queue '{INPUT_QUEUE}'...")

    # Start consuming messages from the queue
    channel.basic_consume(queue=INPUT_QUEUE, on_message_callback=process_message)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Consumer interrupted. Shutting down.")
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
