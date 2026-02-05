import streamlit as st
import requests
from deep_translator import GoogleTranslator
import whisper
import numpy as np
import librosa
import io

# ページ設定とデザイン（前回のCSSを継承）
st.set_page_config(page_title="AGENTIA for ニッポン放送β", layout="centered")

st.markdown("""
    <style>
    header {visibility: hidden;}
    .main .block-container { padding-top: 1rem; max-width: 600px; }
    .stApp { background-color: #f8f9fa; }
    .main-card { background-color: #ffffff; padding: 2.5rem; border-radius: 8px; border: 1px solid #e1e4e8; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 2rem; }
    /* チェック結果のバッジ用 */
    .quality-badge { padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 0.8em; }
    .pass { background-color: #d4edda; color: #155724; }
    .fail { background-color: #f8d7da; color: #721c24; }
    </style>
    """, unsafe_allow_html=True)

# --- 内部解析関数 ---
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

def analyze_audio(audio_bytes, target_text):
    # 1. テキスト照合 (Whisper)
    model = load_whisper()
    # バイナリを一時ファイル的に読み込み
    with open("temp.wav", "wb") as f:
        f.write(audio_bytes)
    
    result = model.transcribe("temp.wav")
    transcribed_text = result["text"].strip()
    
    # 簡易的な一致率計算 (0.0 - 1.0)
    import difflib
    match_score = difflib.SequenceMatcher(None, target_text.lower(), transcribed_text.lower()).ratio()
    
    # 2. 音質解析 (librosa)
    y, sr = librosa.load("temp.wav")
    rms = np.sqrt(np.mean(y**2)) # 音圧の平均
    
    return {
        "transcribed": transcribed_text,
        "accuracy": match_score * 100,
        "rms": rms
    }

# --- メインロジック ---
VOICE_MODELS = {
    "男性": "ffe7a84cf0e243359b28e6c3686bc9af",
    "女性": "735434a118054f65897638d4b7380dfc"
}

try:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image("logo.png", width=250)
    st.markdown('</div>', unsafe_allow_html=True)
except:
    st.title("音声生成システム")

with st.container():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    text_input = st.text_area("テキスト入力 (日本語)", placeholder="内容を入力...", height=120)
    
    col1, col2 = st.columns(2)
    with col1:
        lang_option = st.selectbox("出力言語", ["日本語", "英語", "中国語", "スペイン語", "韓国語"])
    with col2:
        voice_style = st.selectbox("音声モデル", list(VOICE_MODELS.keys()))

    if st.button("音声を生成・検品"):
        api_key = st.secrets.get("FISH_AUDIO_API_KEY")
        if not api_key:
            st.error("API Key not found in Secrets.")
        elif text_input:
            with st.spinner('生成およびAI検品中...'):
                # 翻訳
                lang_map = {"日本語": "ja", "英語": "en", "中国語": "zh-CN", "スペイン語": "es", "韓国語": "ko"}
                translated = GoogleTranslator(source='ja', target=lang_map[lang_option]).translate(text_input)
                
                # Fish Audio生成
                res = requests.post(
                    "https://api.fish.audio/v1/tts",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"text": translated, "format": "wav", "reference_id": VOICE_MODELS[voice_style]}
                )
                
                if res.status_code == 200:
                    audio_data = res.content
                    # --- AI検品実行 ---
                    analysis = analyze_audio(audio_data, translated)
                    
                    # 結果表示
                    st.audio(audio_data)
                    
                    # 検品レポートの表示
                    st.markdown("### AI検品レポート")
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        acc = analysis['accuracy']
                        status = "PASS" if acc > 80 else "REVIEW REQUIRED"
                        color = "pass" if acc > 80 else "fail"
                        st.markdown(f"**読み上げ精度:** <span class='quality-badge {color}'>{acc:.1f}%</span>", unsafe_allow_html=True)
                        st.caption(f"認識内容: {analysis['transcribed']}")
                        
                    with col_b:
                        is_audible = analysis['rms'] > 0.01
                        v_status = "OK" if is_audible else "LOW VOLUME"
                        v_color = "pass" if is_audible else "fail"
                        st.markdown(f"**音圧レベル:** <span class='quality-badge {v_color}'>{v_status}</span>", unsafe_allow_html=True)

                    st.download_button("WAVをダウンロード", audio_data, f"output.wav", "audio/wav", use_container_width=True)
                else:
                    st.error("生成エラーが発生しました。")
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("© 2026 Powered by FEIDIAS Inc.")