import streamlit as st
import requests
from deep_translator import GoogleTranslator
import whisper
import numpy as np
import librosa
import os

# --- ページ設定 & デザイン修正 ---
st.set_page_config(page_title="AGENTIA for ニッポン放送β", layout="centered")

st.markdown("""
    <style>
    /* ヘッダーと余白の削除 */
    header {visibility: hidden;}
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
    .main .block-container { padding-top: 0rem; max-width: 700px; }
    
    /* ロゴのセンター配置とサイズ調整 */
    .logo-box {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        padding: 20px 0;
    }
    .logo-box img {
        max-width: 400px; /* ロゴの最大幅を大きく設定 */
        width: 60%;       /* 画面幅に合わせて調整 */
    }


    
    /* 検品バッジ */
    .quality-badge { padding: 4px 12px; border-radius: 4px; font-weight: bold; }
    .pass { background-color: #d4edda; color: #155724; }
    .fail { background-color: #f8d7da; color: #721c24; }
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
        # 1. テキスト照合
        model = load_whisper()
        result = model.transcribe(temp_file)
        transcribed_text = result["text"].strip()
        
        import difflib
        match_score = difflib.SequenceMatcher(None, target_text.lower(), transcribed_text.lower()).ratio()
        
        # 2. 音質解析
        y, sr = librosa.load(temp_file)
        rms = np.sqrt(np.mean(y**2))
        
        return {"transcribed": transcribed_text, "accuracy": match_score * 100, "rms": rms}
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

# --- メインレイアウト ---

# ロゴ部分
if os.path.exists("logo.png"):
    st.markdown(f'''
        <div class="logo-box">
            <img src="data:image/png;base64,{st.image("logo.png")}" />
        </div>
    ''', unsafe_allow_html=True)

else:
    st.title("音声生成システム")

with st.container():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    text_input = st.text_area("テキスト入力 (日本語)", placeholder="内容を入力してください...", height=120)
    
    col1, col2 = st.columns(2)
    with col1:
        lang_option = st.selectbox("出力言語", ["日本語", "英語", "中国語", "スペイン語", "韓国語"])
    with col2:
        voice_style = st.selectbox("音声モデル", ["男性", "女性"])

    VOICE_MODELS = {
        "男性": "ffe7a84cf0e243359b28e6c3686bc9af",
        "女性": "735434a118054f65897638d4b7380dfc"
    }

    if st.button("音声を生成・検品"):
        api_key = st.secrets.get("FISH_AUDIO_API_KEY")
        if not api_key:
            st.error("Secretsに 'FISH_AUDIO_API_KEY' を設定してください。")
        elif text_input:
            with st.spinner('AIが生成と検品を行っています...'):
                try:
                    # 翻訳
                    lang_map = {"日本語": "ja", "英語": "en", "中国語": "zh-CN", "スペイン語": "es", "韓国語": "ko"}
                    translated = GoogleTranslator(source='ja', target=lang_map[lang_option]).translate(text_input)
                    
                    # 生成
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
                        c1, c2 = st.columns(2)
                        with c1:
                            acc = analysis['accuracy']
                            color = "pass" if acc > 80 else "fail"
                            st.markdown(f"読み上げ精度: <span class='quality-badge {color}'>{acc:.1f}%</span>", unsafe_allow_html=True)
                            st.caption(f"認識: {analysis['transcribed']}")
                        with c2:
                            is_ok = analysis['rms'] > 0.01
                            color = "pass" if is_ok else "fail"
                            st.markdown(f"音圧レベル: <span class='quality-badge {color}'>{'OK' if is_ok else 'LOW'}</span>", unsafe_allow_html=True)

                        st.download_button("WAVをダウンロード", audio_data, "output.wav", "audio/wav")
                    else:
                        st.error("Fish Audio APIでエラーが発生しました。")
                except Exception as e:
                    st.error(f"エラー: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
    
st.caption("© 2026 Powered by FEIDIAS Inc.")
