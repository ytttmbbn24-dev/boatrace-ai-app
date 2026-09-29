import re  
import time  
import pandas as pd  
import requests  
from bs4 import BeautifulSoup  
  
  
def get_race_card(jcd: str, rno: int, date_str: str) -> pd.DataFrame:  
    """指定した競艇場・レース番号・日付の出走表詳細データを取得する"""  
    jcd_str = f"{int(jcd):02d}"  
    url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd_str}&hd={date_str}"  
    headers = {  
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  
    }  
  
    try:  
        response = requests.get(url, headers=headers, timeout=10)  
        response.raise_for_status()  
    except Exception:  
        return pd.DataFrame()  
  
    soup = BeautifulSoup(response.text, "html.parser")  
    tbodies = soup.select("table.is-w780 tbody")  
  
    if not tbodies:  
        return pd.DataFrame()  
  
    race_data = []  
    for idx, tbody in enumerate(tbodies, 1):  
        rows = tbody.find_all("tr")  
        if not rows:  
            continue  
  
        boat_number = idx  
        name_box = tbody.select_one(".is-fs18")  
        player_name = (  
            name_box.get_text(strip=True).replace(" ", "") if name_box else ""  
        )  
  
        toban_box = tbody.select_one(".is-fs11")  
        toban = (  
            re.search(r"\d{4}", toban_box.get_text()).group()  
            if toban_box  
            else ""  
        )  
  
        rank_tag = tbody.select_one("span[class*='is-rank']")  
        rank = rank_tag.get_text(strip=True) if rank_tag else ""  
  
        p_info_text = (  
            tbody.select_one("div.is-fs11").parent.get_text(" ")  
            if tbody.select_one("div.is-fs11")  
            else ""  
        )  
        age_match = re.search(r"(\d{2})歳", p_info_text)  
        weight_match = re.search(r"(\d{2}\.\d)kg", p_info_text)  
        branch_match = re.search(r"([一-龥]{2,4})/", p_info_text)  
  
        age = age_match.group(1) if age_match else ""  
        weight = weight_match.group(1) if weight_match else ""  
        branch = branch_match.group(1) if branch_match else ""  
  
        fl_td = (  
            rows[0].find_all("td")[4]  
            if len(rows[0].find_all("td")) > 4  
            else None  
        )  
        fl_text = fl_td.get_text(strip=True) if fl_td else ""  
        f_count = (  
            re.search(r"F(\d)", fl_text).group(1)  
            if re.search(r"F(\d)", fl_text)  
            else "0"  
        )  
        l_count = (  
            re.search(r"L(\d)", fl_text).group(1)  
            if re.search(r"L(\d)", fl_text)  
            else "0"  
        )  
  
        motor_td = (  
            rows[0].find_all("td")[6]  
            if len(rows[0].find_all("td")) > 6  
            else None  
        )  
        motor_text = (  
            motor_td.get_text(separator=" ", strip=True) if motor_td else ""  
        )  
        motor_matches = re.findall(r"\d+\.\d+|\d+", motor_text)  
        motor_num = motor_matches[0] if len(motor_matches) > 0 else ""  
        motor_2ren = motor_matches[1] if len(motor_matches) > 1 else ""  
  
        boat_td = (  
            rows[0].find_all("td")[7]  
            if len(rows[0].find_all("td")) > 7  
            else None  
        )  
        boat_text = (  
            boat_td.get_text(separator=" ", strip=True) if boat_td else ""  
        )  
        boat_matches = re.findall(r"\d+\.\d+|\d+", boat_text)  
        boat_num = boat_matches[0] if len(boat_matches) > 0 else ""  
        boat_2ren = boat_matches[1] if len(boat_matches) > 1 else ""  
  
        race_data.append({  
            "艇番": boat_number,  
            "登番": toban,  
            "選手名": player_name,  
            "級別": rank,  
            "支部": branch,  
            "年齢": age,  
            "体重": weight,  
            "F数": f_count,  
            "L数": l_count,  
            "モーター番号": motor_num,  
            "モーター2連率": motor_2ren,  
            "ボート番号": boat_num,  
            "ボート2連率": boat_2ren,  
        })  
  
    return pd.DataFrame(race_data)  
  
  
def get_before_info(jcd: str, rno: int, date_str: str) -> pd.DataFrame:  
    """直前情報を取得する"""  
    jcd_str = f"{int(jcd):02d}"  
    url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd_str}&hd={date_str}"  
    headers = {  
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  
    }  
  
    try:  
        response = requests.get(url, headers=headers, timeout=10)  
        response.raise_for_status()  
    except Exception:  
        return pd.DataFrame()  
  
    soup = BeautifulSoup(response.text, "html.parser")  
    tbodies = soup.select("table.is-w780 tbody")  
  
    if not tbodies:  
        return pd.DataFrame()  
  
    info_list = []  
    for idx, tbody in enumerate(tbodies, 1):  
        rows = tbody.find_all("tr")  
        if not rows:  
            continue  
  
        boat_number = idx  
        weight_td = (  
            rows[0].find_all("td")[2]  
            if len(rows[0].find_all("td")) > 2  
            else None  
        )  
        weight = (  
            weight_td.get_text(strip=True).replace("kg", "")  
            if weight_td  
            else ""  
        )  
  
        ex_time_td = (  
            rows[0].find_all("td")[4]  
            if len(rows[0].find_all("td")) > 4  
            else None  
        )  
        ex_time = ex_time_td.get_text(strip=True) if ex_time_td else ""  
  
        tilt_td = (  
            rows[0].find_all("td")[5]  
            if len(rows[0].find_all("td")) > 5  
            else None  
        )  
        tilt = tilt_td.get_text(strip=True) if tilt_td else ""  
  
        info_list.append({  
            "艇番": boat_number,  
            "当日体重": weight,  
            "展示タイム": ex_time,  
            "チルト": tilt,  
        })  
  
    df_base = pd.DataFrame(info_list)  
  
    st_box = soup.select_one("div.stExhibition")  
    st_data = {}  
    entry_course_map = {}  
  
    if st_box:  
        st_rows = st_box.select(".table1 tbody tr")  
        for row in st_rows:  
            boat_num_tag = row.select_one("span[class*='is-boatColor']")  
            st_time_tag = row.select_one(".st-time")  
  
            if boat_num_tag and st_time_tag:  
                try:  
                    boat_num = int(boat_num_tag.get_text(strip=True))  
                    st_text = st_time_tag.get_text(strip=True)  
                    st_data[boat_num] = st_text  
                except ValueError:  
                    continue  
  
        course_boats = st_box.select("span[class*='is-boatColor']")  
        for course_idx, b_tag in enumerate(course_boats, 1):  
            try:  
                b_num = int(b_tag.get_text(strip=True))  
                entry_course_map[b_num] = course_idx  
            except ValueError:  
                continue  
  
    if not df_base.empty:  
        df_base["展示進入コース"] = df_base["艇番"].map(entry_course_map)  
        df_base["展示ST"] = df_base["艇番"].map(st_data)  
  
    return df_base  
  
  
def get_combined_race_data(  
    jcd: str, rno: int, date_str: str  
) -> pd.DataFrame:  
    """出走表と直前情報を結合して返す"""  
    df_race = get_race_card(jcd, rno, date_str)  
    if df_race.empty:  
        return pd.DataFrame()  
  
    time.sleep(1)  
    df_before = get_before_info(jcd, rno, date_str)  
  
    if df_before.empty:  
        return df_race  
  
    df_combined = pd.merge(df_race, df_before, on="艇番", how="left")  
    return df_combined  
