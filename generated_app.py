import streamlit as st
import openai
import os
import json

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    decoder = json.JSONDecoder()
    try:
        data, end = decoder.raw_decode(text)
        return data
    except json.JSONDecodeError:
        st.error(f"JSONファイル {filename} の解析に失敗しました。正しい形式か確認してください。")
        return {}

astrology_data = load_json('Astrology.json')
mbti_data = load_json('MBTI.json')

ZODIAC_JP_MAP = {
    "Aries": "牡羊座", "Taurus": "牡牛座", "Gemini": "双子座",
    "Cancer": "蟹座", "Leo": "獅子座", "Virgo": "乙女座",
    "Libra": "天秤座", "Scorpio": "蠍座", "Sagittarius": "射手座",
    "Capricorn": "山羊座", "Aquarius": "水瓶座", "Pisces": "魚座"
}
JP_TO_ENG = {v: k for k, v in ZODIAC_JP_MAP.items()}
japanese_zodiac_names = list(JP_TO_ENG.keys())

FIXED_MBTI_TYPES = [
    "ISTJ", "ISFJ", "INFJ", "INTJ",
    "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP",
    "ESTJ", "ESFJ", "ENFJ", "ENTJ"
]

def get_astro_traits(sign, data):
    info = data.get(sign, {})
    if isinstance(info, str):
        return info
    elif isinstance(info, dict):
        return info.get('personality', '') or info.get('traits', '') or info.get('description', '') or str(info)
    else:
        return str(info)

def get_mbti_traits(mbti_type, data):
    info = data.get(mbti_type, {})
    if isinstance(info, str):
        return info
    elif isinstance(info, dict):
        return info.get('personality', '') or info.get('traits', '') or info.get('description', '') or str(info)
    else:
        return str(info)

st.set_page_config(page_title="5年後の物語生成")
st.title("5年後の二人の物語ジェネレーター")

if "generate" not in st.session_state:
    st.session_state.generate = False
if "story" not in st.session_state:
    st.session_state.story = ""
if "story_data" not in st.session_state:
    st.session_state.story_data = {}

col1, col2 = st.columns(2)
with col1:
    st.subheader("人物A")
    gender_a = st.selectbox("性別", ["男性", "女性", "その他"], key="gender_a")
    zodiac_a_jp = st.selectbox("星座", japanese_zodiac_names, key="zodiac_a_jp")
    mbti_a = st.selectbox("MBTI", FIXED_MBTI_TYPES, key="mbti_a")
with col2:
    st.subheader("人物B")
    gender_b = st.selectbox("性別", ["男性", "女性", "その他"], key="gender_b")
    zodiac_b_jp = st.selectbox("星座", japanese_zodiac_names, key="zodiac_b_jp")
    mbti_b = st.selectbox("MBTI", FIXED_MBTI_TYPES, key="mbti_b")

relationship = st.selectbox("現在の関係性", ["他人", "学生時代の知り合い", "飲み友達", "遊び友達", "会社の同僚", "恋人", "夫婦"], key="relationship")

if st.button("物語を生成"):
    st.session_state.generate = True
    zodiac_a_eng = JP_TO_ENG[zodiac_a_jp]
    zodiac_b_eng = JP_TO_ENG[zodiac_b_jp]
    st.session_state.story_data = {
        "gender_a": gender_a,
        "zodiac_a": zodiac_a_eng,
        "mbti_a": mbti_a,
        "gender_b": gender_b,
        "zodiac_b": zodiac_b_eng,
        "mbti_b": mbti_b,
        "relationship": relationship
    }

if st.session_state.generate:
    data = st.session_state.story_data
    astro_traits_a = get_astro_traits(data["zodiac_a"], astrology_data)
    mbti_traits_a = get_mbti_traits(data["mbti_a"], mbti_data)
    person_a_desc = f"性別: {data['gender_a']}\n星座の性格: {astro_traits_a}\nMBTIの性格: {mbti_traits_a}"

    astro_traits_b = get_astro_traits(data["zodiac_b"], astrology_data)
    mbti_traits_b = get_mbti_traits(data["mbti_b"], mbti_data)
    person_b_desc = f"性別: {data['gender_b']}\n星座の性格: {astro_traits_b}\nMBTIの性格: {mbti_traits_b}"

    relationship_text = data["relationship"]

    prompt = f"""
あなたは小説家です。以下の2人のプロフィールと現在の関係性をもとに、5年後の関係を描いた短編物語（日本語）を生成してください。
物語は温かみがあり、文学的なスタイルで、800文字程度で書いてください。

【人物A】
{person_a_desc}

【人物B】
{person_b_desc}

【現在の関係性】
{relationship_text}

5年後の物語:
"""
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            st.error("環境変数 DEEPSEEK_API_KEY が設定されていません。")
            st.stop()
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        with st.spinner("物語を生成中..."):
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "あなたは優秀な作家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            story = response.choices[0].message.content
            st.session_state.story = story
    except Exception as e:
        st.error(f"生成エラー: {e}")
        st.session_state.story = ""

    if st.session_state.story:
        st.markdown("### 5年後の物語")
        st.markdown(st.session_state.story)
