from dotenv import load_dotenv
import argparse
import os
import pika
from mq.mq_consumer import run_consumer,get_rabbitmq_connection 

def send_to_queue(wallet_address: str, preferences: str):
    """Send wallet address and preferences to RabbitMQ queue"""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Declare queue
        channel.queue_declare(queue="input_queue", durable=True)
        
        # Combine wallet and preferences into message
        message = f"{wallet_address} {preferences}"
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key="input_queue",
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2  # Make message persistent
            )
        )
        
        print(f"\nSuccessfully sent message:")
        print(f"Wallet: {wallet_address}")
        print(f"Preferences: {preferences}")
        
    except Exception as e:
        print(f"\nError sending message: {e}")
    finally:
        if connection and not connection.is_closed:
            connection.close()

def main():
    parser = argparse.ArgumentParser(description='RabbitMQ Producer/Consumer')
    parser.add_argument('--mode', choices=['producer', 'consumer'], required=True,
                      help='Run as producer or consumer')
    parser.add_argument('--wallet', help='Wallet address (required for producer)')
    parser.add_argument('--preferences', help='User preferences (optional for producer)',
                      default='default')
    
    args = parser.parse_args()
    
    if args.mode == 'producer':
        if not args.wallet:
            parser.error("--wallet is required when running as producer")
        send_to_queue(args.wallet, args.preferences)
    else:  # consumer mode
        run_consumer()

if __name__ == "__main__":
    load_dotenv()
    main()