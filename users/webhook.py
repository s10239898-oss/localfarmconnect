"""
Webhook integration for n8n automation
Handles triggering n8n workflows when messages are created.
"""
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from django.conf import settings


logger = logging.getLogger(__name__)


def create_retry_session(
    retries=3,
    backoff_factor=0.5,
    status_forcelist=(500, 502, 503, 504),
):
    """Create a requests session with retry logic"""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def trigger_n8n_webhook(message):
    """
    Trigger n8n webhook when a new message is created.
    
    This function is called from the Message model's save method.
    It runs asynchronously (via thread) to not block the user experience.
    """
    # Only trigger for buyer messages (not automated responses)
    if message.is_automated:
        return
    
    # Only trigger if n8n is enabled
    if not settings.N8N_ENABLED:
        return
    
    # Only trigger for buyer -> farmer messages
    if message.sender != message.conversation.buyer:
        return
    
    try:
        conversation = message.conversation
        product = conversation.product
        
        payload = {
            'conversation_id': conversation.id,
            'sender': 'buyer',
            'sender_username': message.sender.username,
            'farmer_id': conversation.farmer.id,
            'farmer_username': conversation.farmer.username,
            'product_id': product.id if product else None,
            'product_name': product.name if product else None,
            'message': message.content,
            'timestamp': message.timestamp.isoformat()
        }
        
        session = create_retry_session(retries=2)
        
        response = session.post(
            settings.N8N_WEBHOOK_URL,
            json=payload,
            timeout=settings.N8N_WEBHOOK_TIMEOUT,
            headers={
                'Content-Type': 'application/json',
                'X-Source': 'localfarmconnect'
            }
        )
        
        if response.status_code == 200:
            logger.info(
                f"Successfully triggered n8n webhook for conversation {conversation.id}"
            )
        else:
            logger.warning(
                f"n8n webhook returned status {response.status_code} for conversation {conversation.id}"
            )
            
    except requests.exceptions.Timeout:
        logger.error(
            f"Timeout triggering n8n webhook for conversation {message.conversation.id}"
        )
    except requests.exceptions.ConnectionError:
        logger.error(
            f"Connection error triggering n8n webhook for conversation {message.conversation.id}. "
            f"Is n8n running at {settings.N8N_WEBHOOK_URL}?"
        )
    except Exception as e:
        logger.error(
            f"Error triggering n8n webhook for conversation {message.conversation.id}: {str(e)}"
        )


def trigger_n8n_webhook_async(message):
    """
    Trigger n8n webhook in a background thread.
    This ensures the user experience is not blocked.
    """
    import threading
    
    thread = threading.Thread(
        target=trigger_n8n_webhook,
        args=(message,),
        daemon=True
    )
    thread.start()
    logger.debug(f"Started n8n webhook thread for message {message.id}")
