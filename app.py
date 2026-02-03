import streamlit as st
import requests
from deep_translator import GoogleTranslator
import base64

# --- ページ設定 & 余白削除のCSS ---
st.set_page_config(page_title="AGENTIA by FEIDIAS", layout="centered")

st.markdown("""
    <style>
    /* 上部のヘッダーと余白を完全に削除 */
    header {visibility: hidden;}
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 600px;
    }
    .stApp { background-color: #f8f9fa; }
    

    }
    
    /* ロゴセンター配置 */
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }
    
    /* ボタンデザイン */
    .stButton>button {
        background-color: #004e92;
        color: white;
        border-radius: 4px;
        width: 100%;
        font-weight: bold;
        height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 設定エリア ---
VOICE_MODELS = {
    "Man": "ffe7a84cf0e243359b28e6c3686bc9af",
    "Woman": "735434a118054f65897638d4b7380dfc"
}
TTS_URL = "https://api.fish.audio/v1/tts"

# --- ロゴの表示 ---
try:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image("logo.png", width=600)
    st.markdown('</div>', unsafe_allow_html=True)
except:
    st.write("Logo (logo.png) not found.")

# --- メインコンテンツ ---
with st.container():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # 入力フォーム
    text_input = st.text_area("テキスト入力 (日本語)", placeholder="音声化したい内容をここに入力...", height=150)

    col1, col2 = st.columns(2)
    with col1:
        # スペイン語と韓国語を追加
        lang_option = st.selectbox(
            "出力言語", 
            ["日本語", "英語", "中国語", "スペイン語", "韓国語"]
        )
    with col2:
        voice_style = st.selectbox("音声モデル", list(VOICE_MODELS.keys()))

    lang_map = {
        "日本語": "ja", 
        "英語": "en", 
        "中国語": "zh-CN", 
        "スペイン語": "es", 
        "韓国語": "ko"
    }

    if st.button("音声を生成"):
        # SecretsからAPIキーを取得（表示はされない）
        try:
            api_key = st.secrets["FISH_AUDIO_API_KEY"]
        except:
            st.error("Secretsに 'FISH_AUDIO_API_KEY' が設定されていません。")
            st.stop()

        if not text_input:
            st.warning("テキストを入力してください。")
        else:
            with st.spinner('翻訳および音声生成中...'):
                try:
                    # 1. 翻訳
                    target_lang = lang_map[lang_option]
                    translated = GoogleTranslator(source='ja', target=target_lang).translate(text_input)
                    st.info(f"【翻訳結果】 {translated}")

                    # 2. Fish Audio API
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "text": translated,
                        "format": "wav",
                        "reference_id": VOICE_MODELS[voice_style],
                        "normalize": True
                    }

                    response = requests.post(TTS_URL, json=payload, headers=headers)

                    if response.status_code == 200:
                        audio_bytes = response.content
                        st.success("生成が完了しました。")
                        
                        st.audio(audio_bytes, format='audio/wav')

                        st.download_button(
                            label="ファイルをダウンロード (WAV)",
                            data=audio_bytes,
                            file_name=f"voice_{target_lang}.wav",
                            mime="audio/wav"
                        )
                    else:
                        st.error(f"APIエラー: {response.status_code}")
                
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("© 2026 Powered by FEIDIAS Inc.")
