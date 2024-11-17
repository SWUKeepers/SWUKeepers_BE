import os
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from django.conf import settings
from django.apps import apps
import re
import pandas as pd
import transformers
from sklearn.model_selection import train_test_split
from torch.optim import AdamW
import spacy
import json
import sys

# 출력을 생략하지 않도록 설정
pd.set_option('display.max_colwidth', None)  # Pandas 사용 시 생략 방지
sys.setrecursionlimit(10000)  # 재귀 제한을 높여서 긴 출력도 표시되도록


# 모델 및 토크나이저 로드 함수
def load_model_and_tokenizer():
    model_path = os.path.join(settings.BASE_DIR, 'swukeepers_be/models/model_weight.bin')
    model = BertForSequenceClassification.from_pretrained('bert-base-multilingual-cased', num_labels=2)
    tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')
    
    # 모델 가중치 로드
    try:
        state_dict = torch.load(model_path, weights_only=True)
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


# 욕설 리스트를 json 파일에서 불러오는 함수
def get_abuse_word():
    with open('swukeepers_be/models/curse (1).json') as json_file:
        json_data = json.load(json_file)
        return dict(json_data)

# 욕설을 포함하고 있는지 확인하는 함수
def contains_abuse_word(sentence, abuse_words):
    for values in abuse_words.values():
        for word in values:
            if word in sentence:
                return True
    return False

# 'ㅋ' 또는 'ㅎ'가 포함되어 있는지 확인하는 함수
def contains_laughing_symbols(sentence):
    return 'ㅋ' in sentence or 'ㅎ' in sentence

# BERT 모델을 이용한 감정 예측
def predict_sentiment(model, tokenizer, text, device, abuse_words):
    model.eval()
    inputs = tokenize_data(text, tokenizer)
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        _, predicted = torch.max(outputs.logits, dim=1)

    label = predicted.cpu().item()
    return "긍정" if label == 1 else "부정"

# 사이버불링 여부를 판단하는 함수
def check_cyberbullying(sentiments):
    positive_count = sentiments.count("긍정")
    negative_count = sentiments.count("부정")
    positive_ratio = positive_count / len(sentiments) if len(sentiments) > 0 else 0
    negative_ratio = negative_count / len(sentiments) if len(sentiments) > 0 else 0

    # 사이버불링 조건
    is_cyberbullying = (
        negative_ratio > 0.6 or                  # 부정 비율이 60% 이상인 경우
        any(sentiments[i:i+3] == ["부정", "부정", "부정"] for i in range(len(sentiments) - 2)) or  # 부정이 연속 3회 이상 나오는 경우
        (positive_ratio < 0.5 and positive_count < negative_count)  # 긍정 비율이 낮고 부정이 많을 경우
    )
    
    # 결과 출력
    return "사이버불링" if is_cyberbullying else "사이버불링이 아님"

# 기존 predict 함수에 사이버불링 여부 검사 추가
# 기존 predict 함수에 사이버불링 여부 검사 추가
def predict_with_cyberbullying_check(sentences, tokenizer, model, device):
    abuse_words = get_abuse_word()
    sentiments = []  # 문장별 분석 결과 저장
    analysis_results = []

    for sentence in sentences:
        # 욕설 여부 확인
        contains_abuse = contains_abuse_word(sentence, abuse_words)
        contains_laughing = contains_laughing_symbols(sentence)

        # 감정 분석 결과
        if contains_abuse or contains_laughing:
            sentiment = "긍정"
        else:
            sentiment = predict_sentiment(model, tokenizer, sentence, device, abuse_words)

        # is_curse 여부 저장 (욕설 포함 여부)
        is_curse = contains_abuse

        # 결과 저장
        sentiments.append({"sentence": sentence, "sentiment": sentiment, "is_curse": is_curse})

    # 사이버불링 여부 판단
    bullying_result = check_cyberbullying([s["sentiment"] for s in sentiments])

    return {
        "cyberbullying": bullying_result,
        "details": sentiments,  # 문장별 상세 결과 포함
    }

