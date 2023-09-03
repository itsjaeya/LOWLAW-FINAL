import streamlit as st
from elastic_app_search import Client
import datetime
from PIL import Image
import re

# Create App Search client
client = Client(
    base_endpoint="lowlaw.ent.ap-northeast-2.aws.elastic-cloud.com/api/as/v1",
    api_key="private-egnzqo7tt7fd6fngz13mmox9",
    use_https=True
)
engine_name_1 = 'law-content'
engine_name_2 = 'prec-search'

# Function to align text to justify content
def align_text(text):
    return f"<div style='text-align: justify;'>{text}</div>"

def highlight_match(match):
        return f"<span style='color:red;'>{match}</span>"

# Function to highlight search terms in text
def highlight_search_terms(text, terms):
    highlighted_text = text
    for term in terms:
        highlighted_text = highlighted_text.replace(term, f"<span style='background-color: yellow;'>{term}</span>")
    return highlighted_text

def load_image(img_file): # st 이미지 불러오기 함수
    img = Image.open(img_file)
    return img

logo_file = '../image/lowlaw.png' # 로고 이미지 파일경로
logo_img = load_image(logo_file) # 로고 이미지 가져옴

# Streamlit 애플리케이션 시작
st.header("LOWLAW :mag_right: Search")

st.write("LOWLAW에 오신 것을 환영합니다👋 이곳에서 판례/법령이나 키워드로 검색을 도와드려요 🧑‍⚖️")

# sidebar
with st.sidebar:
    with st.expander("📌 LOWLAW Search 이용 가이드"):
        st.markdown("**📍 법령 검색 Tip**")
        st.markdown("하위항목까지 검색 시 **제+n조**로 띄어쓰기 없이 작성해 보세요!")
        st.caption("eg. 주택임대차보호법 제8조 제3항, 상가건물 임대차보호법 제10조의4 제1항")
        st.markdown("하위항목 중 '**목**'은 '제'가 붙지 않아요!")
        st.caption("eg. 상가건물 임대차보호법 제10조 제1항 제7호 가목")
        st.markdown("**📍 판례 검색 Tip**")
        st.markdown("특정 판례를 찾고자 하는 경우 **사건번호**로 검색해 보세요!")
        st.caption("eg. 사건번호 : 2015다14136 ")
        st.markdown("**📍 키워드 검색 Tip**")
        st.markdown("명사 조합으로 검색 해보세요!")
        st.caption("eg. 보증금 회수 / 계약갱신 요구 / 권리금 보호")


col1, col2 = st.columns([4, 1])

# 사용자로부터 검색어 입력 받기
with col1:
    search_query = st.text_input(label="", placeholder="❓ 검색어를 입력하세요.", label_visibility="collapsed")

# 검색 버튼 클릭 시 동작
with col2:
    if st.button("검색"):
        pass

if search_query:
    # 검색 옵션 설정 (score 점수 내림차순 정렬, 상위 3개 결과)
    search_options = {
        "sort": [{"_score": "desc"}],  # score 점수 내림차순 정렬
        "page": {"size": 3, "current": 1}  # 상위 3개 결과
    }

    # Search on Engine 1
    search_result_engine_1 = client.search(engine_name_1, search_query, search_options)

    # Search on Engine 2
    search_result_engine_2 = client.search(engine_name_2, search_query, search_options)

    # Display results for Engine 1
    st.subheader("법령 :book:")
    for result in search_result_engine_1['results']:
        score = result['_meta']['score']
        law_name = result.get('law', {}).get('raw', '')  # Get the law name from the result
        if law_name:
            highlighted_law_name = highlight_search_terms(law_name, search_query.split())
            st.write(f"**{highlighted_law_name}**", unsafe_allow_html=True)  # Apply highlight to law name
        
            # Combine jo, hang, ho, mok fields and display using write
            combined_fields = ' '.join([result[field]['raw'] for field in ['jo', 'hang', 'ho', 'mok'] if field in result])
            highlighted_combined_fields = highlight_search_terms(combined_fields, search_query.split())
            st.write(f"**{highlighted_combined_fields}**", unsafe_allow_html=True)  # Apply highlight to combined fields

            combined_content = ""
            content_fields = ['jo_content', 'hang_content', 'ho_content', 'mok_content']
            for content_field in content_fields:
                if content_field in result:
                    content = result[content_field]['raw']
                    # Use regular expression to find '제n조' pattern and its content
                    pattern = r'제(\d+)조\(([^)]+)\)'
                    replaced_content = re.sub(pattern, lambda match: f'제{match.group(1)}조({highlight_match(match.group(2))})', content)
                    combined_content += replaced_content + " "
         
            if combined_content:
                highlighted_combined_content = highlight_search_terms(combined_content, search_query.split())
                st.write(highlighted_combined_content, unsafe_allow_html=True)
            
            st.write("-" * 40)

    # Display results for Engine 2
    st.subheader("판례 :scales:")
    for result in search_result_engine_2['results']:
        score = result['_meta']['score']
        
        # 필요한 필드들을 함께 출력
        fields_to_print = ['사건명', '사건번호', '선고일자', '법원명', '사건종류명', '판시사항', '판결요지', '참조조문', '참조판례', '판례내용']
        for field in fields_to_print:
            if field in result:
                field_value = result[field]['raw']
                formatted_field_name = f"**{field.capitalize()}**"  # Adding bold formatting to field name
                if not field_value:  # If field value is empty
                    continue
                if field in ['사건명', '사건번호']:
                    highlighted_field_value = highlight_match(field_value)
                    st.write(f"{formatted_field_name}: {highlighted_field_value}", unsafe_allow_html=True)
                elif field == '선고일자':
                    # 선고일자를 datetime 형식으로 변환하여 원하는 포맷으로 출력
                    try:
                        date_value = datetime.datetime.strptime(str(int(field_value)), '%Y%m%d').strftime('%Y.%m.%d')
                        st.write(f"{formatted_field_name}: {date_value}")
                    except ValueError:
                        st.write(f"{formatted_field_name}: {field_value}")
                elif field in ['판시사항', '판결요지']:
                    # 판시사항과 판결요지가 있는 경우 출력
                    if field_value:
                        highlighted_value = highlight_search_terms(field_value, search_query.split())
                        highlighted_value = highlighted_value.replace('[', '\n\n[')  # 엔터 삽입 수정
                        st.write(f"{formatted_field_name}: {highlighted_value}", unsafe_allow_html=True)
                elif field == '판례내용':
                    # 판시사항과 판결요지 모두 없는 경우에만 판례내용 출력
                    if field_value:
                        highlighted_value = highlight_search_terms(field_value, search_query.split())
                        highlighted_value = highlighted_value.replace('【', '\n\n 【')  # 엔터 삽입 수정
                        expander = st.expander(formatted_field_name)  # Using formatted field name in expander title
                        expander.write(highlighted_value, unsafe_allow_html=True)
                elif field == '참조조문' or field == '참조판례':
                    # 참조조문과 참조판례를 붉은 글자로 강조하고 일반 텍스트 형태로 출력
                    if field_value:
                        search_terms = search_query.split()
                        for term in search_terms:
                            field_value = field_value.replace(term, f"<span style='color:red;'>{term}</span>")
                        field_value = field_value.replace('<span>', '')  # HTML 태그 제거
                        field_value = field_value.replace(' / ', ' <br><br> ')  # 줄 바꿈 추가
                        st.write(f"{formatted_field_name}:\n\n{field_value}", unsafe_allow_html=True)
                else:
                    st.write(f"{formatted_field_name}: {field_value}")
    
        st.write("-" * 40)