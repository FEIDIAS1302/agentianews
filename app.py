import streamlit as st
import requests
from deep_translator import GoogleTranslator
import whisper
import numpy as np
import os
import difflib

# --- ページ設定 & デザイン修正 ---
st.set_page_config(page_title="AGENTIA for ニッポン放送β", layout="centered")

st.markdown("""
    <style>
    /* ヘッダーと余白の削除 */
    header {visibility: hidden;}
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
    .main .block-container { padding-top: 0rem; max-width: 700px; }
    
    /* カードデザイン */
    .main-card { 
        background-color: #ffffff; 
        padding: 2.5rem; 
        border-radius: 12px; 
        border: 1px solid #e1e4e8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    
    /* 検品バッジ */
    .quality-badge { padding: 4px 12px; border-radius: 4px; font-weight: bold; }
    .pass { background-color: #d4edda; color: #155724; }
    .fail { background-color: #f8d7da; color: #721c24; }
    
    /* ボタンのホバーエフェクト */
    .stButton>button { 
        background-color: #004e92; 
        color: white; 
        font-weight: bold; 
        width: 100%;
        border-radius: 6px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #003366;
        border-color: #003366;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 内部解析関数 ---
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

def analyze_audio(audio_bytes, target_text):
    temp_file = "temp_audio.wav"
    with open(temp_file, "wb") as f:
        f.write(audio_bytes)
    
    try:
        model = load_whisper()
        result = model.transcribe(temp_file)
        transcribed_text = result["text"].strip()
        
        match_score = difflib.SequenceMatcher(None, target_text.lower(), transcribed_text.lower()).ratio()
        return {"transcribed": transcribed_text, "accuracy": match_score * 100}
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

# --- メインレイアウト ---

# ロゴ部分
if os.path.exists("logo.png"):
    col_l, col_m, col_r = st.columns([1, 4, 1])
    with col_m:
        st.image("logo.png", use_container_width=True)
else:
    st.title("音声生成システム")

with st.container():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    text_input = st.text_area("テキスト入力 (日本語)", placeholder="音声化したい内容を入力してください...", height=120)
    
    col1, col2 = st.columns(2)
    with col1:
        lang_option = st.selectbox("出力言語", ["日本語", "英語", "中国語", "スペイン語", "韓国語"])
    with col2:
        # モデル選択肢を3つに増強
        voice_style = st.selectbox("音声モデル", ["男性", "女性", "吉田アナ(TEST)"])

    # --- 音声モデルIDの設定 ---
    VOICE_MODELS = {
        "男性": "b8580c330cd74c2bbb7785815f1756d3",
        "女性": "735434a118054f65897638d4b7380dfc",
        "吉田アナ(TEST)": "ffe7a84cf0e243359b28e6c3686bc9af" 
    }

    if st.button("音声を生成・検品"):
        api_key = st.secrets.get("FISH_AUDIO_API_KEY")
        if not api_key:
            st.error("Secretsに 'FISH_AUDIO_API_KEY' を設定してください。")
        elif text_input:
            with st.spinner('AIが生成と検品を行っています...'):
                try:
                    lang_map = {"日本語": "ja", "英語": "en", "中国語": "zh-CN", "スペイン語": "es", "韓国語": "ko"}
                    translated = GoogleTranslator(source='ja', target=lang_map[lang_option]).translate(text_input)
                    
                    res = requests.post(
                        "https://api.fish.audio/v1/tts",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={"text": translated, "format": "wav", "reference_id": VOICE_MODELS[voice_style]}
                    )
                    
                    if res.status_code == 200:
                        audio_data = res.content
                        analysis = analyze_audio(audio_data, translated)
                        
                        st.audio(audio_data)
                        
                        st.markdown("### AI検品レポート")
                        acc = analysis['accuracy']
                        color = "pass" if acc > 80 else "fail"
                        st.markdown(f"読み上げ精度: <span class='quality-badge {color}'>{acc:.1f}%</span>", unsafe_allow_html=True)
                        st.caption(f"認識内容: {analysis['transcribed']}")

                        st.markdown("---")
                        st.download_button("WAVをダウンロード", audio_data, f"voice_{lang_option}.wav", "audio/wav", use_container_width=True)
                    else:
                        st.error(f"APIエラーが発生しました。Status: {res.status_code}")
                except Exception as e:
                    st.error(f"システムエラー: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
    
st.caption("© 2026 Powered by FEIDIAS Inc.")