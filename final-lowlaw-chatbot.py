# final chatbot
import streamlit as st
from sentence_transformers import SentenceTransformer, util
from elasticsearch import Elasticsearch
from PIL import Image # 이미지
import re # 정규식
from streamlit_option_menu import option_menu # 메뉴바
from elastic_app_search import Client
import json
import datetime

# Elasticsearch 클라이언트 설정
es_cloud_id = "lowlaw:YXAtbm9ydGhlYXN0LTIuYXdzLmVsYXN0aWMtY2xvdWQuY29tOjQ0MyQ2YzNmMjA4MmNiMzk0M2YxYTBiZWI0ZDY2M2JmM2VlZCRjZTA2NGZhNjFiMmI0N2Y0ODgzMjY0Y2FlMzVlZDgxZQ=="
es_username = "elastic"
es_pw = "LWkW2eILoZYZylsDDThLaCKY"

es = Elasticsearch(cloud_id=es_cloud_id, basic_auth=(es_username, es_pw))

# Appsearch 클라이언트 설정
client = Client(
    base_endpoint="lowlaw.ent.ap-northeast-2.aws.elastic-cloud.com/api/as/v1",
    api_key="private-egnzqo7tt7fd6fngz13mmox9",
    use_https=True
)

# SentenceTransformer 모델 로드
@st.cache_data() # st 캐싱 (로컬캐시에 저장)
def cached_model():
    model = SentenceTransformer('jhgan/ko-sroberta-multitask')
    return model

def load_image(img_file): # st 이미지 불러오기 함수
    img = Image.open(img_file)
    return img

def law_search(data): # App Search에서 참조법령 찾기
    # 검색 옵션 설정 (score 점수 내림차순 정렬, 상위 1개 결과)
    search_options = {
        "sort": [{"_score": "desc"}],  # score 점수 내림차순 정렬
        "page": {"size": 1, "current": 1}  # 상위 1개 결과 (페이지 크기와 현재 페이지 번호를 지정)
    }

    # 결과를 문자열로 저장
    result_string = ""

    engine_name = 'law-content' # 법령검색 App Search
    
    # search
    search_query = data
    search_result = client.search(engine_name, search_query, search_options)

    # 필요한 필드들을 함께 저장
    for result in search_result['results']:
        score = result['_meta']['score']

        # 조항, 호, 목 필드 값이 있는 경우에만 'title' 변수 생성
        title_fields = [result[field]['raw'] for field in ['law', 'jo', 'hang', 'ho', 'mok'] if field in result and result[field]['raw']]
        if title_fields:
            title = " ".join(title_fields)
            
            content_fields = [result[field]['raw'] for field in ['jo_content', 'hang_content', 'ho_content', 'mok_content'] if field in result and result[field]['raw']]
            if content_fields:
                content = "\n\n".join(content_fields) + "\n"

        # 'title' 변수도 result_string에 추가
        result_string += f"{title}\n\n"
        result_string += f"\n\n {content}\n\n"
        result_string += "-" * 40 + "\n"  # 구분선 추가
            
    return result_string

def prec_search(data): # App Search 에서 참조판례 찾기
    engine_name = 'prec-search'
    # 검색 옵션 설정 (score 점수 내림차순 정렬, 상위 1개 결과)
    search_options = {
        "sort": [{"_score": "desc"}],  # score 점수 내림차순 정렬
        "page": {"size": 1, "current": 1}  # 상위 3개 결과
    }
    # search
    search_query = data
    search_result = client.search(engine_name, search_query, search_options)

    # 결과 문자열 초기화
    result_string = ""

    for result in search_result['results']:
        score = result['_meta']['score']

        # 필요한 필드들을 함께 출력
        fields_to_print = ['사건명', '사건번호', '선고일자', '법원명', '사건종류명', '판시사항', '판결요지', '참조조문', '참조판례', '판례내용']
        # 결과 문자열 생성
        for field in fields_to_print:
            if field in result:
                field_value = result[field]['raw']
                formatted_field_name = f"**{field}**"  # 필드명 굵은 글씨
                if not field_value:
                    continue
                if field == '선고일자':
                    try:
                        date_value = datetime.datetime.strptime(str(int(field_value)), '%Y%m%d').strftime('%Y.%m.%d')
                        result_string += f"{formatted_field_name}: {date_value}\n"
                    except ValueError:
                        result_string += f"{formatted_field_name}: {field_value}\n"
                elif field in ['법원명', '사건종류명']:
                    if field_value:
                        result_string += f"{formatted_field_name}: {field_value}\n"
                elif field == '판시사항':
                    if field_value:
                        field_value = field_value.replace('[', '\n[')  # '['가 나오면 '[' 앞에 줄바꿈 추가
                        result_string += "\n\n"+ "-" * 40 + "\n"
                        result_string += f"\n{formatted_field_name}:\n\n{field_value}\n\n"
                        result_string += "-" * 40 + "\n"
                elif field == '판결요지':
                    if field_value:
                        field_value = field_value.replace('[', '\n[')  # '['가 나오면 '[' 앞에 줄바꿈 추가
                        result_string += f"\n{formatted_field_name}:\n\n{field_value}\n\n"
                        result_string += "-" * 40 + "\n"
                elif field == '참조조문':
                    if field_value:
                        field_value = field_value.replace('/', '\n\n')  # '/'를 기준으로 줄바꿈 후 '/' 삭제
                        result_string += f"\n{formatted_field_name}:\n\n{field_value}\n\n"
                        result_string += "-" * 40 + "\n"
                elif field == '참조판례':
                    if field_value:
                        field_value = field_value.replace('/', '\n\n')  # '/'를 기준으로 줄바꿈 후 '/' 삭제
                        result_string += f"\n{formatted_field_name}:\n\n{field_value}\n\n"
                        result_string += "-" * 40 + "\n"
                elif field == '판례내용':
                    if field_value:
                        field_value = field_value.replace('【', '\n\n【')  # '【'가 나오면 '【' 앞에 줄바꿈 추가
                        result_string += f"{formatted_field_name}:\n\n{field_value}\n\n"
                        result_string += "-" * 40 + "\n"
                else:
                    if field == '사건명':
                        result_string += f"{formatted_field_name} {field_value}\n\n"  # 사건명 출력 시 콜론을 출력하지 않음
                        result_string += "-" * 40 + "\n"
                    elif field == '사건번호':
                        result_string += f"{formatted_field_name}: {field_value}\n\n"  # 사건번호 출력 시 콜론을 출력함
                        result_string += "-" * 40 + "\n"
                    else:
                        result_string += f"{formatted_field_name}: {field_value}\n"
                        result_string += "-" * 40 + "\n"

    return result_string

def button_law():
    result1 = law_search(law)
    st.session_state.messages.append({"role": "📖", "content": result1})

def button_prec() :
    result2 = prec_search(prec)
    st.session_state.messages.append({"role" : "⚖️", "content" : result2}) 

model = cached_model() # sentenceBERT 모델

logo_file = '../image/lowlaw.png' # 로고 이미지 파일경로
logo_img = load_image(logo_file) # 로고 이미지 가져옴

# 챗봇 sidebar
with st.sidebar:
    with st.expander("📌 LawBot 에게 더 정확한 답변 받는 Tip!"):
        st.markdown("📍'나' 혹은 '집주인'이라는 말보다 **임대인,임차인**으로 작성하여 물어보세요! ")
        st.caption("eg. 임차 주택의 변기를 수리하였습니다. 그 수리비를 임대인에게 청구할 수 있나요.")
        st.markdown("📍 개인적인 조건을 나열하는 것보다 객관적인 상황을 설명해 주세요!")
        st.caption("eg. 세입자가 월세를 미루고 있습니다. 월세를 계속 미룰 시 이자를 청구하겠다는 내용증명을 보내려고 합니다. 정말로 이자를 청구할 수 있을까요.")
        st.markdown("📍 어려운 법률용어도 질문가능!")
        st.caption("eg. 근저당권이란? 직권말소란? ")

# Streamlit 앱 시작
st.markdown('<p style="text-align: center; font-size: 40px;"><strong>🤖 LAWBOT ⚖️</strong></p>', unsafe_allow_html=True)

# ChatBot의 환영인사
with st.chat_message("assistant"):
    st.write("안녕하세요! LOWLAW에 오신 것을 환영합니다:wave:")
    st.write("내가 어떤 상황인지 파악하고 어떻게 해결할지 궁금하다면 LOWLAW와 대화하면서 해결해 보세요")

# 사용자에게 문장 입력 받기
user_input = st.chat_input(placeholder = "어떤 상황인지 설명해 주세요!")

# 문장벡터 계산
embeddings = model.encode([user_input])[0] if user_input is not None else None

# Elasticsearch에서 embedding 필드 값 검색
query = {
    "query": {
        "match_all": {}
    },
    "_source": ["question","answer","law", "prec", "embedding"]
}

response = es.search(index="legal_qa_final", body=query, size=3000) # size = 6478

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

butt = False

if user_input : # 사용자가 user_input를 입력하였다면
    # 가장 높은 코사인 유사도 값 초기화
    max_cosine_similarity = -1
    best_answer = ""

    # 사용자의 user_input chat message에 띄워주기
    st.chat_message("user").markdown(user_input)

    # 사용자의 user_input을 chat history에 append
    st.session_state.messages.append({"role" : "user", "content" : user_input}) 

    # 각 문서와의 코사인 유사도 비교
    for hit in response["hits"]["hits"]:
        doc_embedding = hit["_source"]["embedding"]
    
        # Elasticsearch에서 가져온 'embedding' 값을 문자열에서 리스트로 변환
        doc_embedding = [float(value) for value in doc_embedding.strip("[]").split(", ")]
    
        cosine_similarity = util.pytorch_cos_sim(embeddings, [doc_embedding]).item()
    
        if cosine_similarity > max_cosine_similarity:
            max_cosine_similarity = cosine_similarity
            best_answer = hit["_source"]["answer"]
            related_law = hit["_source"].get("law", None) # 필드에 데이터가 존재하면 law 값을 가져오고 존재하지 않으면 None 반환
            related_prec = hit["_source"].get("prec", None) # 필드에 데이터가 존재하면 prec 값을 가져오고 존재하지 않으면 None 반환

    if max_cosine_similarity > 0.7 : # max_cosine_similarity 값이 0.7 이상이면 해당 답변 출력 

        with st.chat_message("assistant"):# assistant의 답변 chat message에 띄워주기 
            
            best_answer = re.sub(r'\((.*?)\)', lambda x: x.group(0).replace('.', ' '), best_answer)# 괄호 안의 내용을 제외하고 .을 기준으로 두번 줄바꿈 (가독성)
            best_answer = best_answer.replace('.', '.  \n\n') # .을 줄바꿈 2번으로 대체
            st.markdown(best_answer) # 가장 유사한 답변
            
            st.session_state.messages.append({"role" : "assistant", "content" : best_answer}) # assistant의 가상 유사한 답변 chat history에 append 하기

            if related_law: # 만약 참조법령이 있다면 
                related_law_list = related_law.split(",")  # ','로 구분하여 리스트로 변환
                st.markdown(f"**:red[참조법령]** :book:")
                for law in related_law_list: # 참조법령 리스트 안에 있는 내용 각각 버튼으로 출력
                    st.button(law,on_click=lambda:button_law()) # 버튼누르면 App Search에 참조법령 query로 보내고 결과값 return

            if related_prec: # 만약 참조판례가 있다면 related_prec출력
                related_prec_list = related_prec.split(",")  # ','로 구분하여 리스트로 변환
                st.markdown(f"**:red[참조판례]** :scales:")
                for prec in related_prec_list: # 참조판례 리스트 안에 있는 내용 각각 버튼으로 출력  
                    st.button(prec,on_click = lambda:button_prec()) # 버튼누르면 App Search에 참조판례 query로 보내고 결과값 return

    else: # assistant의 답변 오류메세지 chat message에 띄워주기 (0.7 이하일 때)  
        with st.chat_message("assistant"):
            st.markdown("질문에 대한 답변을 찾을 수 없어요:cry: 상황에 대해서 정확히 입력해주세요!") 
        st.session_state.messages.append({"role" : "assistant", "content" : "질문에 대한 답변을 찾을 수 없어요:cry: 상황에 대해서 정확히 입력해주세요!" }) # assistant의 chat history에 append 하기