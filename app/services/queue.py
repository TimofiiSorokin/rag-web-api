import json
import logging
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class SQSService:
    """Service for SQS queue operations"""

    def __init__(self, endpoint_url: Optional[str] = None):
        """Initialize SQS client"""
        # Use provided endpoint_url or fall back to settings
        self.endpoint_url = endpoint_url or settings.SQS_ENDPOINT_URL

        self.sqs_client = boto3.client(
            "sqs",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.queue_name = settings.SQS_QUEUE_NAME
        self.queue_url = None

        logger.info(f"SQSService initialized with endpoint: {self.endpoint_url}")
        logger.info(f"SQSService queue: {self.queue_name}")

    def create_queue_if_not_exists(self) -> bool:
        """Create SQS queue if it doesn't exist"""
        try:
            # Check if queue already exists
            response = self.sqs_client.get_queue_url(QueueName=self.queue_name)
            self.queue_url = response["QueueUrl"]
            logger.info(f"Queue already exists: {self.queue_url}")
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                # Queue doesn't exist, create it
                try:
                    response = self.sqs_client.create_queue(
                        QueueName=self.queue_name,
                        Attributes={
                            "VisibilityTimeout": "300",  # 5 minutes
                            "MessageRetentionPeriod": "1209600",  # 14 days
                        },
                    )
                    self.queue_url = response["QueueUrl"]
                    logger.info(f"Created queue: {self.queue_url}")
                    return True

                except ClientError as create_error:
                    logger.error(f"Failed to create queue: {create_error}")
                    return False
            else:
                logger.error(f"Error checking queue existence: {e}")
                return False

    def send_message(self, message_body: Dict[str, Any]) -> bool:
        """Send message to SQS queue"""
        try:
            if not self.queue_url:
                if not self.create_queue_if_not_exists():
                    return False

            # Convert message to JSON string
            message_json = json.dumps(message_body)

            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url, MessageBody=message_json
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
                if not self.create_queue_if_not_exists():
                    return []

            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=20,  # Long polling
            )

            messages = response.get("Messages", [])
            logger.info(f"Received {len(messages)} messages")
            return messages

        except ClientError as e:
            logger.error(f"Failed to receive messages: {e}")
            return []

    def delete_message(self, receipt_handle: str) -> bool:
        """Delete message from SQS queue"""
        try:
            if not self.queue_url:
                logger.error("Queue URL not available")
                return False

            self.sqs_client.delete_message(
                QueueUrl=self.queue_url, ReceiptHandle=receipt_handle
            )

            logger.info("Message deleted successfully")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete message: {e}")
            return False

    def get_queue_attributes(self) -> Dict[str, Any]:
        """Get queue attributes"""
        try:
            if not self.queue_url:
                if not self.create_queue_if_not_exists():
                    return {}

            response = self.sqs_client.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=["All"],
            )

            return response.get("Attributes", {})

        except ClientError as e:
            logger.error(f"Failed to get queue attributes: {e}")
            return {}

    def purge_queue(self) -> bool:
        """Purge all messages from SQS queue"""
        try:
            if not self.queue_url:
                if not self.create_queue_if_not_exists():
                    return False

            # Get queue attributes to check if there are messages
            attributes = self.get_queue_attributes()
            approximate_number_of_messages = int(attributes.get("ApproximateNumberOfMessages", 0))
            
            if approximate_number_of_messages == 0:
                logger.info("Queue is already empty")
                return True

            logger.info(f"Purging {approximate_number_of_messages} messages from queue")

            # Purge all messages
            self.sqs_client.purge_queue(QueueUrl=self.queue_url)

            logger.info("Queue purged successfully")
            return True

        except ClientError as e:
            logger.error(f"Failed to purge queue: {e}")
            return False
