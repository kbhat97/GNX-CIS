#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module implements a message bus for inter-agent communication.

It uses Google Cloud Pub/Sub for production environments and a local in-memory queue for development.
"""

import json
import logging
from typing import Any, Callable, Dict, Optional
from concurrent.futures import TimeoutError

from config import config

try:
    from google.cloud import pubsub_v1
except ImportError:
    pubsub_v1 = None

logger = logging.getLogger(__name__)


class MessageBus:
    """A message bus for asynchronous inter-agent communication."""

    def __init__(self):
        """Initialize the message bus."""
        self.is_production = config.environment == "production" and pubsub_v1 is not None
        if self.is_production:
            self.publisher = pubsub_v1.PublisherClient()
            self.subscriber = pubsub_v1.SubscriberClient()
            self.project_id = config.project_id
        else:
            self.local_queue = {}
        logger.info(f"Message bus initialized in {"production" if self.is_production else "development"} mode.")

    def publish(self, topic_name: str, message_data: Dict[str, Any]):
        """
        Publish a message to a topic.

        Args:
            topic_name: The name of the topic to publish to.
            message_data: The message data to publish.
        """
        if self.is_production:
            topic_path = self.publisher.topic_path(self.project_id, topic_name)
            data = json.dumps(message_data).encode("utf-8")
            future = self.publisher.publish(topic_path, data)
            try:
                future.result(timeout=10)
                logger.info(f"Message published to topic {topic_name}.")
            except TimeoutError:
                logger.error(f"Publishing to topic {topic_name} timed out.")
        else:
            if topic_name not in self.local_queue:
                self.local_queue[topic_name] = []
            self.local_queue[topic_name].append(message_data)
            logger.info(f"Message added to local queue for topic {topic_name}.")

    def subscribe(self, topic_name: str, subscription_name: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Subscribe to a topic and process messages with a callback.

        Args:
            topic_name: The name of the topic to subscribe to.
            subscription_name: The name of the subscription.
            callback: The callback function to process messages.
        """
        if self.is_production:
            topic_path = self.publisher.topic_path(self.project_id, topic_name)
            subscription_path = self.subscriber.subscription_path(self.project_id, subscription_name)
            try:
                self.subscriber.create_subscription(name=subscription_path, topic=topic_path)
                logger.info(f"Subscription {subscription_name} created for topic {topic_name}.")
            except Exception as e:
                logger.info(f"Subscription {subscription_name} already exists.")

            def message_callback(message):
                try:
                    data = json.loads(message.data.decode("utf-8"))
                    callback(data)
                    message.ack()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message data: {e}")
                    message.nack()

            streaming_pull_future = self.subscriber.subscribe(subscription_path, callback=message_callback)
            logger.info(f"Listening for messages on {subscription_path}...")

            try:
                streaming_pull_future.result(timeout=60) # Keep the subscription active
            except TimeoutError:
                streaming_pull_future.cancel()
                logger.info(f"Subscription {subscription_name} timed out.")
        else:
            if topic_name in self.local_queue:
                for message_data in self.local_queue[topic_name]:
                    callback(message_data)
                self.local_queue[topic_name] = [] # Clear the queue after processing


message_bus = MessageBus()
