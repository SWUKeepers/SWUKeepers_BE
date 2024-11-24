from django.http import HttpResponse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit  # 긴 문자열을 줄바꿈 처리
from .models import ChatRoom
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer
<<<<<<< HEAD
from .models import ChatRoom
from api.utils.bert_load import predict_with_cyberbullying_check  # 사이버불링 함수 import
import torch  # torch 명시적 import
#from .utils.bert_load import get_analysis_result
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
=======
>>>>>>> develop

# 한글 폰트 등록
font_path = "/home/minji/SWUKeepers_BE/static/fonts/NanumGothic-Regular.ttf"
pdfmetrics.registerFont(TTFont("NanumGothic", font_path))

def draw_wrapped_text(pdf, x, y, text, max_width, font_name="NanumGothic", font_size=12):
    """
    긴 문자열을 주어진 너비에 맞게 줄 바꿈하여 PDF에 그리는 함수.
    """
    pdf.setFont(font_name, font_size)
    lines = simpleSplit(text, font_name, font_size, max_width)  # 줄 바꿈 처리
    for line in lines:
        pdf.drawString(x, y, line)
        y -= 15  # 줄 간격 조정
    return y

# PDF 다운로드 기능
def download_cyberbullying_pdf(request, pk):
    """
    PDF 생성 및 다운로드를 처리하는 뷰.
    사이버불링 여부가 Yes인 채팅방의 정보를 PDF로 생성하여 제공.
    """
    # ChatRoom 객체 가져오기
    try:
        chat_room = ChatRoom.objects.get(pk=pk, is_cyberbullying=True)
    except ChatRoom.DoesNotExist:
        return HttpResponse("Chat room not found or not marked as cyberbullying.", status=404)

    # PDF 응답 생성
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={chat_room.room_name}_cyberbullying_report.pdf"

    # PDF 생성
    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setFont("NanumGothic", 12)  # 등록된 한글 폰트를 사용

    # PDF 제목
    pdf.drawString(100, 800, "Cyberbullying Report")
    pdf.drawString(100, 780, f"Room Name: {chat_room.room_name}")
    pdf.drawString(100, 760, f"Saved At: {chat_room.saved_at.strftime('%Y-%m-%d %H:%M:%S')}")
    y = draw_wrapped_text(pdf, 100, 740, f"Room Hash: {chat_room.room_hash}", max_width=400)

    # 메시지 내용 추가
    pdf.drawString(100, y - 20, "Messages:")
    y -= 40
    for message in chat_room.messages.all():
        message_text = f"- {message.sender}: {message.content[:50]}{'...' if len(message.content) > 50 else ''}"
        y = draw_wrapped_text(pdf, 100, y, message_text, max_width=400)
        if y < 50:  # 페이지 하단에 도달하면 새 페이지로 이동
            pdf.showPage()
            pdf.setFont("NanumGothic", 12)  # 새 페이지에서도 폰트 설정 필요
            y = 800

    # PDF 저장
    pdf.save()

    return response


# 파일 업로드 API
class FileUploadView(APIView):
    """
    파일 업로드를 처리하는 API View.
    """
    def post(self, request, *args, **kwargs):
        # ChatRoomSerializer를 이용해 파일 데이터 처리
        serializer = ChatRoomSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
<<<<<<< HEAD
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
=======
            chat_room = serializer.save()
            return Response(
                {"message": "File uploaded successfully!", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
>>>>>>> develop
