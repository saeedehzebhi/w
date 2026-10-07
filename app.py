import streamlit as st
import pandas as pd
import base64
import os
import re
import numpy as np
from pathlib import Path
from PyPDF2 import PdfReader
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# =========================================================
# تنظیمات اصلی صفحه
# =========================================================

st.set_page_config(
    page_title="اداره کل ارتباطات و فناوری اطلاعات استان یزد",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# تنظیمات هوش مصنوعی
# =========================================================

AI_API_KEY = "1xai-f2wfQtVkSEYgCpFjvTOnr27MTQa51eC3IAcWgQkkl40"
#"1xai-rCHeJx2q4xOwh3fSnLp12eCRzmwRqBe6Ipvo25JQM4o"
AI_BASE_URL = "https://1xai.ir/v1"
AI_MODEL = "gpt-4o-mini"
AI_MODEL_REWRITE = "gpt-4o-mini"

# AI_API_KEY = "aEY9FpS_kDtR_LMOh2qq3iAO5vFnEW3McW1G13BPn2g"
# AI_BASE_URL = "https://ai.parspack.com/v1/"
# AI_MODEL = "openai/gpt-4o-mini-2024-07-18"
# AI_MODEL_REWRITE = "openai/gpt-4o-mini-2024-07-18"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_FOLDER = os.path.join(BASE_DIR, "PDFs")

# =========================================================
# تابع تبدیل تصویر به Base64
# =========================================================

import os
from pathlib import Path
import base64

BASE_DIR = Path(__file__).resolve().parent

def get_base64_image(image_path):
    # نام فایل را از مسیر جدا کن (چون ممکن است مسیر ویندوزی باشد)
    filename = os.path.basename(image_path.replace("\\", "/"))
    
    possible_paths = [
        BASE_DIR / filename,
        BASE_DIR / "assets" / filename,
        BASE_DIR / "background.jpg",
        BASE_DIR / "background.png",
        Path.cwd() / filename,
        Path.cwd() / "assets" / filename,
        Path.cwd() / "background.jpg",
        Path.cwd() / "background.png",
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_file():
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    
    # اگر هیچ‌کدام پیدا نشد، لاگ بده
    print(f"⚠️ تصویر پیدا نشد. مسیرهای بررسی‌شده: {possible_paths}")
    return ""
    for path in possible_paths:
        if path.exists() and path.is_file():
            try:
                with open(path, "rb") as f:
                    data = f.read()
                return base64.b64encode(data).decode()
            except Exception:
                return None
    return None

# =========================================================
# مدیریت صفحات
# =========================================================

if "page" not in st.session_state:
    st.session_state["page"] = "home"

# =========================================================
# CSS پایه
# =========================================================

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    .stApp {
        background: linear-gradient(135deg, #e3f2fd, #f5f7fa);
    }

    .page-title {
        background: white;
        padding: 16px;
        border-radius: 15px;
        text-align: center;
        color: #00695c;
        font-size: 26px;
        font-weight: bold;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.12);
        direction: rtl;
    }

    .stButton > button {
        background: rgba(255, 255, 255, 0.95);
        color: #00695c;
        border: 2px solid #00695c;
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: bold;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        background: #00695c;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0,105,92,0.4);
    }

    .clickable-card {
        display: block;
        background: rgba(255, 255, 255, 0.92);
        border-radius: 18px;
        padding: 25px 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.5);
        text-align: center;
        text-decoration: none !important;
        color: inherit !important;
        transition: all 0.3s ease;
        cursor: pointer;
        height: 100%;
        direction: rtl;
    }
    .clickable-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.28);
        background: rgba(255, 255, 255, 0.98);
    }
    .clickable-card .icon { font-size: 45px; margin-bottom: 10px; }
    .clickable-card .title { font-size: 20px; font-weight: bold; margin-bottom: 8px; }
    .clickable-card .desc { font-size: 13px; color: #555; }

    .bottom-left-footer {
        position: fixed;
        bottom: 15px;
        left: 20px;
        color: #ffffff;
        font-size: 14px;
        font-weight: bold;
        text-shadow: 0 2px 6px rgba(0,0,0,0.8),
                     0 0 10px rgba(0,0,0,0.6);
        z-index: 9999;
    }

    div[data-testid="stInfo"] {
        background: rgba(255, 255, 255, 0.95) !important;
    }

    .chat-user {
        background: #d1ecf1;
        padding: 12px 16px;
        border-radius: 12px;
        margin: 8px 0;
        text-align: right;
        border-right: 4px solid #0c5460;
        direction: rtl;
    }
    .chat-ai {
        background: #e8f5e9;
        padding: 12px 16px;
        border-radius: 12px;
        margin: 8px 0;
        text-align: right;
        border-right: 4px solid #2e7d32;
        direction: rtl;
    }
    .chat-label {
        font-size: 12px;
        color: #666;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# فایل‌های Excel
# =========================================================

VILLAGE_FILE = "1405.6.22-12_55_39.xlsx"
USO_FILE = "ورژن2-ابلاغ های انجام شده از ابتدای سال 1401.xlsx"

# ✅ فقط شیت ابلاغی-هدف باقی مانده است
SHEETS = [
    "ابلاغی-هدف"
]

SHEETS_HEADER_ROW_1 = ["ابلاغی-هدف"]

# =========================================================
# تابع یکسان سازی متن فارسی
# =========================================================

def normalize_text(value):
    if pd.isna(value):
        return ""
    value = str(value)
    value = value.replace("ي", "ی").replace("ى", "ی").replace("ك", "ک")
    value = value.replace("\u200c", " ").replace("\u200f", "").replace("\u200e", "")
    value = " ".join(value.split())
    return value.strip()

# =========================================================
# توابع هوش مصنوعی و PDF
# =========================================================

@st.cache_resource
def load_pdf_documents():
    documents = []
    filenames = []
    if not PDF_FOLDER.exists():
        return [], []
    for filename in os.listdir(PDF_FOLDER):
        if filename.lower().endswith(".pdf"):
            filepath = PDF_FOLDER / filename
            try:
                reader = PdfReader(str(filepath))
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                text = re.sub(r'\s+', ' ', text).strip()
                if text:
                    documents.append(text)
                    filenames.append(filename)
            except Exception as e:
                print(f"خطا در خواندن فایل {filename}: {e}")
    return documents, filenames

def chunk_text(text, chunk_size=600, overlap=150):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

@st.cache_resource
def build_search_index():
    documents, filenames = load_pdf_documents()
    if not documents:
        return None, None, None, None
    all_chunks = []
    chunk_to_file = {}
    for i, doc in enumerate(documents):
        chunks = chunk_text(doc)
        for chunk in chunks:
            all_chunks.append(chunk)
            chunk_to_file[chunk] = filenames[i]
    if not all_chunks:
        return None, None, None, None
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_chunks)
    return vectorizer, tfidf_matrix, all_chunks, chunk_to_file

def rewrite_query(query):
    prompt = f"""سوال زیر را به ۸ تا ۱۲ کلیدواژه فارسی مرتبط با اسناد اداری، مخابراتی و روستایی تبدیل کن.
فقط کلیدواژه‌ها را با کاما جدا کن. هیچ توضیح اضافه‌ای نده.
نام روستاها، شهرستان‌ها و اعداد را حتماً حفظ کن.

سوال: {query}

کلیدواژه‌ها:"""
    try:
        client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
        r = client.chat.completions.create(
            model=AI_MODEL_REWRITE,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=150
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return ""

def get_candidate_chunks(query, all_chunks, chunk_to_file):
    query_words = set(re.findall(r'\w{3,}', query))
    if not query_words:
        return all_chunks
    candidates = []
    for chunk in all_chunks:
        if any(w in chunk for w in query_words):
            candidates.append(chunk)
    if len(candidates) < 20:
        return all_chunks
    return candidates

def get_ai_response(query, context_chunks, chat_history=None):
    trimmed_chunks = [c[:800] for c in context_chunks[:6]]
    context_text = "\n\n---\n\n".join(trimmed_chunks)
    system_prompt = """شما یک دستیار مدیریتی برای مدیرکل ارتباطات و فناوری اطلاعات استان یزد هستید.
وظیفه شما: پاسخ دقیق و مستند به سوال مدیر، فقط بر اساس متن‌های ارائه‌شده.

قوانین سخت‌گیرانه:
1. فقط از اطلاعات متن‌های ارائه‌شده استفاده کن. هیچ دانش خارجی اضافه نکن.
2. اگر بخشی از پاسخ در متن‌ها نیست، صریح بنویس: «در اسناد موجود اطلاعاتی درباره این بخش یافت نشد.»
3. پاسخ را در قالب یک پاراگراف مدیریتی روان بنویس.
4. اگر متن‌ها متناقض بودند، هر دو نظر را با ذکر منبع بیاور.
5. عدد، تاریخ، نام روستا و نام سازمان را عیناً همان‌طور که در متن است بنویس."""
    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    user_prompt = f"""بر اساس متن‌های مرتبط زیر به سوال مدیر پاسخ دهید.

متن‌های مرتبط:
{context_text}

سوال مدیر:
{query}

پاسخ خلاصه مدیریتی:"""
    messages.append({"role": "user", "content": user_prompt})
    try:
        client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ خطا در برقراری ارتباط: {str(e)}"

# =========================================================
# دکمه بازگشت
# =========================================================

def back_button():
    if st.button("⬅️ بازگشت به صفحه اصلی"):
        st.session_state["page"] = "home"
        st.rerun()

# =========================================================
# صفحه اصلی
# =========================================================

def home_page():
    bg_base64 = get_base64_image("background.png")
    if bg_base64:
        st.markdown(f"""
        <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{bg_base64}") !important;
                background-size: cover !important;
                background-position: center !important;
                background-attachment: fixed !important;
                background-repeat: no-repeat !important;
            }}
        </style>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:280px;'></div>", unsafe_allow_html=True)

    left, center, right = st.columns([1, 5, 1])
    with center:
        col1, col2, col3 = st.columns(3, gap="medium")

        with col1:
            st.markdown("""
            <a class="clickable-card" href="?page=village" target="_self" style="border-top: 6px solid #1b8a5a;">
                <div class="icon">🏘️</div>
                <div class="title" style="color: #1b8a5a;">روستاها و آبادی‌ها</div>
                <div class="desc">مشاهده اطلاعات کامل روستاها و آبادی‌های استان یزد</div>
            </a>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <a class="clickable-card" href="?page=uso" target="_self" style="border-top: 6px solid #6a1b9a;">
                <div class="icon">📡</div>
                <div class="title" style="color: #6a1b9a;">پروژه‌های توسعه ارتباطات روستایی (USO)</div>
                <div class="desc">ابلاغی از ابتدای سال 1401</div>
            </a>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <a class="clickable-card" href="?page=chat" target="_self" style="border-top: 6px solid #c62828;">
                <div class="icon">💬</div>
                <div class="title" style="color: #c62828;">پرسش و پاسخ مدیر</div>
                <div class="desc">پرسش سوال از اسناد و مدارک</div>
            </a>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="bottom-left-footer">
        اداره کل ارتباطات و فناوری اطلاعات یزد
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# مدیریت پارامتر URL
# =========================================================

query_params = st.query_params
if "page" in query_params:
    requested_page = query_params["page"]
    if requested_page in ["village", "uso", "chat"]:
        st.session_state["page"] = requested_page
        st.query_params.clear()
        st.rerun()

# =========================================================
# پیدا کردن ستون
# =========================================================

def find_column(df, names):
    for column in df.columns:
        column_normal = normalize_text(column)
        for name in names:
            if column_normal == normalize_text(name):
                return column
    return None

def find_column_flexible(df, keywords):
    for column in df.columns:
        column_normal = normalize_text(column)
        for keyword in keywords:
            keyword_normal = normalize_text(keyword)
            if keyword_normal in column_normal:
                return column
    return None

# =========================================================
# نمایش یک ردیف
# =========================================================

def show_row(row):
    items = []
    for column in row.index:
        value = row[column]
        if pd.isna(value):
            value = "اطلاعات ثبت نشده"
        items.append((str(column), str(value)))
    for i in range(0, len(items), 2):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{items[i][0]}**")
            st.info(items[i][1])
        if i + 1 < len(items):
            with col2:
                st.markdown(f"**{items[i + 1][0]}**")
                st.info(items[i + 1][1])

def show_multiple_rows(result):
    st.success(f"✅ تعداد {len(result)} رکورد پیدا شد.")
    for number, (_, row) in enumerate(result.iterrows(), start=1):
        st.markdown(f"### 📋 رکورد {number}")
        show_row(row)
        st.divider()

# =========================================================
# صفحه اطلاعات روستا (روستا → شهرستان → دهستان)
# =========================================================

def village_page():
    back_button()
    st.markdown("""
    <div class="page-title">
        🏘️ اطلاعات روستا
    </div>
    """, unsafe_allow_html=True)

    @st.cache_data
    def load_village_data():
        return pd.read_excel(VILLAGE_FILE)

    df = load_village_data()
    df.columns = [normalize_text(str(col)) for col in df.columns]

    village_col = find_column(df, ["روستا/آبادی", "روستا", "آبادی"])
    if village_col is None:
        village_col = find_column_flexible(df, ["روستا", "آبادی"])

    city_col = find_column(df, ["شهرستان"])
    if city_col is None:
        city_col = find_column_flexible(df, ["شهرستان"])

    dehestan_col = find_column(df, ["دهستان"])
    if dehestan_col is None:
        dehestan_col = find_column_flexible(df, ["دهستان"])

    if village_col is None:
        st.error("❌ ستون «روستا/آبادی» در فایل اکسل پیدا نشد.")
        st.info(f"📋 ستون‌های موجود: {list(df.columns)}")
        return
    if city_col is None:
        st.error("❌ ستون «شهرستان» در فایل اکسل پیدا نشد.")
        st.info(f"📋 ستون‌های موجود: {list(df.columns)}")
        return
    if dehestan_col is None:
        st.error("❌ ستون «دهستان» در فایل اکسل پیدا نشد.")
        st.info(f"📋 ستون‌های موجود: {list(df.columns)}")
        return

    df["روستا_جستجو"] = df[village_col].apply(normalize_text)
    df["شهرستان_جستجو"] = df[city_col].apply(normalize_text)
    df["دهستان_جستجو"] = df[dehestan_col].apply(normalize_text)

    st.info("ابتدا روستا / آبادی، سپس شهرستان و در نهایت دهستان را انتخاب کنید.")

    # گام ۱: انتخاب روستا / آبادی
    villages = sorted([x for x in df["روستا_جستجو"].unique() if x != ""])
    selected_village = st.selectbox(
        "🏘️ روستا / آبادی را انتخاب کنید:",
        ["انتخاب کنید..."] + villages
    )

    if selected_village != "انتخاب کنید...":
        village_data = df[df["روستا_جستجو"] == selected_village]

        # گام ۲: انتخاب شهرستان
        cities = sorted([x for x in village_data["شهرستان_جستجو"].unique() if x != ""])

        if len(cities) == 1:
            selected_city = cities[0]
            st.info(f"🏙️ شهرستان: **{selected_city}**")
        else:
            selected_city = st.selectbox(
                "🏙️ شهرستان را انتخاب کنید:",
                ["انتخاب کنید..."] + cities
            )

        if selected_city != "انتخاب کنید...":
            city_data = village_data[village_data["شهرستان_جستجو"] == selected_city]

            # گام ۳: انتخاب دهستان
            dehestans = sorted([x for x in city_data["دهستان_جستجو"].unique() if x != ""])

            if len(dehestans) == 1:
                selected_dehestan = dehestans[0]
                st.info(f"🌳 دهستان: **{selected_dehestan}**")
            else:
                selected_dehestan = st.selectbox(
                    "🌳 دهستان را انتخاب کنید:",
                    ["انتخاب کنید..."] + dehestans
                )

            if selected_dehestan != "انتخاب کنید...":
                result = city_data[city_data["دهستان_جستجو"] == selected_dehestan]

                if not result.empty:
                    st.success("✅ اطلاعات روستا پیدا شد.")
                    row = result.iloc[0]
                    st.markdown("### 📋 اطلاعات کامل روستا")
                    items = []
                    for column in df.columns:
                        if column in ["روستا_جستجو", "شهرستان_جستجو", "دهستان_جستجو"]:
                            continue
                        value = row[column]
                        if pd.isna(value):
                            value = "اطلاعات ثبت نشده"
                        items.append((str(column), str(value)))
                    for i in range(0, len(items), 2):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**{items[i][0]}**")
                            st.info(items[i][1])
                        if i + 1 < len(items):
                            with col2:
                                st.markdown(f"**{items[i + 1][0]}**")
                                st.info(items[i + 1][1])
                else:
                    st.error("❌ اطلاعاتی برای این روستا پیدا نشد.")

# =========================================================
# صفحه پروژه های USO (فقط شیت ابلاغی-هدف، جستجو: شهرستان و آبادی)
# =========================================================

def uso_page():
    back_button()
    st.markdown("""
    <div class="page-title">
        📡 پیشرفت پروژه‌های (USO)
        <br>
        <span style="font-size:18px;">
            ابلاغی از ابتدای سال 1401
        </span>
    </div>
    """, unsafe_allow_html=True)

    @st.cache_data
    def load_uso_data():
        data = {}
        for sheet in SHEETS:
            # ✅ هدر در ردیف دوم برای شیت ابلاغی-هدف
            header = 1 if sheet in SHEETS_HEADER_ROW_1 else 0
            try:
                df = pd.read_excel(USO_FILE, sheet_name=sheet, header=header)
                df = df.dropna(axis=1, how="all")
                df = df.dropna(axis=0, how="all")
                df.columns = [normalize_text(str(col)) for col in df.columns]
                data[sheet] = df
            except Exception as e:
                st.error(f"خطا در خواندن شیت «{sheet}»: {e}")
        return data

    data = load_uso_data()

    for sheet_name in SHEETS:
        df = data[sheet_name]
        with st.expander(f"📁 {sheet_name}", expanded=True):
            st.markdown(f"## 📁 {sheet_name}")

            # ✅ پیدا کردن ستون‌های موردنیاز
            city_col = find_column(df, ["شهرستان", "District"])
            if city_col is None:
                city_col = find_column_flexible(df, ["شهرستان"])

            village_col = find_column(df, ["آبادی", "روستا/آبادی", "روستا", "Village"])
            if village_col is None:
                village_col = find_column_flexible(df, ["آبادی", "روستا"])

            if city_col is None:
                st.error(f"❌ ستون «شهرستان» در شیت «{sheet_name}» پیدا نشد.")
                st.info(f"📋 ستون‌های موجود: {list(df.columns)}")
                continue

            if village_col is None:
                st.error(f"❌ ستون «آبادی» یا «روستا» در شیت «{sheet_name}» پیدا نشد.")
                st.info(f"📋 ستون‌های موجود: {list(df.columns)}")
                continue

            # =================================================
            # گام ۱: انتخاب شهرستان
            # =================================================
            cities = sorted([
                x for x in
                df[city_col].dropna().apply(normalize_text).unique()
                if x != ""
            ])

            selected_city = st.selectbox(
                "🏙️ شهرستان را انتخاب کنید:",
                ["انتخاب کنید..."] + cities,
                key=f"{sheet_name}_city"
            )

            if selected_city != "انتخاب کنید...":
                city_data = df[
                    df[city_col].apply(normalize_text) == selected_city
                ]

                # =================================================
                # گام ۲: انتخاب آبادی
                # =================================================
                villages = sorted([
                    x for x in
                    city_data[village_col].dropna().apply(normalize_text).unique()
                    if x != ""
                ])

                selected_village = st.selectbox(
                    "🏘️ آبادی را انتخاب کنید:",
                    ["انتخاب کنید..."] + villages,
                    key=f"{sheet_name}_village"
                )

                if selected_village != "انتخاب کنید...":
                    result = city_data[
                        city_data[village_col].apply(normalize_text) == selected_village
                    ]
                    if result.empty:
                        st.error("❌ اطلاعاتی برای این آبادی پیدا نشد.")
                    else:
                        st.success(f"✅ اطلاعات «{selected_village}» پیدا شد.")
                        show_multiple_rows(result)

# =========================================================
# صفحه پرسش و پاسخ مدیر
# =========================================================

def chat_page():
    back_button()
    st.markdown("""
    <div class="page-title">
        💬 پرسش و پاسخ مدیر
        <br>
        <span style="font-size:16px;">
            پرسش سوال از اسناد و مدارک
        </span>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("⏳ در حال بارگذاری اسناد PDF..."):
        vectorizer, tfidf_matrix, all_chunks, chunk_to_file = build_search_index()

    if vectorizer is None:
        st.error(f"❌ هیچ فایل PDF در پوشه «{PDF_FOLDER}» پیدا نشد.")
        st.info(f"📁 لطفاً فایل‌های PDF خود را در پوشه زیر قرار دهید:\n\n`{PDF_FOLDER}`")
        return

    st.success(f"✅ {len(set(chunk_to_file.values()))} فایل PDF بارگذاری شد ({len(all_chunks)} قطعه متن).")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    col_a, col_b = st.columns([4, 1])
    with col_b:
        if st.button("🗑️ پاک کردن چت"):
            st.session_state.chat_messages = []
            st.rerun()

    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-user">
                <div class="chat-label">👤 مدیر:</div>
                {msg["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-ai">
                <div class="chat-label">🤖 دستیار هوشمند:</div>
                {msg["content"]}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    with st.form(key="chat_form", clear_on_submit=True):
        query = st.text_input("✍️ سوال خود را وارد کنید:", placeholder="آخرین وضعیت احداث سایت تلفن همراه در تنگل چیست؟")
        submit_button = st.form_submit_button("📤 ارسال سوال", use_container_width=True)

    if submit_button and query.strip():
        query = query.strip()
        st.session_state.chat_messages.append({
            "role": "user",
            "content": query
        })

        with st.spinner("🔎 در حال تحلیل سوال..."):
            expanded_keywords = rewrite_query(query)

        search_query = query + " " + expanded_keywords if expanded_keywords else query
        candidate_chunks = get_candidate_chunks(search_query, all_chunks, chunk_to_file)

        if len(candidate_chunks) < len(all_chunks):
            candidate_matrix = vectorizer.transform(candidate_chunks)
            query_vector = vectorizer.transform([search_query])
            similarities = cosine_similarity(query_vector, candidate_matrix).flatten()
            top_indices = similarities.argsort()[-6:][::-1]
            top_chunks = [candidate_chunks[i] for i in top_indices if similarities[i] > 0.03]
        else:
            query_vector = vectorizer.transform([search_query])
            similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
            top_indices = similarities.argsort()[-6:][::-1]
            top_chunks = [all_chunks[i] for i in top_indices if similarities[i] > 0.03]

        if not top_chunks:
            answer = "❌ متاسفانه پاسخ مرتبطی در اسناد PDF پیدا نشد. لطفاً سوال را با جزئیات بیشتر بپرسید."
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": answer
            })
            st.rerun()
        else:
            related_files = list(set(chunk_to_file.get(c, "") for c in top_chunks))
            related_files = [f for f in related_files if f]

            with st.spinner("🤖 در حال دریافت پاسخ..."):
                ai_answer = get_ai_response(
                    query,
                    top_chunks,
                    chat_history=st.session_state.chat_messages[:-1]
                )

            files_info = " | ".join([f"📁 {f}" for f in related_files])
            full_answer = f"{ai_answer}\n\n---\n**اسناد مرتبط:** {files_info}"

            if expanded_keywords:
                full_answer += f"\n\n<sub>🔍 کلیدواژه‌های جستجو: {expanded_keywords}</sub>"

            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": full_answer
            })
            st.rerun()

# =========================================================
# اجرای صفحه انتخاب‌شده
# =========================================================

if st.session_state["page"] == "home":
    home_page()
elif st.session_state["page"] == "village":
    village_page()
elif st.session_state["page"] == "uso":
    uso_page()
elif st.session_state["page"] == "chat":
    chat_page()
