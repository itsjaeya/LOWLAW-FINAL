import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image # 이미지

def load_image(img_file): # st 이미지 불러오기 함수
    img = Image.open(img_file)
    return img

logo_file = './image/lowlaw.png' # 로고 이미지 파일경로
logo_img = load_image(logo_file) # 로고 이미지 가져옴

# sidebar
with st.sidebar:
    st.image(logo_img, width = 300, output_format = "PNG")
    st.markdown('<p style="text-align: center; font-size: 25px;"><strong>임대차 분쟁 법률 조언 서비스</strong></p>', unsafe_allow_html=True)
    st.divider()
    # 메뉴바
    choice = option_menu("Menu",["LOWLAW ChatBot","LOWLAW Search"],
                         icons = ["bi bi-robot","bi bi-search"],
                         menu_icon = "bi bi-app-indicator", default_index = 0, #default_index = 처음에 보여줄 페이지 인덱스 번호
                         styles = {
                            "container": {"padding": "4!important", "background-color": "#fafafa"},
                            "icon": {"color": "black", "font-size": "25px"},
                            "nav-link": {"font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "#fafafa"},
                            "nav-link-selected": {"background-color": "#f0a543"},          
                         }#css설정
                         )
    


if choice == "LOWLAW ChatBot":
    exec(open('lowlaw-final/final-lowlaw-chatbot.py').read())

elif choice == "LOWLAW Search":
    exec(open('lowlaw-final/final-search.py').read())
