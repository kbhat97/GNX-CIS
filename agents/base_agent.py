#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines the base class for all agents.

It provides a common interface for interacting with the message bus.
"""

import logging
from typing import Any, Callable, Dict

from core.message_bus import message_bus

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all agents."""

    def __init__(self, agent_name: str):
        """Initialize the base agent.

        Args:
            agent_name: The name of the agent.
        """
        self.agent_name = agent_name
        self.message_bus = message_bus

    def publish(self, topic_name: str, message_data: Dict[str, Any]):
        """Publish a message to a topic.

        Args:
            topic_name: The name of the topic to publish to.
            message_data: The message data to publish.
        """
        logger.info(f"[{self.agent_name}] Publishing message to topic: {topic_name}")
        self.message_bus.publish(topic_name, message_data)

    def subscribe(self, topic_name: str, subscription_name: str, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to a topic.

        Args:
            topic_name: The name of the topic to subscribe to.
            subscription_name: The name of the subscription.
            callback: The callback function to process messages.
        """
        logger.info(f"[{self.agent_name}] Subscribing to topic: {topic_name} with subscription: {subscription_name}")
        self.message_bus.subscribe(topic_name, subscription_name, callback)
