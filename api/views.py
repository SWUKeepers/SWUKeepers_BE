from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer
from .models import ChatRoom
from api.utils.bert_load import predict_with_cyberbullying_check  # 사이버불링 함수 import
import torch  # torch 명시적 import
#from .utils.bert_load import get_analysis_result
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

class FileUploadView(APIView):
    def post(self, request, *args, **kwargs):
        if "file" not in request.FILES:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES["file"]
        serializer = ChatRoomSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            try:
                chat_room = serializer.save()
                chat_room.analyze_cyberbullying()  # 사이버불링 분석 수행
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"Error while processing file: {e}")
                return Response(
                    {"detail": "파일 처리 중 오류가 발생했습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            print("Validation errors: ", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class ChatRoomBullyingMessages(APIView):
    def get(self, request, pk):
        try:
            chat_room = ChatRoom.objects.get(pk=pk)
            messages = chat_room.messages.filter(is_curse=True)  # 사이버 불링 메시지만 필터링
            data = [
                {"id": msg.id, "sender": msg.sender, "content": msg.content, "time_sent": msg.time_sent}
                for msg in messages
            ]
            return JsonResponse({"chat_room": chat_room.room_name, "messages": data}, safe=False)
        except ChatRoom.DoesNotExist:
            return JsonResponse({"error": "Chat room not found"}, status=404)
        
class DownloadBullyingPDF(APIView):
    def get(self, request, pk):
        # 특정 ChatRoom 객체 가져오기
        chat_room = get_object_or_404(ChatRoom, pk=pk)  # 여기에서 데이터가 없으면 404 발생
        messages = chat_room.messages.filter(is_curse=True)

        # PDF 응답 준비
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{chat_room.room_name}_bullying.pdf"'

        # PDF 생성
        p = canvas.Canvas(response)
        p.setFont("Helvetica", 14)
        p.drawString(50, 800, f"Chatroom: {chat_room.room_name}")
        p.drawString(50, 780, f"Hash Value: {chat_room.room_hash}")
        p.drawString(50, 760, f"Cyberbullying Detected: {'Yes' if chat_room.is_cyberbullying else 'No'}")

        # 메시지 출력
        y_position = 740
        for msg in messages:
            if y_position < 50:
                p.showPage()
                y_position = 800
            p.drawString(50, y_position, f"Sender: {msg.sender}, Content: {msg.content}")
            y_position -= 40

        p.save()
        return response

def chatroom_result_api(request, pk):
    chat_room = get_object_or_404(ChatRoom, pk=pk)
    messages = chat_room.messages.filter(is_curse=True)
    data = {
        "chat_room": {
            "id": chat_room.id,
            "name": chat_room.room_name,
            "hash": chat_room.room_hash,
            "is_cyberbullying": chat_room.is_cyberbullying,
            "saved_at": chat_room.saved_at,
        },
        "messages": [
            {"id": msg.id, "sender": msg.sender, "content": msg.content, "time_sent": msg.time_sent}
            for msg in messages
        ],
    }
    return JsonResponse(data)