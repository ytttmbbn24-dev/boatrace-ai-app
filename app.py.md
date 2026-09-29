import sqlite3  
import numpy as np  
import pandas as pd  
import plotly.express as px  
import streamlit as st  
  
try:  
    from ai_predict import (  
        preprocess_and_feature_engineering,  
        train_lightgbm_model,  
    )  
    from combined_script import get_combined_race_data  
except ImportError:  
    st.error("必要なスクリプトが同じフォルダに見つかりません。")  
  
st.set_page_config(  
    page_title="競艇AI予想ダッシュボード", page_icon="🚤", layout="wide"  
)  
  
JCD_MAP = {  
    "01": "桐生",  
    "02": "戸田",  
    "03": "江戸川",  
    "04": "平和島",  
    "05": "多摩川",  
    "06": "浜名湖",  
    "07": "蒲郡",  
    "08": "常滑",  
    "09": "津",  
    "10": "三国",  
    "11": "びわこ",  
    "12": "住之江",  
    "13": "尼崎",  
    "14": "鳴門",  
    "15": "丸亀",  
    "16": "児島",  
    "17": "宮島",  
    "18": "徳山",  
    "19": "下関",  
    "20": "若松",  
    "21": "芦屋",  
    "22": "福岡",  
    "23": "唐津",  
    "24": "大村",  
}  
  
  
@st.cache_resource  
def load_trained_ai_model():  
    model, feature_cols = train_lightgbm_model(db_path="boatrace.db")  
    return model, feature_cols  
  
  
def main():  
    st.title("🚤 競艇AI予想ダッシュボード")  
  
    st.sidebar.header("🔍 レース選択")  
    selected_date = st.sidebar.date_input("日付").strftime("%Y%m%d")  
  
    jcd_options = {f"{code} : {name}": code for code, name in JCD_MAP.items()}  
    selected_jcd_label = st.sidebar.selectbox(  
        "競艇場", list(jcd_options.keys()), index=3  
    )  
    selected_jcd = jcd_options[selected_jcd_label]  
  
    selected_rno = st.sidebar.slider("レース番号 (R)", 1, 12, 11)  
    fetch_btn = st.sidebar.button("🤖 予想を実行する", type="primary")  
  
    if fetch_btn:  
        with st.spinner("データを取得・解析中..."):  
            df_race = pd.DataFrame()  
            try:  
                conn = sqlite3.connect("boatrace.db")  
                query = "SELECT * FROM race_entries WHERE date = ? AND jcd = ? AND rno = ?"  
                df_race = pd.read_sql_query(  
                    query,  
                    conn,  
                    params=(selected_date, selected_jcd, selected_rno),  
                )  
                conn.close()  
            except Exception:  
                pass  
  
            if df_race.empty:  
                df_race = get_combined_race_data(  
                    jcd=selected_jcd, rno=selected_rno, date_str=selected_date  
                )  
  
            if df_race.empty:  
                st.error(  
                    "指定されたレースのデータを取得できませんでした。開催日・時間帯を確認してください。"  
                )  
                return  
  
            model, feature_cols = load_trained_ai_model()  
            if model is None:  
                st.error("AIモデルの読み込みに失敗しました。")  
                return  
  
            df_features = preprocess_and_feature_engineering(df_race)  
  
            for col in feature_cols:  
                if col not in df_features.columns:  
                    df_features[col] = 0  
  
            X_race = df_features[feature_cols]  
            raw_preds = model.predict(X_race)  
            exp_preds = np.exp(raw_preds - np.max(raw_preds))  
            prob_softmax = exp_preds / exp_preds.sum()  
  
            df_features["1着確率(%)"] = np.round(prob_softmax * 100, 1)  
            df_result = df_features.sort_values(  
                "1着確率(%)", ascending=False  
            )  
  
            st.subheader(  
                f"📊 【{selected_date}】 {JCD_MAP[selected_jcd]} {selected_rno}R 予想結果"  
            )  
  
            col1, col2 = st.columns([3, 2])  
  
            with col1:  
                st.markdown("#### 艇番別 1着予測確率")  
                boat_colors = {  
                    1: "#ffffff",  
                    2: "#000000",  
                    3: "#ff0000",  
                    4: "#0000ff",  
                    5: "#ffff00",  
                    6: "#008000",  
                }  
                fig = px.bar(  
                    df_result,  
                    x="艇番",  
                    y="1着確率(%)",  
                    text="1着確率(%)",  
                    color="艇番",  
                    color_discrete_map={b: c for b, c in boat_colors.items()},  
                    labels={"1着確率(%)": "1着確率 (%)", "艇番": "艇番"},  
                )  
                fig.update_traces(  
                    texttemplate="%{text}%", textposition="outside"  
                )  
                fig.update_layout(  
                    showlegend=False, yaxis=dict(range=[0, 100])  
                )  
                st.plotly_chart(fig, use_container_width=True)  
  
            with col2:  
                st.markdown("#### 🎯 AI推奨 3連単買い目")  
                ranked_boats = df_result["艇番"].tolist()  
                b1, b2, b3, b4 = (  
                    ranked_boats[0],  
                    ranked_boats[1],  
                    ranked_boats[2],  
                    ranked_boats[3],  
                )  
  
                bets = [  
                    (f"{b1} - {b2} - {b3}", "本線 (確率最高)"),  
                    (f"{b1} - {b2} - {b4}", "本線抑え"),  
                    (f"{b1} - {b3} - {b2}", "対抗好走"),  
                    (f"{b1} - {b3} - {b4}", "中穴狙い"),  
                    (f"{b2} - {b1} - {b3}", "逆転（頭捻り）"),  
                ]  
  
                for combo, label in bets:  
                    st.success(f"**{combo}**  \t *({label})*")  
  
            st.markdown("---")  
            st.markdown("#### 📋 出走表 ＆ 分析データ")  
            disp_cols = [  
                "艇番",  
                "選手名",  
                "級別",  
                "1着確率(%)",  
                "コース",  
                "展示タイム",  
                "モーター2连率",  
                "F数",  
            ]  
            disp_cols = [c for c in disp_cols if c in df_result.columns]  
            st.dataframe(  
                df_result[disp_cols]  
                .sort_values("艇番")  
                .reset_index(drop=True),  
                use_container_width=True,  
            )  
  
  
if __name__ == "__main__":  
    main()  
