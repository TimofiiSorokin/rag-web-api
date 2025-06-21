import boto3
import json
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class SQSService:
    """Service for SQS queue operations"""
    
    def __init__(self, endpoint_url: Optional[str] = None):
        """Initialize SQS client"""
        # Use provided endpoint_url or fall back to settings
        self.endpoint_url = endpoint_url or settings.SQS_ENDPOINT_URL
        
        self.sqs_client = boto3.client(
            'sqs',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.queue_name = settings.SQS_QUEUE_NAME
        self.queue_url = None
        
        logger.info(f"SQSService initialized with endpoint: {self.endpoint_url}")
        logger.info(f"SQSService queue: {self.queue_name}")
        
    def create_queue_if_not_exists(self) -> Optional[str]:
        """Create SQS queue if it doesn't exist and return queue URL"""
        try:
            # Try to get queue URL first
            response = self.sqs_client.get_queue_url(QueueName=self.queue_name)
            self.queue_url = response['QueueUrl']
            logger.info(f"Queue {self.queue_name} already exists")
            return self.queue_url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AWS.SimpleQueueService.NonExistentQueue':
                try:
                    # Create queue
                    response = self.sqs_client.create_queue(
                        QueueName=self.queue_name,
                        Attributes={
                            'VisibilityTimeout': '300',  # 5 minutes
                            'MessageRetentionPeriod': '86400',  # 1 day
                            'ReceiveMessageWaitTimeSeconds': '20'  # Long polling
                        }
                    )
                    self.queue_url = response['QueueUrl']
                    logger.info(f"Created queue {self.queue_name}")
                    return self.queue_url
                    
                except ClientError as create_error:
                    logger.error(f"Failed to create queue: {create_error}")
                    return None
            else:
                logger.error(f"Error checking queue: {e}")
                return None
    
    def send_message(self, message_body: Dict[str, Any]) -> bool:
        """Send message to SQS queue"""
        try:
            if not self.queue_url:
                self.queue_url = self.create_queue_if_not_exists()
                if not self.queue_url:
                    return False
            
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body)
            )
            
            logger.info(f"Message sent successfully: {response['MessageId']}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def receive_messages(self, max_messages: int = 10) -> list:
        """Receive messages from SQS queue"""
        try:
            if not self.queue_url:
                self.queue_url = self.create_queue_if_not_exists()
                if not self.queue_url:
                    return []
            
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=20  # Long polling
            )
            
            messages = response.get('Messages', [])
            logger.info(f"Received {len(messages)} messages")
            return messages
            
        except ClientError as e:
            logger.error(f"Failed to receive messages: {e}")
            return []
    
    def delete_message(self, receipt_handle: str) -> bool:
        """Delete message from SQS queue"""
        try:
            if not self.queue_url:
                return False
            
            self.sqs_client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            
            logger.info("Message deleted successfully")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete message: {e}")
            return False 