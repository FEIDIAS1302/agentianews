import streamlit as st
import requests
from deep_translator import GoogleTranslator

# ページ設定
st.set_page_config(page_title="AGENTIA NEWS Speaker", layout="centered")

# --- 設定エリア ---
# ここにご自身の Reference ID を入力してください
VOICE_MODELS = {
    "男性": "b5dbca68e48f4f488799fcb988dfc005",
    "女性": "735434a118054f65897638d4b7380dfc"
}
TTS_URL = "https://api.fish.audio/v1/tts"

# --- UIデザイン (Chatwork風) ---
st.markdown("""
    <style>
    body { color: #333; }
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 8px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    h1 { color: #004e92; font-size: 22px !important; margin-bottom: 20px; font-weight: 600; }
    .stButton>button {
        background-color: #004e92;
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #003366; border: none; color: white; }
    label { font-size: 14px !important; color: #666; }
    </style>
    """, unsafe_allow_html=True)

# コンテンツ
with st.container():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.title("音声生成システム")

    # APIキー入力（Secrets運用でない場合）
    api_key = st.text_input("Fish Audio API Key", type="password", help="APIキーを入力してください")

    # 入力フォーム
    text_input = st.text_area("テキスト入力 (日本語)", placeholder="音声化したい内容をここに入力...", height=120)

    col1, col2 = st.columns(2)
    with col1:
        lang_option = st.selectbox("出力言語", ["日本語", "英語", "中国語"])
    with col2:
        voice_style = st.selectbox("音声モデル", list(VOICE_MODELS.keys()))

    lang_map = {"日本語": "ja", "英語": "en", "中国語": "zh-CN"}

    if st.button("音声を生成"):
        if not api_key or not text_input:
            st.error("APIキーとテキストは必須です。")
        else:
            with st.spinner('処理中...'):
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
                        "reference_id": VOICE_MODELS[voice_style], # 選択されたIDを適用
                        "normalize": True
                    }

                    response = requests.post(TTS_URL, json=payload, headers=headers)

                    if response.status_code == 200:
                        audio_bytes = response.content
                        st.success("音声生成が完了しました。")
                        
                        # 再生プレーヤー
                        st.audio(audio_bytes, format='audio/wav')

                        # ダウンロードボタン
                        st.download_button(
                            label="ファイルをダウンロード (WAV)",
                            data=audio_bytes,
                            file_name=f"voice_{target_lang}.wav",
                            mime="audio/wav",
                            use_container_width=True
                        )
                    else:
                        st.error(f"APIエラーが発生しました (Status: {response.status_code})")
                
                except Exception as e:
                    st.error(f"エラー: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("Developed by Genius Engineer | Fish Audio API Integration")