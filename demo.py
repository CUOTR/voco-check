import streamlit as st
import pandas as pd
import random
import re

# ✨ Tiêu đề app
st.set_page_config(page_title="Kiểm tra Từ vựng", layout="centered")
st.title("\U0001F4D6 Chương trình Học từ vựng")

# ✨ Hỗ trợ hàm chuẩn hóa chuỗi
def normalize(text):
    if isinstance(text, str):
        return re.sub(r'\s+', ' ', text.strip().lower())
    return ''

# ✨ Load dữ liệu từ sheet
def load_data(sheet_choice):
    sheets = [f"Sheet{i}" for i in range(1, sheet_choice + 1)]
    df_list = []
    for sheet in sheets:
        try:
            df = pd.read_excel("Everyday language.xlsx", sheet_name=sheet)
            df.columns = ['Vocabulary', 'Phonetic', 'Meaning', 'Example']
            df = df.dropna()
            df_list.append(df)
        except Exception as e:
            st.error(f"\u274c Không đọc được {sheet}: {e}")
    if not df_list:
        return pd.DataFrame()
    full_df = pd.concat(df_list, ignore_index=True)
    for col in ['Vocabulary', 'Phonetic', 'Meaning', 'Example']:
        full_df[col + '_norm'] = full_df[col].apply(normalize)
    return full_df

# ✨ Lọc ngẫu nhiên không trùng key_text

def get_random_entries(df, exclude_indexes, count):
    attempts = 0
    selected = []
    used_texts = set()
    
    while len(selected) < count and attempts < 1000:
        idx = random.randint(0, len(df) - 1)
        if idx in exclude_indexes:
            attempts += 1
            continue

        row = df.iloc[idx]
        key_texts = [row['Vocabulary_norm'], row['Phonetic_norm'], row['Example_norm']]

        if any(text in used_texts for text in key_texts):
            attempts += 1
            continue

        selected.append(idx)
        used_texts.update(key_texts)
        attempts = 0

    if len(selected) < count:
        raise ValueError("\u274c Không thể chọn đủ 25 câu hỏi hợp lệ. Dữ liệu quá ít hoặc bị trùng nhiều.")

    return selected

# ✨ Khởi tạo session_state
if "step" not in st.session_state:
    st.session_state.step = "choose"
    st.session_state.sheet_num = 1
    st.session_state.df = pd.DataFrame()
    st.session_state.quiz1_indexes = []
    st.session_state.quiz2_indexes = []
    st.session_state.quiz1_answers = {}
    st.session_state.quiz2_answers = {}

# ✨ Giao diện chọn sheet
if st.session_state.step == "choose":
    sheet_num = st.number_input("Chọn số sheet muốn học (1–10):", 1, 10, 1)
    if st.button("Bắt đầu kiểm tra"):
        df = load_data(sheet_num)
        if len(df) < 50:
            st.error("\u274c Cần tối thiểu 50 từ vựng để tạo 2 bài kiểm tra.")
        else:
            st.session_state.sheet_num = sheet_num
            st.session_state.df = df
            st.session_state.quiz1_indexes = get_random_entries(df, set(), 25)
            st.session_state.quiz2_indexes = get_random_entries(df, set(st.session_state.quiz1_indexes), 25)
            st.session_state.step = "quiz1"

# ✨ Giao diện bài kiểm tra 1
elif st.session_state.step == "quiz1":
    st.header("Bài Kiểm tra 1: Tìm nghĩa của từ")
    for i, idx in enumerate(st.session_state.quiz1_indexes):
        row = st.session_state.df.iloc[idx]
        prompt_type = random.choice(['Vocabulary', 'Phonetic', 'Example'])
        prompt = row[prompt_type]
        key = f"quiz1_q{i}"
        st.session_state.quiz1_answers[idx] = st.text_input(f"{i+1}. {prompt_type}: {prompt}", key=key)
    if st.button("Kiểm tra kết quả 1"):
        st.session_state.step = "result1"

# ✨ Kết quả quiz 1
elif st.session_state.step == "result1":
    st.subheader("Kết quả bài Kiểm tra 1")
    correct = 0
    for i, idx in enumerate(st.session_state.quiz1_indexes):
        row = st.session_state.df.iloc[idx]
        user = normalize(st.session_state.quiz1_answers[idx])
        ans = row['Meaning_norm']
        if user == ans:
            correct += 1
        else:
            st.markdown(f"**Câu {i+1} sai:** Nhập: `{user}` | Đúng: `{row['Meaning']}`")
    st.success(f"Số đúng: {correct}/25")
    if correct >= 20:
        st.balloons()
        st.success("Đã vượt qua bài Kiểm tra 1!")
    else:
        st.warning("Chưa đạt. Hãy thử lại sau.")
    if st.button("Tiếp tục Kiểm tra 2"):
        st.session_state.step = "quiz2"

# ✨ Bài kiểm tra 2
elif st.session_state.step == "quiz2":
    st.header("Bài Kiểm tra 2: Tìm từ theo nghĩa")
    for i, idx in enumerate(st.session_state.quiz2_indexes):
        row = st.session_state.df.iloc[idx]
        key = f"quiz2_q{i}"
        st.session_state.quiz2_answers[idx] = st.text_input(f"{i+1}. Nghĩa: {row['Meaning']}", key=key)
    if st.button("Kiểm tra kết quả 2"):
        st.session_state.step = "result2"

# ✨ Kết quả quiz 2
elif st.session_state.step == "result2":
    st.subheader("Kết quả bài Kiểm tra 2")
    correct = 0
    for i, idx in enumerate(st.session_state.quiz2_indexes):
        row = st.session_state.df.iloc[idx]
        user = normalize(st.session_state.quiz2_answers[idx])
        ans = row['Vocabulary_norm']
        if user == ans:
            correct += 1
        else:
            st.markdown(f"**Câu {i+1} sai:** Nhập: `{user}` | Đúng: `{row['Vocabulary']}`")
    st.success(f"Số đúng: {correct}/25")
    if correct >= 20:
        st.balloons()
        st.success("Đã vượt qua bài Kiểm tra 2!")
    else:
        st.warning("Chưa đạt. Tiếp tục luyện tập.")
    if st.button("Làm lại từ đầu"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
