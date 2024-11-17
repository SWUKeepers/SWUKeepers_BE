# 필요한 라이브러리 다 임포트하기

import pandas as pd
import transformers
from sklearn.model_selection import train_test_split
from transformers import BertTokenizer, BertForSequenceClassification
import torch
from torch.optim import AdamW
import os
import re
import spacy
import json
import sys


# 모델 가중치값 위치
model_save_path = '/home/doa/PPBL/swukeepers_be/models/model_weight.bin'

# 출력을 생략하지 않도록 설정
pd.set_option('display.max_colwidth', None)  # Pandas 사용 시 생략 방지
sys.setrecursionlimit(10000)  # 재귀 제한을 높여서 긴 출력도 표시되도록

# BERT 모델 불러오기
model = BertForSequenceClassification.from_pretrained('bert-base-multilingual-cased', num_labels=2)

model_save_path = '/home/doa/PPBL/swukeepers_be/models/model_weight.bin'

# 저장된 가중치 로드하기
try:
    state_dict = torch.load(model_save_path)
    model.load_state_dict(state_dict, strict=False)
except Exception as e:
    print("저장된 모델이 없습니다.")
    print(e)

# GPU 사용 설정
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
print(f"Using device: {device}")

# 옵티마이저 설정
optimizer = AdamW(model.parameters(), lr=2e-5)


# BERT 모델과 토크나이저 로드
tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')

# 데이터 토크나이징 함수
def tokenize_data(texts, tokenizer, max_len=128):
    texts = re.sub(r'ㅋ{2,}', '', texts)  # 'ㅋ' 반복 제거

    inputs = tokenizer.encode_plus(
        texts,
        padding=True,        
        truncation=True,     
        max_length=max_len,  
        return_tensors='pt'  
    )
    return inputs


# 욕설 리스트를 json 파일에서 불러오는 함수
def get_abuse_word():
    with open('/home/doa/PPBL/swukeepers_be/models/curse (1).json') as json_file:
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
def predict_with_cyberbullying_check(sentences, tokenizer, model, device):
    abuse_words = get_abuse_word()
    sentiments = []  # 각 문장의 긍정/부정 결과를 저장할 리스트
    
    for sentence in sentences:
        # 욕설이 있는지 확인
        contains_abuse = contains_abuse_word(sentence, abuse_words)
        # 'ㅋ' 또는 'ㅎ'가 있는지 확인
        contains_laughing = contains_laughing_symbols(sentence)
        
        # 조건에 따른 긍정 처리
        if contains_abuse or contains_laughing:
            sentiment = "긍정"
        else:
            sentiment = predict_sentiment(model, tokenizer, sentence, device, abuse_words)
        
        sentiments.append(sentiment)
        print(f"{sentiment} -> {sentence}")
    
    # 사이버불링 여부 검사
    bullying_result = check_cyberbullying(sentiments)
    print(bullying_result)


# 예시 문장 리스트 - 사이버불링
sentences = [
"[이준혁] [오후 1:15] 야, 너 진짜 왜 이렇게 조용하냐? 아까까지는 잘만 말하더니 지금은 무슨 말도 못 해?  ",
"[김태훈] [오후 1:16] ㅋㅋㅋ 말도 못 하는 거 보니까 자기가 잘못한 건 아나 보네. 맨날 이렇게 아무 말 못 하고 당하고만 있으니까 애들한테 무시 당하지.  ",
"[이준혁] [오후 1:18] 너 어차피 우리가 너한테 관심 가져주는 것도 호의로 해주는 거야. 니가 이런 취급 받는 것도 다 이유가 있지 않냐?  ",
"[박수현] [오후 1:19] 쟤 원래 이래. 그냥 자기가 뭘 잘못했는지 몰라서 입 다물고 있는 거겠지. 네가 이러니까 애들이 더 놀리는 거야.  ",
"[김태훈] [오후 1:21] 진짜 답답하다, 너. 사람들은 다 너 싫어하는데 넌 뭐가 문제인지도 모르고 있겠지?  ",
"[이준혁] [오후 1:23] 진짜 너한테 더 이상 뭐라 말해줄 필요도 없을 것 같아. 너 같은 애는 여기서 사라지는 게 다들 편할 거야.  ",
"[박수현] [오후 1:25] ㅋㅋㅋ 맞아. 우리 방에서도 나가줘라. 그냥 보기 싫다. 너 같은 애 있으면 분위기 다 망치거든.  ",
"[김태훈] [오후 1:27] 그냥 눈치 없이 남아있지 말고 알아서 꺼져라. 니가 나가야 다들 속이 시원할 거다."
]

# 예시 문장 처리
predict_with_cyberbullying_check(sentences, tokenizer, model, device)
