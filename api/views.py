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
from api.utils.bert_load import (
    predict_with_cyberbullying_check,
)  # 사이버불링 함수 import
from django.contrib.staticfiles import finders

font_path = finders.find("fonts/NanumGothic.ttf")

pdfmetrics.registerFont(TTFont("/NanumGothic.ttf", font_path))

if font_path:
    pdfmetrics.registerFont(TTFont("CustomFont", font_path))
    print(f"Font 'CustomFont' registered successfully from {font_path}")
else:
    print("Font file not found: fonts/custom_font.ttf")


def draw_wrapped_text(
    pdf, x, y, text, max_width, font_name="NanumGothic", font_size=12
):
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
    try:
        chat_room = ChatRoom.objects.get(pk=pk, is_cyberbullying=True)
    except ChatRoom.DoesNotExist:
        return HttpResponse(
            "Chat room not found or not marked as cyberbullying.", status=404
        )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f"attachment; filename={chat_room.room_name}_cyberbullying_report.pdf"
    )

    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setFont("NanumGothic", 12)

    pdf.drawString(100, 800, "Cyberbullying Report")
    pdf.drawString(100, 780, f"Room Name: {chat_room.room_name}")
    pdf.drawString(
        100, 760, f"Saved At: {chat_room.saved_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    y = draw_wrapped_text(
        pdf, 100, 740, f"Room Hash: {chat_room.room_hash}", max_width=400
    )

    pdf.drawString(100, y - 20, "Messages:")
    y -= 40
    for message in chat_room.messages.all():
        message_text = f"- {message.sender}: {message.content[:50]}{'...' if len(message.content) > 50 else ''}"
        y = draw_wrapped_text(pdf, 100, y, message_text, max_width=400)
        if y < 50:
            pdf.showPage()
            pdf.setFont("NanumGothic", 12)
            y = 800

    pdf.save()

    return response


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
                chat_room.analyze_cyberbullying()  # 사이버불링 분석 및 저장
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"Error while processing file: {e}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            print("Validation errors: ", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
