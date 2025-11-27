import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Cấu hình trang
st.set_page_config(page_title="FinAI Evaluation Dashboard", layout="wide")

st.title("📊 Bảng Điều Khiển Chất Lượng FinAI")
st.markdown("Trực quan hóa hiệu năng của hệ thống RAG và Multi-Agent.")

# --- HÀM LOAD DỮ LIỆU ---
@st.cache_data
def load_data():
    data = {}
    
    # Map đổi tên cột từ chuẩn Ragas v0.2+ sang chuẩn cũ của Dashboard
    rename_map = {
        'user_input': 'question',
        'response': 'answer',
        'reference': 'ground_truth',
        'retrieved_contexts': 'contexts'
    }
    
    # 1. Load RAG Report
    if os.path.exists("rag_evaluation_report.csv"):
        df_rag = pd.read_csv("rag_evaluation_report.csv")
        data["rag"] = df_rag.rename(columns=rename_map)
    
    # 2. Load Sub-Agent Report (File này do ta tự tạo, ko cần rename)
    if os.path.exists("sub_agents_score_card.csv"):
        data["agents"] = pd.read_csv("sub_agents_score_card.csv")
        
    # 3. Load Editor Report (Cũng do Ragas tạo -> Cần rename)
    if os.path.exists("editor_faithfulness_report.csv"):
        df_editor = pd.read_csv("editor_faithfulness_report.csv")
        data["editor"] = df_editor.rename(columns=rename_map)
        
    return data

data = load_data()

# --- TẠO TABS ---
tab1, tab2, tab3 = st.tabs(["📈 Đánh giá RAG (BCTC)", "🤖 Đánh giá Sub-Agents", "📝 Đánh giá Editor"])

# ==================================================
# TAB 1: RAG EVALUATION
# ==================================================
with tab1:
    if "rag" in data:
        df = data["rag"]
        
        st.subheader("1. Điểm số trung bình")
        
        metrics = {
            "Answer Correctness": "answer_correctness",
            "Faithfulness": "faithfulness",
            "Context Recall": "context_recall",
            "Context Precision": "context_precision",
            "Answer Relevancy": "answer_relevancy"
        }
        
        cols = st.columns(5)
        avg_scores = {}
        
        valid_metrics = {}
        for label, col_name in metrics.items():
            if col_name in df.columns:
                valid_metrics[label] = col_name

        for i, (label, col_name) in enumerate(valid_metrics.items()):
            if i < 5:
                score = df[col_name].mean()
                avg_scores[label] = score
                cols[i].metric(label, f"{score:.2f}")

        st.subheader("2. Biểu đồ cân bằng hệ thống")
        if avg_scores:
            fig = px.line_polar(
                r=list(avg_scores.values()),
                theta=list(avg_scores.keys()),
                line_close=True,
                range_r=[0, 1],
                title="RAG Metrics Overview"
            )
            fig.update_traces(fill='toself')
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("3. Truy vết lỗi (Drill-down)")
        
        if 'answer_correctness' in df.columns:
            score_threshold = st.slider("Lọc các câu hỏi có điểm Correctness dưới:", 0.0, 1.0, 0.6)
            bad_cases = df[df['answer_correctness'] < score_threshold]
            
            st.write(f"Tìm thấy **{len(bad_cases)}** trường hợp điểm thấp:")
            
            display_cols = ['question', 'answer', 'ground_truth', 'answer_correctness']
            if 'faithfulness' in df.columns: display_cols.append('faithfulness')
            if 'context_precision' in df.columns: display_cols.append('context_precision')
            
            st.dataframe(bad_cases[display_cols])
            
            with st.expander("🔍 Xem chi tiết ngữ cảnh (Context) của các câu điểm thấp"):
                for index, row in bad_cases.iterrows():
                    st.markdown(f"**Q:** {row['question']}")
                    st.markdown(f"**Bot:** {row['answer']}")
                    st.markdown(f"**Thực tế:** {row['ground_truth']}")
                    ctx = row.get('contexts', '')
                    st.caption(f"Contexts: {str(ctx)[:500]}...")
                    st.divider()
        else:
            st.dataframe(df)

    else:
        st.warning("Chưa có file 'rag_evaluation_report.csv'. Hãy chạy evaluate_rag.py trước.")

# ==================================================
# TAB 2: SUB-AGENTS EVALUATION
# ==================================================
with tab2:
    if "agents" in data:
        df_agent = data["agents"]
        st.subheader("Hiệu năng của các Chuyên gia con (Thang 5)")
        
        agent_cols = [c for c in df_agent.columns if "_score" in c]
        if agent_cols:
            avg_agent_scores = df_agent[agent_cols].mean()
            fig = px.bar(
                x=[c.replace("_score", "").upper() for c in agent_cols],
                y=avg_agent_scores.values,
                color=avg_agent_scores.values,
                labels={'x': 'Agent', 'y': 'Điểm trung bình (1-5)'},
                range_y=[0, 5],
                title="So sánh chất lượng giữa các Agent"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Chi tiết từng phiên chạy")
        st.dataframe(df_agent)
    else:
        st.warning("Chưa có file 'sub_agents_score_card.csv'. Hãy chạy evaluate_sub_agents.py trước.")

# ==================================================
# TAB 3: EDITOR EVALUATION
# ==================================================
with tab3:
    if "editor" in data:
        df_editor = data["editor"]
        st.subheader("Độ trung thực của Editor (Trưởng phòng)")
        
        if 'faithfulness' in df_editor.columns and 'answer_relevancy' in df_editor.columns:
            col1, col2 = st.columns(2)
            col1.metric("Faithfulness Avg", f"{df_editor['faithfulness'].mean():.2f}")
            col2.metric("Relevancy Avg", f"{df_editor['answer_relevancy'].mean():.2f}")
            
            fig = px.scatter(
                df_editor,
                x="faithfulness",
                y="answer_relevancy",
                # --- ĐÃ FIX: Bây giờ cột 'question' đã có nhờ hàm load_data ---
                hover_data=["question"], 
                title="Phân bố chất lượng bài viết",
                color="faithfulness"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Dữ liệu chi tiết")
        st.dataframe(df_editor)
    else:
        st.info("Chưa có file 'editor_faithfulness_report.csv'. Hãy chạy evaluate_editor.py trước.")