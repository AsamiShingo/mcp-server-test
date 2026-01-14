from pathlib import Path
import json
import requests

BASE_DIR = Path(__file__).resolve().parent
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

with open(BASE_DIR / 'config' / 'url.json', 'r', encoding='utf-8') as f:
    NEWARP_URLS = json.load(f)

with open(BASE_DIR / 'config' / 'logininfo.json', 'r', encoding='utf-8') as f:
    NEWARP_USER_INFO = json.load(f)

def login_newarp(session: requests.Session):
    payload = {
        "engageCode": NEWARP_USER_INFO["ENGAGE_CODE"],
        "userId": NEWARP_USER_INFO["USER_ID"],
        "pass": NEWARP_USER_INFO["PASSWORD"]
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }

    response = session.post(NEWARP_URLS["LOGIN"], json=payload, headers=headers)
    response.raise_for_status() # 200番台以外は例外を投げる

def download_json(session: requests.Session, url: str, referer: str, payload, save_filepath: str):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Referer": referer
    }

    response = session.post(url, json=payload, headers=headers)
    response.raise_for_status()

    response_json = response.json()
    data_only = response_json.get('data')
    with open(save_filepath, 'w', encoding='utf-8') as f:
        json.dump(data_only, f, ensure_ascii=False, indent=2)


# 事業部マスタ
def dewonload_division_master(session: requests.Session, save_filepath: str):
    url = NEWARP_URLS["GET_DIVISION_MASTER"]
    referer = NEWARP_URLS["GET_DIVISION_MASTER_REFERER"]
    payload = {
        "divisionName": "",
        "divisionShortName": ""
    }
    download_json(session, url, referer, payload, save_filepath)

# 部門マスタ
def dewonload_department_master(session: requests.Session, save_filepath: str):
    url = NEWARP_URLS["GET_DEPARTMENT_MASTER"]
    referer = NEWARP_URLS["GET_DEPARTMENT_MASTER_REFERER"]
    payload = {
        "departmentKey": "",
        "departmentName": "",
        "departmentShortName": ""
    }
    download_json(session, url, referer, payload, save_filepath)

# 課マスタ
def dewonload_group_master(session: requests.Session, save_filepath: str):
    url = NEWARP_URLS["GET_GROUP_MASTER"]
    referer = NEWARP_URLS["GET_GROUP_MASTER_REFERER"]
    payload = {
        "divisionKey": "",
        "departmentKey": "",
        "groupName": "",
        "groupShortName": ""
    }
    download_json(session, url, referer, payload, save_filepath)

# ユーザマスタ
def download_user_master(session: requests.Session, save_filepath: str):
    url = NEWARP_URLS["GET_USER_MASTER"]
    referer = NEWARP_URLS["GET_USER_MASTER_REFERER"]
    payload = {
        "procUserKey": NEWARP_USER_INFO["PROC_USER_KEY"],
        "userId": "",
        "userKbnId": "1",
        "isNotRetire": "on",
        "userName": "",
        "departmentKey": "",
        "groupKey": "",
        "positionId": "",
        "authorityId": ""
    }
    download_json(session, url, referer, payload, save_filepath)

# FB面談シート
def download_fb_interview_sheet(session: requests.Session, save_filepath: str, user_key: str):
    url = NEWARP_URLS["GET_FB_INTERVIEW_SHEET"]
    referer = NEWARP_URLS["GET_FB_INTERVIEW_SHEET_REFERER"]
    payload = {
        "userKey": user_key,
        "goalManagementPeriodId": NEWARP_USER_INFO["FB_INTERVIEW_YEAR_MONTH"]
    }
    download_json(session, url, referer, payload, save_filepath)