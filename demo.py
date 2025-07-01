import streamlit as st
import pandas as pd
import random
import re

# ====== Cấu hình ======
FILE_NAME = "Everyday language.xlsx"

# ====== Hàm xử lý ======

def normalize(text):
    if isinstance(text, str):
        return re.sub(r'\s+', ' ', text.strip().lower())
    return ""

def highlight_vocab(example, vocab):
    if not isinstance(example, str) or not isinstance(vocab, str):
        return example
    pattern = re.escape(vocab.strip())
    return re.sub(f"(?i)({pattern})", r"**\1**", example, flags=re.IGNORECASE)

def load_data(sheet_choice):
    dfs = []
    for i in range(1, sheet_choice + 1):
        try:
            df = pd.read_excel(FILE_NAME, sheet_name=f"Sheet{i}")
            df.columns = ['Vocabulary', 'Phonetic', 'Meaning', 'Example']
            df.dropna(inplace=True)
            for col in ['Vocabulary', 'Phonetic', 'Meaning', 'Example']:
                df[col + "_norm"] = df[col].apply(normalize)
            dfs.append(df)
        except Exception as e:
            st.error(f"Không thể đọc Sheet{i}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def get_random_entries(df, exclude_idxs, count):
    selected = []
    used_texts = set()
    tries = 0
    while len(selected) < count and tries < 1000:
        idx = random.randint(0, len(df) - 1)
        if idx in exclude_idxs:
            tries += 1
            continue
        row = df.iloc[idx]
        key_texts = {row['Vocabulary_norm'], row['Phonetic_norm'], row['Example_norm']}
        if used_texts & key_texts:
            tries += 1
            continue
        selected.append(idx)
        used_texts.update(key_texts)
        tries = 0
    return selected

# ====== Giao diện ======

st.set_page_config(page_title="Ứng dụng học từ vựng", layout="centered")
st.title("📝 CHƯƠNG TRÌNH HỌC TỪ VỰNG")

# ====== Khởi tạo trạng thái ======
for key in ['step', 'data', 'quiz1_indexes', 'quiz2_indexes', 'answers1', 'answers2']:
    if key not in st.session_state:
        st.session_state[key] = None

# ====== Bước 0: Chọn Sheet ======
if st.session_state.step is None:
    sheet_num = st.number_input("Chọn số sheet muốn học (1–10):", min_value=1, max_value=10, step=1)
    if st.button("Bắt đầu"):
        df = load_data(sheet_num)
        if len(df) < 50:
            st.error("Không đủ dữ liệu để tạo 2 bài kiểm tra.")
        else:
            st.session_state.data = df
            st.session_state.step = 1
            st.rerun()

# ====== Bước 1: Tạo kiểm tra 1 ======
elif st.session_state.step == 1:
    st.subheader("📚 KIỂM TRA 1: Cho từ → Chọn nghĩa")
    df = st.session_state.data
    indexes = get_random_entries(df, exclude_idxs=set(), count=25)
    if len(indexes) < 25:
        st.error("Không thể chọn đủ 25 câu hỏi hợp lệ. Dữ liệu có thể bị trùng lặp quá nhiều.")
    else:
        st.session_state.quiz1_indexes = indexes
        st.session_state.answers1 = {}
        st.session_state.prompt1_types = [
            random.choice(["Vocabulary", "Phonetic", "Example"]) for _ in indexes
        ]
        st.session_state.ste
