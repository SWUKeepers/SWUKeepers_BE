from django.http import HttpResponse, FileResponse, Http404
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
import os
from .models import ChatRoom
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer

# 한글 폰트 등록
font_path = "/root/SWUKeepers_BE/static/fonts/NanumGothic-Regular.ttf"
if not os.path.exists(font_path):  # 폰트 경로 확인
    raise FileNotFoundError(f"Font file not found at {font_path}")

pdfmetrics.registerFont(TTFont("NanumGothic", font_path))


def draw_wrapped_text(pdf, x, y, text, max_width, font_name="NanumGothic", font_size=12):
    """
    긴 문자열을 주어진 너비에 맞게 줄 바꿈하여 PDF에 그리는 함수.
    """
    pdf.setFont(font_name, font_size)
    lines = simpleSplit(text, font_name, font_size, max_width)
    for line in lines:
        pdf.drawString(x, y, line)
        y -= 15
    return y


def upload_file(request):
    """
    이미 생성된 PDF 파일을 반환하는 함수.
    """
    try:
        file_path = "example.pdf"  # 반환할 PDF 파일의 경로
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{file_path} not found.")
        with open(file_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="example.pdf"'
            return response
    except FileNotFoundError:
        raise Http404("The requested file does not exist.")


def download_cyberbullying_pdf(request, pk):
    """
    PDF 생성 및 다운로드를 처리하는 뷰.
    """
    try:
        chat_room = ChatRoom.objects.get(pk=pk, is_cyberbullying=True)
    except ChatRoom.DoesNotExist:
        raise Http404("Chat room not found or not marked as cyberbullying.")

    # PDF 저장 경로 설정
    pdf_dir = "media/pdfs/"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"{chat_room.room_hash}_cyberbullying_report.pdf")

    # PDF 생성
    if not os.path.exists(pdf_path):  # 파일이 없는 경우 새로 생성
        pdf = canvas.Canvas(pdf_path, pagesize=A4)
        pdf.setFont("NanumGothic", 12)

        pdf.drawString(100, 800, "Cyberbullying Report")
        pdf.drawString(100, 780, f"Room Name: {chat_room.room_name}")
        pdf.drawString(100, 760, f"Saved At: {chat_room.saved_at.strftime('%Y-%m-%d %H:%M:%S')}")
        y = draw_wrapped_text(pdf, 100, 740, f"Room Hash: {chat_room.room_hash}", max_width=400)

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

    # 생성된 PDF 파일 반환
    try:
        return FileResponse(open(pdf_path, "rb"), content_type="application/pdf")
    except FileNotFoundError:
        raise Http404("PDF file could not be generated.")


class FileUploadView(APIView):
    def post(self, request, *args, **kwargs):
        """
        파일 업로드 및 분석 처리
        """
        if "file" not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES["file"]
        serializer = ChatRoomSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            try:
                chat_room = serializer.save()
                chat_room.analyze_cyberbullying()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
