import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from combined_script import get_combined_race_data
except ImportError:
    st.error("combined_script.py が同じフォルダに見つかりません。ファイル名を確認してください。")

st.set_page_config(page_title="競艇AI予想ダッシュボード", page_icon="🚤", layout="wide")

JCD_MAP = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}

def main():
    st.title("🚤 競艇AI予想ダッシュボード")

    st.sidebar.header("🔍 レース選択")
    selected_date = st.sidebar.date_input("日付").strftime("%Y%m%d")
    
    jcd_options = {f"{code} : {name}": code for code, name in JCD_MAP.items()}
    selected_jcd_label = st.sidebar.selectbox("競艇場", list(jcd_options.keys()), index=18) # デフォルト下関
    selected_jcd = jcd_options[selected_jcd_label]
    
    selected_rno = st.sidebar.slider("レース番号 (R)", 1, 12, 9)
    fetch_btn = st.sidebar.button("🤖 予想を実行する", type="primary")

    if fetch_btn or "has_run" in st.session_state:
        st.session_state["has_run"] = True
        
        with st.spinner("データを取得・AI解析中..."):
            df_race = get_combined_race_data(selected_jcd, selected_rno, selected_date)

            if df_race is None or df_race.empty:
                st.error("データの取得に失敗しました。")
                return

            # スコア計算ロジック
            m_2ren = pd.to_numeric(df_race.get("モーター2連率", 30.0), errors="coerce").fillna(30.0)
            ex_time = pd.to_numeric(df_race.get("展示タイム", 6.80), errors="coerce").fillna(6.80)
            
            course_weights = np.array([3.5, 2.0, 1.5, 1.2, 0.8, 0.5])
            raw_scores = course_weights + (m_2ren.values / 20.0) + ((7.0 - ex_time.values) * 2.0)
            
            exp_scores = np.exp(raw_scores - np.max(raw_scores))
            probs = np.round((exp_scores / exp_scores.sum()) * 100, 1)
            
            df_race["1着確率(%)"] = probs
            df_result = df_race.sort_values("1着確率(%)", ascending=False)

            st.subheader(f"📊 【{selected_date}】 {JCD_MAP[selected_jcd]} {selected_rno}R 予想結果")

            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown("#### 艇番別 1着予測確率")
                fig = px.bar(
                    df_result.sort_values("艇番"),
                    x="艇番",
                    y="1着確率(%)",
                    text="1着確率(%)",
                    color="艇番",
                    color_discrete_map={1: "#E0E0E0", 2: "#333333", 3: "#E53935", 4: "#1E88E5", 5: "#FDD835", 6: "#43A047"},
                )
                fig.update_traces(texttemplate="%{text}%", textposition="outside")
                fig.update_layout(showlegend=False, yaxis=dict(range=[0, 100]))
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("#### 🎯 AI推奨 3連単買い目")
                ranked = df_result["艇番"].tolist()
                b1, b2, b3, b4 = ranked[0], ranked[1], ranked[2], ranked[3]

                bets = [
                    (f"{b1} - {b2} - {b3}", "本線 (確率最高)"),
                    (f"{b1} - {b2} - {b4}", "本線抑え"),
                    (f"{b1} - {b3} - {b2}", "対抗好走"),
                    (f"{b1} - {b3} - {b4}", "中穴狙い"),
                    (f"{b2} - {b1} - {b3}", "逆転狙い"),
                ]

                for combo, label in bets:
                    st.success(f"**{combo}** \t *({label})*")

            st.markdown("---")
            st.markdown("#### 📋 出走表 ＆ 分析データ")
            disp_cols = ["艇番", "選手名", "級別", "1着確率(%)", "展示タイム", "モーター2連率", "F数"]
            disp_cols = [c for c in disp_cols if c in df_race.columns]
            st.dataframe(
                df_race[disp_cols]
                .sort_values("艇番")
                .reset_index(drop=True),
                use_container_width=True,
            )

if __name__ == "__main__":
    main()
