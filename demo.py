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

if "step" not in st.session_state:
    st.session_state.step = 0
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame()
if "quiz1_indexes" not in st.session_state:
    st.session_state.quiz1_indexes = []
if "quiz2_indexes" not in st.session_state:
    st.session_state.quiz2_indexes = []
if "answers1" not in st.session_state:
    st.session_state.answers1 = {}
if "answers2" not in st.session_state:
    st.session_state.answers2 = {}

# ====== Bước 0: Chọn Sheet ======

if st.session_state.step == 0:
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
        st.session_state.step = 2
        st.rerun()

# ====== Bước 2: Làm kiểm tra 1 ======

elif st.session_state.step == 2:
    st.subheader("📚 KIỂM TRA 1: Trả lời các câu hỏi")
    df = st.session_state.data
    answers = st.session_state.answers1
    for i, idx in enumerate(st.session_state.quiz1_indexes, 1):
        row = df.iloc[idx]
        kind = random.choice(["Vocabulary", "Phonetic", "Example"])
        prompt = row[kind]
        key = f"q1_{i}"
        answers[key] = st.text_input(f"{i}. {kind}: {prompt}", value=answers.get(key, ""))

    if st.button("Kiểm tra kết quả"):
        st.session_state.answers1 = answers
        st.session_state.step = 3
        st.rerun()

# ====== Bước 3: Kết quả kiểm tra 1 ======

elif st.session_state.step == 3:
    st.subheader("✅ KẾT QUẢ KIỂM TRA 1")
    df = st.session_state.data
    correct = 0
    wrong_list = []
    for i, idx in enumerate(st.session_state.quiz1_indexes, 1):
        row = df.iloc[idx]
        key = f"q1_{i}"
        user_ans = normalize(st.session_state.answers1.get(key, ""))
        if user_ans == row['Meaning_norm']:
            correct += 1
        else:
            wrong_list.append((i, row['Meaning'], st.session_state.answers1.get(key, "")))

    st.write(f"🎯 Bạn đã trả lời đúng {correct}/25 câu.")
    st.success("🎉 Bạn đã vượt qua bài kiểm tra!") if correct >= 20 else st.warning("❌ Bạn chưa vượt qua bài kiểm tra.")

    if wrong_list:
        st.write("### ❌ Những câu trả lời sai:")
        for i, correct_ans, user_ans in wrong_list:
            st.write(f"- Câu {i}: Đáp án đúng: **{correct_ans}** | Bạn trả lời: `{user_ans}`")

    if st.button("Tiếp tục kiểm tra 2"):
        st.session_state.step = 4
        st.rerun()

# ====== Bước 4: Tạo kiểm tra 2 ======

elif st.session_state.step == 4:
    st.subheader("📘 KIỂM TRA 2: Cho nghĩa → Chọn từ")
    df = st.session_state.data
    used = set(st.session_state.quiz1_indexes)
    indexes = get_random_entries(df, exclude_idxs=used, count=25)
    if len(indexes) < 25:
        st.error("Không thể chọn đủ 25 câu hỏi hợp lệ cho kiểm tra 2.")
    else:
        st.session_state.quiz2_indexes = indexes
        st.session_state.answers2 = {}
        st.session_state.step = 5
        st.rerun()

# ====== Bước 5: Làm kiểm tra 2 ======

elif st.session_state.step == 5:
    st.subheader("📘 KIỂM TRA 2: Trả lời các câu hỏi")
    df = st.session_state.data
    answers = st.session_state.answers2
    for i, idx in enumerate(st.session_state.quiz2_indexes, 1):
        row = df.iloc[idx]
        key = f"q2_{i}"
        answers[key] = st.text_input(f"{i}. Nghĩa: {row['Meaning']}", value=answers.get(key, ""))

    if st.button("Kiểm tra kết quả kiểm tra 2"):
        st.session_state.answers2 = answers
        st.session_state.step = 6
        st.rerun()

# ====== Bước 6: Kết quả kiểm tra 2 ======

elif st.session_state.step == 6:
    st.subheader("✅ KẾT QUẢ KIỂM TRA 2")
    df = st.session_state.data
    correct = 0
    wrong_list = []
    for i, idx in enumerate(st.session_state.quiz2_indexes, 1):
        row = df.iloc[idx]
        key = f"q2_{i}"
        user_ans = normalize(st.session_state.answers2.get(key, ""))
        if user_ans == row['Vocabulary_norm']:
            correct += 1
        else:
            wrong_list.append((i, row['Vocabulary'], st.session_state.answers2.get(key, "")))

    st.write(f"🎯 Bạn đã trả lời đúng {correct}/25 câu.")
    st.success("🎉 Bạn đã vượt qua bài kiểm tra!") if correct >= 20 else st.warning("❌ Bạn chưa vượt qua bài kiểm tra.")

    if wrong_list:
        st.write("### ❌ Những câu trả lời sai:")
        for i, correct_ans, user_ans in wrong_list:
            st.write(f"- Câu {i}: Đáp án đúng: **{correct_ans}** | Bạn trả lời: `{user_ans}`")

    if st.button("Làm lại từ đầu"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
