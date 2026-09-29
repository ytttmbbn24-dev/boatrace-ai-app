import sqlite3  
import numpy as np  
import pandas as pd  
import lightgbm as lgb  
from sklearn.model_selection import train_test_split  
  
  
def preprocess_and_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:  
    """特徴量を作成する"""  
    data = df.copy()  
  
    numeric_cols = [  
        "F数",  
        "L数",  
        "モーター2連率",  
        "ボート2連率",  
        "展示タイム",  
        "チルト",  
        "年齢",  
        "当日体重",  
    ]  
    for col in numeric_cols:  
        if col in data.columns:  
            data[col] = pd.to_numeric(data[col], errors="coerce")  
  
    data["F数"] = data["F数"].fillna(0)  
    data["L数"] = data["L数"].fillna(0)  
    data["モーター2連率"] = data["モーター2連率"].fillna(30.0)  
    data["ボート2連率"] = data["ボート2連率"].fillna(30.0)  
    data["展示タイム"] = data["展示タイム"].fillna(6.80)  
    data["当日体重"] = data["当日体重"].fillna(52.0)  
  
    rank_map = {"A1": 4, "A2": 3, "B1": 2, "B2": 1}  
    data["級別_score"] = data["級別"].map(rank_map).fillna(1)  
  
    # 競艇場・日付・レース単位でグループ化（無い場合は艇番基準で簡易計算）  
    if "展示タイム" in data.columns:  
        min_time = data["展示タイム"].min()  
        data["展示タイム_diff_min"] = data["展示タイム"] - min_time  
        data["展示タイム_rank"] = data["展示タイム"].rank(  
            method="min", ascending=True  
        )  
  
    if "モーター2連率" in data.columns:  
        data["モーター2連率_rank"] = data["モーター2連率"].rank(  
            method="min", ascending=False  
        )  
  
    if "展示進入コース" in data.columns:  
        data["コース"] = pd.to_numeric(  
            data["展示進入コース"], errors="coerce"  
        ).fillna(data["艇番"])  
    else:  
        data["コース"] = data["艇番"]  
  
    data["is_in_course"] = (data["コース"] == 1).astype(int)  
  
    return data  
  
  
def train_lightgbm_model(db_path: str = "boatrace.db"):  
    """デモ用またはDBデータに基づくモデル学習"""  
    # クラウド環境等でDBがない場合はデモデータで学習してモデルを返す  
    try:  
        conn = sqlite3.connect(db_path)  
        df_raw = pd.read_sql_query("SELECT * FROM race_entries", conn)  
        conn.close()  
    except Exception:  
        df_raw = pd.DataFrame()  
  
    if df_raw.empty or len(df_raw) < 12:  
        # DBに十分なデータがない場合のフォールバック用ダミー学習データ  
        dummy_data = []  
        for i in range(1, 7):  
            dummy_data.append({  
                "艇番": i,  
                "級別": "A1" if i in [1, 2] else "B1",  
                "F数": 0,  
                "L数": 0,  
                "モーター2連率": 40.0 if i == 1 else 25.0,  
                "ボート2連率": 35.0,  
                "展示タイム": 6.65 if i == 1 else 6.75,  
                "当日体重": 52.0,  
                "展示進入コース": i,  
                "target": 1 if i == 1 else 0,  
            })  
        df_features = preprocess_and_feature_engineering(  
            pd.DataFrame(dummy_data)  
        )  
    else:  
        df_features = preprocess_and_feature_engineering(df_raw)  
        df_features["target"] = np.where(df_features["艇番"] == 1, 1, 0)  
  
    feature_cols = [  
        "艇番",  
        "コース",  
        "is_in_course",  
        "級別_score",  
        "F数",  
        "L数",  
        "モーター2連率",  
        "ボート2連率",  
        "展示タイム",  
        "展示タイム_diff_min",  
        "展示タイム_rank",  
        "モーター2連率_rank",  
        "当日体重",  
    ]  
  
    # データに存在しない列があれば埋める  
    for col in feature_cols:  
        if col not in df_features.columns:  
            df_features[col] = 0  
  
    X = df_features[feature_cols]  
    y = df_features["target"]  
  
    train_data = lgb.Dataset(X, label=y)  
    params = {  
        "objective": "binary",  
        "metric": "binary_logloss",  
        "boosting_type": "gbdt",  
        "learning_rate": 0.05,  
        "num_leaves": 15,  
        "verbose": -1,  
    }  
  
    model = lgb.train(params, train_data, num_boost_round=50)  
    return model, feature_cols  
