"""
API endpoints for n8n automation integration
"""
import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404

from users.models import Conversation, Message


logger = logging.getLogger(__name__)


class SendAutoMessageView(View):
    """
    Secure API endpoint for n8n to send automated responses.
    Requires X-AUTO-SECRET header matching settings.N8N_SECRET_KEY.
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        # Validate secret header
        secret_header = request.headers.get('X-AUTO-SECRET')
        if not secret_header or secret_header != settings.N8N_SECRET_KEY:
            logger.warning("Unauthorized attempt to send auto-message")
            return JsonResponse(
                {'error': 'Unauthorized'},
                status=401
            )
        
        try:
            # Parse request body
            data = json.loads(request.body)
            
            conversation_id = data.get('conversation_id')
            content = data.get('message', '').strip()
            
            if not conversation_id or not content:
                return JsonResponse(
                    {'error': 'Missing required fields: conversation_id, message'},
                    status=400
                )
            
            # Get conversation
            conversation = get_object_or_404(Conversation, pk=conversation_id)
            
            # Create automated message from farmer
            message = Message.objects.create(
                conversation=conversation,
                sender=conversation.farmer,
                content=content,
                is_automated=True
            )
            
            logger.info(
                f"Automated message created for conversation {conversation_id} "
                f"from farmer {conversation.farmer.username}"
            )
            
            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'conversation_id': conversation_id,
                'content': content,
                'timestamp': message.timestamp.isoformat()
            }, status=201)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in auto-message request")
            return JsonResponse(
                {'error': 'Invalid JSON'},
                status=400
            )
        except Exception as e:
            logger.error(f"Error creating automated message: {str(e)}")
            return JsonResponse(
                {'error': 'Internal server error'},
                status=500
            )


class HealthCheckView(View):
    """Health check endpoint for n8n to verify API availability"""
    
    def get(self, request):
        secret_header = request.headers.get('X-AUTO-SECRET')
        if not secret_header or secret_header != settings.N8N_SECRET_KEY:
            return JsonResponse(
                {'error': 'Unauthorized'},
                status=401
            )
        
        return JsonResponse({
            'status': 'healthy',
            'n8n_enabled': settings.N8N_ENABLED,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        })
