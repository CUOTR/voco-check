import streamlit as st
import pandas as pd
import random
import re
import datetime

# ====== Cấu hình ======
FILE_NAME = "Everyday language.xlsx"

# ====== Hàm xử lý ======
def normalize(text):
    if isinstance(text, str):
        return re.sub(r'\s+', ' ', text.strip().lower())
    return ""

def load_data(sheet_indexes):
    dfs = []
    for i in sheet_indexes:
        try:
            df = pd.read_excel(FILE_NAME, sheet_name=f"Sheet{i}")
            if df.shape[1] < 4:
                st.error(f"Sheet{i} không đủ cột cần thiết.")
                continue
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

def log_user_action(action, data=""):
    with open("log.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {action} | {data}\n")

# ====== Giao diện ======
st.set_page_config(page_title="Ứng dụng học từ vựng", layout="centered")
st.title("📝 CHƯƠNG TRÌNH HỌC Từa VỰNG")

# ====== Khởi tạo trạng thái ======
for key in ['step', 'data', 'data_previous', 'sheet_chosen',
            'quiz0_indexes', 'quiz0_types', 'answers0',
            'quiz1_indexes', 'answers1', 'prompt1_types',
            'quiz2_indexes', 'answers2']:
    if key not in st.session_state:
        st.session_state[key] = None

# ====== Bước 0: Chọn Sheet ======
if st.session_state.step is None:
    sheet_num = st.number_input("Chọn số buổi học muốn kiểm tra:", min_value=1, max_value=20, step=1)
    if st.button("Bắt đầu"):
        log_user_action("Bắt đầu học", f"Sheet {sheet_num}")
        st.session_state.sheet_chosen = sheet_num
        st.session_state.data = load_data([sheet_num])

        if sheet_num > 1:
            st.session_state.data_previous = load_data(range(1, sheet_num))
            st.session_state.step = 0
        else:
            st.session_state.data_previous = pd.DataFrame()
            st.session_state.step = 1

        if len(st.session_state.data) < 70:
            st.error("Không đủ dữ liệu để tạo 2 bài kiểm tra.")
        else:
            st.rerun()

# === Bước 1: Quiz0 - bài tổng hợp ===
if st.session_state.step == 0:
    st.subheader("🧠 KIỂM TRA TỔNG HỢP")
    df = st.session_state.data_previous
    total_needed = 20
    indexes = get_random_entries(df, exclude_idxs=set(), count=total_needed)
    st.session_state.quiz0_indexes = indexes
    st.session_state.quiz0_types = ['prompt'] * 10 + ['reverse'] * 10
    st.session_state.answers0 = {}
    st.session_state.step = 'quiz0'
    st.rerun()

elif st.session_state.step == 'quiz0':
    st.subheader("🧠 KIỂM TRA TỔNG HỢP")
    df = st.session_state.data_previous
    for i, idx in enumerate(st.session_state.quiz0_indexes):
        row = df.iloc[idx]
        kind = st.session_state.quiz0_types[i]
        key = f"q0_{i+1}"
        if kind == 'prompt':
            field = random.choice(['Vocabulary', 'Phonetic', 'Example'])
            st.markdown(f"**{i+1}. {field}**: {row[field]}")
            st.session_state.answers0[key] = st.text_input("Nhập nghĩa:", key=key)
        else:
            st.markdown(f"**{i+1}. Nghĩa**: {row['Meaning']}")
            st.session_state.answers0[key] = st.text_input("Nhập từ vựng:", key=key)
    if st.button("Xem kết quả"):
        st.session_state.step = 'quiz0_result'
        st.rerun()

elif st.session_state.step == 'quiz0_result':
    st.subheader("✅ KẾT QUẢ TỔNG HỢP")
    df = st.session_state.data_previous
    correct = 0
    for i, idx in enumerate(st.session_state.quiz0_indexes):
        row = df.iloc[idx]
        kind = st.session_state.quiz0_types[i]
        key = f"q0_{i+1}"
        user_ans = normalize(st.session_state.answers0.get(key, ""))
        answer = row['Meaning_norm'] if kind == 'prompt' else row['Vocabulary_norm']
        if user_ans == answer:
            correct += 1
    st.write(f"Trả lời đúng {correct}/20")
    if st.button("Tiếp tục Quiz 1"):
        st.session_state.step = 1
        st.rerun()

# === Quiz1 ===
elif st.session_state.step == 1:
    st.subheader("📚 KIỂM TRA 1: Cho từ → Nghĩa")
    df = st.session_state.data
    indexes = get_random_entries(df, exclude_idxs=set(), count=35)
    st.session_state.quiz1_indexes = indexes
    st.session_state.prompt1_types = [random.choice(["Vocabulary", "Phonetic", "Example"]) for _ in indexes]
    st.session_state.answers1 = {}
    st.session_state.step = 2
    st.rerun()

elif st.session_state.step == 2:
    st.subheader("📚 Trả lời Quiz 1")
    df = st.session_state.data
    for i, idx in enumerate(st.session_state.quiz1_indexes):
        row = df.iloc[idx]
        field = st.session_state.prompt1_types[i]
        st.markdown(f"**{i+1}. {field}**: {row[field]}")
        st.session_state.answers1[f"q1_{i+1}"] = st.text_input("Nghĩa:", key=f"q1_{i+1}")
    if st.button("Kết quả Quiz 1"):
        st.session_state.step = 3
        st.rerun()

elif st.session_state.step == 3:
    st.subheader("✅ KẾT QUẢ Quiz 1")
    df = st.session_state.data
    correct = 0
    for i, idx in enumerate(st.session_state.quiz1_indexes):
        row = df.iloc[idx]
        ans = normalize(st.session_state.answers1.get(f"q1_{i+1}", ""))
        if ans == row['Meaning_norm']:
            correct += 1
    st.write(f"Trả lời đúng {correct}/35")
    if st.button("Tiếp Quiz 2"):
        st.session_state.step = 4
        st.rerun()

# === Quiz2 ===
elif st.session_state.step == 4:
    st.subheader("📘 KIỂM TRA 2: Cho nghĩa → Từ")
    df = st.session_state.data
    used = set(st.session_state.quiz1_indexes)
    indexes = get_random_entries(df, exclude_idxs=used, count=35)
    st.session_state.quiz2_indexes = indexes
    st.session_state.answers2 = {}
    st.session_state.step = 5
    st.rerun()

elif st.session_state.step == 5:
    st.subheader("📘 Trả lời Quiz 2")
    df = st.session_state.data
    for i, idx in enumerate(st.session_state.quiz2_indexes):
        row = df.iloc[idx]
        st.markdown(f"**{i+1}. Nghĩa**: {row['Meaning']}")
        st.session_state.answers2[f"q2_{i+1}"] = st.text_input("Từ:", key=f"q2_{i+1}")
    if st.button("Kết quả Quiz 2"):
        st.session_state.step = 6
        st.rerun()

elif st.session_state.step == 6:
    st.subheader("✅ KẾT QUẢ Quiz 2")
    df = st.session_state.data
    correct = 0
    for i, idx in enumerate(st.session_state.quiz2_indexes):
        row = df.iloc[idx]
        ans = normalize(st.session_state.answers2.get(f"q2_{i+1}", ""))
        if ans == row['Vocabulary_norm']:
            correct += 1
    st.write(f"Trả lời đúng {correct}/35")
    if st.button("🔄 Bắt đầu lại"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
