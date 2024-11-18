import os
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from django.conf import settings
from django.apps import apps
import re

# 모델 및 토크나이저 로드 함수
def load_model_and_tokenizer():
    model_path = os.path.join(settings.BASE_DIR, '/home/doa/PPBL/swukeepers_be/models/model_weight.bin')
    model = BertForSequenceClassification.from_pretrained('bert-base-multilingual-cased', num_labels=2)
    tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')
    
    # 모델 가중치 로드
    try:
        state_dict = torch.load(model_path)
        model.load_state_dict(state_dict, strict=False)
    except Exception as e:
        print("모델 로드 실패:", e)
    
    return model, tokenizer

def predict(text):
    # `apps.get_app_config`을 사용해 전역 모델과 토크나이저에 접근
    model = apps.get_app_config('api').model
    tokenizer = apps.get_app_config('api').tokenizer
    model.eval()
    
    inputs = tokenize_data(
        text,
        tokenizer,
    )
    
    # GPU 사용 설정
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    inputs = {key: val.to(device) for key, val in inputs.items()}
    
    # 예측
    with torch.no_grad():
        outputs = model(**inputs)
    
    # 결과 해석
    prediction = torch.argmax(outputs.logits, dim=-1).item()
    is_curse = prediction == 1  # 예: 1이면 욕설, 0이면 비욕설
    
    return is_curse

# 데이터 토크나이징 함수
def tokenize_data(texts, tokenizer, max_len=128):
    # texts가 리스트인 경우 각 요소에 대해 반복 제거 적용
    if isinstance(texts, list):
        texts = [re.sub(r'ㅋ{2,}', '', text) for text in texts]
    else:
        texts = re.sub(r'ㅋ{2,}', '', texts)

    inputs = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=max_len,
        return_tensors='pt'
    )
    return inputs
