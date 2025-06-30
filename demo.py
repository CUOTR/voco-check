import streamlit as st
import pandas as pd
import random
import re

# --- Cấu hình ---
EXCEL_FILE = "1.Everyday language.xlsx"

# --- Tiền xử lý ---
def normalize(text):
    if isinstance(text, str):
        return re.sub(r'\s+', ' ', text.strip().lower())
    return ''

@st.cache_data
def load_data(sheet_choice):
    sheets_to_read = [f"Sheet{i}" for i in range(1, sheet_choice + 1)]
    df_list = []
    for sheet in sheets_to_read:
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)
            df.columns = ['Vocabulary', 'Phonetic', 'Meaning', 'Example']
            df = df.dropna()
            df_list.append(df)
        except Exception as e:
            st.error(f"Không thể đọc {sheet}: {e}")
    if not df_list:
        return pd.DataFrame()
    combined_df = pd.concat(df_list, ignore_index=True)
    for col in ['Vocabulary', 'Phonetic', 'Meaning', 'Example']:
        combined_df[col + '_norm'] = combined_df[col].apply(normalize)
    return combined_df

def get_random_entries(df, exclude_indexes, count):
    attempts = 0
    selected = []
    used_texts = set()
    max_attempts = 500

    while len(selected) < count and attempts < max_attempts:
        idx = random.randint(0, len(df) - 1)
        if idx in exclude_indexes or idx in selected:
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
        return None
    return selected

def run_quiz(df, indexes, mode):
    st.write("📝 Trả lời 25 câu hỏi. Kết quả sẽ hiển thị sau khi hoàn thành.")
    answers = {}
    for i, idx in enumerate(indexes, 1):
        row = df.iloc[idx]
        if mode == 'vocab_to_meaning':
            prompt_type = random.choice(['Vocabulary', 'Phonetic', 'Example'])
            prompt = row[prompt_type]
            correct = row['Meaning_norm']
            question = f"{i}. {prompt_type}: {prompt}"
        else:
            prompt = row['Meaning']
            correct = row['Vocabulary_norm']
            question = f"{i}. Nghĩa: {prompt}"
        user_input = st.text_input(question, key=f"{mode}_{i}")
        answers[i] = (normalize(user_input), correct, row)
    return answers

def evaluate(answers, mode_label):
    st.subheader(f"📊 Kết quả kiểm tra {mode_label}")
    correct = 0
    wrong = []

    for i, (user_input, correct_answer, row) in answers.items():
        if user_input == correct_answer:
            correct += 1
        else:
            wrong.append((i, user_input, correct_answer, row))

    st.write(f"✅ Số câu đúng: {correct}/25")
    if correct >= 20:
        st.success("🎉 Bạn đã vượt qua!")
    else:
        st.warning("🔁 Bạn chưa vượt qua.")

    if wrong:
        with st.expander("📌 Các câu sai"):
            for i, user_input, correct_answer, row in wrong:
                if mode_label == 1:
                    st.markdown(f"**Câu {i}** — {row['Vocabulary']} → _{row['Meaning']}_, bạn trả lời: _{user_input}_")
                else:
                    st.markdown(f"**Câu {i}** — {row['Meaning']} → _{row['Vocabulary']}_ , bạn trả lời: _{user_input}_")

# --- Giao diện chính ---
def main():
    st.title("📘 Ứng dụng kiểm tra từ vựng tiếng Anh")
    st.markdown("Học và kiểm tra từ vựng theo các sheet trong file Excel.")

    sheet_num = st.number_input("Chọn số sheet để học (1–10):", min_value=1, max_value=10, step=1)

    if st.button("🚀 Bắt đầu kiểm tra"):
        df = load_data(sheet_num)

        if df.empty:
            st.error("⚠ Không có dữ liệu hợp lệ.")
            return

        if len(df) < 50:
            st.warning("⚠ Dữ liệu hiện tại có thể không đủ để tạo 2 bài kiểm tra với 25 câu mỗi bài.")

        st.success(f"✅ Đã tải {len(df)} từ vựng từ {sheet_num} sheet.")

        used_indexes = get_random_entries(df, set(), 25)
        if not used_indexes:
            st.error("❗ Không đủ dữ liệu cho bài kiểm tra 1.")
            return

        st.header("🧪 Kiểm tra 1: Cho từ, tìm nghĩa")
        answers1 = run_quiz(df, used_indexes, mode='vocab_to_meaning')

        remaining_indexes = get_random_entries(df, set(used_indexes), 25)
        if not remaining_indexes:
            st.error("❗ Không đủ dữ liệu cho bài kiểm tra 2.")
            return

        st.header("🧪 Kiểm tra 2: Cho nghĩa, tìm từ")
        answers2 = run_quiz(df, remaining_indexes, mode='meaning_to_vocab')

        if st.button("📊 Xem kết quả"):
            evaluate(answers1, mode_label=1)
            evaluate(answers2, mode_label=2)

if __name__ == "__main__":
    main()
