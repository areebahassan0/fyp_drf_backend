from django.shortcuts import render
# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utilities.chatbot import generate_final_response
from rest_framework.permissions import AllowAny

class ChatbotAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        user_input = request.data.get('message', '').strip()
        if not user_input:
            return Response({'error': 'No message provided.'}, status=status.HTTP_400_BAD_REQUEST)

        chat_history = request.session.get('chat_history', [])
 
        bot_reply, chat_history = generate_final_response(user_input, chat_history)

        request.session['chat_history'] = chat_history

        return Response({'reply': bot_reply})
