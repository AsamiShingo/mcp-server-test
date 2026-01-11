from mcp.server.fastmcp import FastMCP
from typing import Dict
from pathlib import Path
import json
import requests
import os
import sys

BASE_DIR = Path(__file__).resolve().parent
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

with open(BASE_DIR / 'config' / 'url.json', 'r', encoding='utf-8') as f:
    NEWARP_URLS = json.load(f)

with open(BASE_DIR / 'config' / 'logininfo.json', 'r', encoding='utf-8') as f:
    NEWARP_USER_INFO = json.load(f)
    
mcp = FastMCP("NeWarp MCP Server")

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
        # "procUserKey": user_info["PROC_USER_KEY"],
        "procUserKey": "143",
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
    
@mcp.tool(
    name="get_company_organization_master",
    description=(
        "会社全体の組織構造を一覧で取得するツールです。"
        "事業部・部門・グループのすべての階層を含む組織マスタを返します。"
        "組織の全体像を把握したい場合や、"
        "どの事業部・部門・グループが存在するか分からない場合に使用してください。"
        "他の組織検索ツール（事業部・部門・グループ指定）の前段として利用されます。"
        "例: '会社の組織構成を教えて', 'どんな事業部があるか一覧で見たい'"
    )
)
def get_company_organization_master() -> dict:
    try:
        required_files = [
            BASE_DIR / "newarp_data" / "事業部マスタ.json",
            BASE_DIR / "newarp_data" / "部門マスタ.json",
            BASE_DIR / "newarp_data" / "課マスタ.json",
        ]
        if any(not os.path.isfile(f) for f in required_files):
            with requests.Session() as session:
                login_newarp(session)
                dewonload_division_master(session, required_files[0])
                dewonload_department_master(session, required_files[1])
                dewonload_group_master(session, required_files[2])

        with open(required_files[0], 'r', encoding='utf-8') as f:
            division_data = json.load(f)

        with open(required_files[1], 'r', encoding='utf-8') as f:
            department_data = json.load(f)

        with open(required_files[2], 'r', encoding='utf-8') as f:
            group_data = json.load(f)

        division_map = {d["divisionCode"]: d for d in division_data}
        department_map = {d["departmentCode"]: d for d in department_data}

        result_data = []
        for group in group_data:
            department_code = group["departmentCode"]
            department = department_map.get(department_code, {})

            division_code = department["divisionCode"]
            division = division_map.get(division_code, {})

            result_data.append({
                # 事業部
                "事業部コード": division.get("divisionCode", ""),
                "事業部名": division.get("divisionName", ""),
                "事業部短縮名": division.get("divisionShortName", ""),

                # 部門
                "部門コード": department.get("departmentCode", ""),
                "部門名": department.get("departmentName", ""),
                "部門短縮名": department.get("departmentShortName", ""),

                # 課
                "グループコード": group.get("groupCode", ""),
                "グループ名": group.get("groupName", ""),
                "グループ短縮名": group.get("groupShortName", "")
            })

        columns = [
            "事業部コード", "事業部名", "事業部短縮名",
            "部門コード", "部門名", "部門短縮名",
            "グループコード", "グループ名", "グループ短縮名"
        ]

        return {
            "report_title": "会社組織情報",
            "description": (
                "これは会社全体の組織情報です。"
                "事業部 → 部門 → グループの階層構造を1行ずつ表しています。"
                "各行は1つのグループに対応し、上位の事業部・部門情報を含みます。"
            ),
            "analysis_instruction": (
                "このデータから事業部・部門・グループの階層構造を整理し、質問で求められている組織単位や名称を特定してください。"
                "全体構造の説明が求められている場合は、上位から順に分かりやすく文章でまとめてください。"
            ),
            "columns": columns,
            "data": result_data,
        }
    except Exception as e:
        print(str(e), file=sys.stderr)
        return {"error": str(e)}
    
@mcp.tool(
    name="get_division_master",
    description=(
        "事業部単位で組織情報を取得するツールです。"
        "事業部短縮名（divisionShortName）を指定して検索します。"
        "指定した事業部に属する部門およびグループ一覧を返します。"
        "特定の事業部にどの部門・グループがあるかを知りたい質問のときに使用してください。"
        "例: '営業事業部にはどんな部門がある？', 'BSS事業部の組織構成を教えて'"
    )
)
def get_division_master(divisionShortName: str) -> dict:
    """
    Args:
        divisionShortName: 検索対象の事業部短縮名（完全一致）
    """
    result = get_company_organization_master()
    if "error" in result:
        return result
    
    all_data = result["data"]
    result_data = []
    for data in all_data:
        if data["事業部短縮名"] == divisionShortName:
            result_data.append(data)

    if not result_data:
        return {
            "report_title": "事業部情報",
            "description": "指定された事業部は見つかりませんでした。",
            "analysis_instruction": "該当する事業部が存在しないことをユーザーに伝えてください。",
            "columns": result["columns"],
            "data": [],
        }

    return {
            "report_title": "事業部情報",
            "description": "これは指定された事業部の情報です。事業部→部門→グループの構造を表しています。",
            "analysis_instruction": "質問で求められている情報を文章で回答してください。",
            "columns": result["columns"],
            "data": result_data,
        }
    
@mcp.tool(
    name="get_department_master",
    description=(
        "部門単位で組織情報を取得するツールです。"
        "部門短縮名（departmentShortName）を指定して検索します。"
        "指定した部門に属するグループ一覧と、上位の事業部情報を含めて返します。"
        "特定の部門にどのグループが属しているか、またその部門の事業部を知りたい質問のときに使用してください。"
        "例: '営業部にはどんなグループがある？', 'BSS部門はどの事業部？'"
    )
)
def get_department_master(departmentShortName: str) -> dict:
    """
    Args:
        departmentShortName: 検索対象の部門短縮名（完全一致）
    """
    result = get_company_organization_master()
    if "error" in result:
        return result
    
    all_data = result["data"]
    result_data = []
    for data in all_data:
        if data["部門短縮名"] == departmentShortName:
            result_data.append(data)

    if not result_data:
        return {
            "report_title": "部門情報",
            "description": "指定された部門は見つかりませんでした。",
            "analysis_instruction": "該当する部門が存在しないことをユーザーに伝えてください。",
            "columns": result["columns"],
            "data": [],
        }

    return {
            "report_title": "部門情報",
            "description": "これは指定された部門の情報です。事業部→部門→グループの構造を表しています。",
            "analysis_instruction": "質問で求められている情報を文章で回答してください。",
            "columns": result["columns"],
            "data": result_data,
        }
    
@mcp.tool(
    name="get_group_master",
     description=(
        "グループ（課）単位の組織情報を取得するツールです。"
        "グループ短縮名（groupShortName）を指定して検索します。"
        "事業部・部門・グループの階層構造を含む情報を返します。"
        "特定のグループがどの事業部・部門に属しているかを知りたい質問のときに使用してください。"
        "例: 'BSSグループはどの部門？', '○○グループの所属事業部を教えて'"
    )
)
def get_group_master(groupShortName: str) -> dict:
    """
    Args:
        groupShortName: 検索対象のグループ短縮名（完全一致）
    """    
    result = get_company_organization_master()
    if "error" in result:
        return result
    
    all_data = result["data"]
    result_data = []
    for data in all_data:
        if data["グループ短縮名"] == groupShortName:
            result_data.append(data)

    if not result_data:
        return {
            "report_title": "グループ情報",
            "description": "指定されたグループは見つかりませんでした。",
            "analysis_instruction": "該当するグループが存在しないことをユーザーに伝えてください。",
            "columns": result["columns"],
            "data": [],
        }

    return {
            "report_title": "グループ情報",
            "description": "これは指定されたグループの情報です。事業部→部門→グループの構造を表しています。",
            "analysis_instruction": "質問で求められている情報を文章で回答してください。",
            "columns": result["columns"],
            "data": result_data,
        }

@mcp.tool(
    name="get_user_master",
    description=(
        "社員（ユーザ）情報を検索して返すツールです。"
        "社員名（userName）をもとにユーザマスタを検索します。"
        "userName は部分一致で検索されます。"
        "社員の氏名、メールアドレス、所属グループ、役職などを知りたい質問のときに使用してください。"
        "例: '山田太郎のメールアドレスは？', '佐藤という名前の社員一覧を出して'"
    )
)
def get_user_master(userName: str) -> dict:
    """
    Args:
        userName: 検索したい社員名（部分一致）
    """
    try:
        user_master_file = BASE_DIR / "newarp_data" / "ユーザマスタ.json"
        if not os.path.isfile(user_master_file):
            with requests.Session() as session:
                login_newarp(session)
                download_user_master(session, user_master_file)

        with open(user_master_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)

        columns = [
            "ユーザID", "ユーザ名", "メールアドレス", "グループ短縮名", "役職", "入社日"
        ]

        result_data = []
        for user in user_data:
            if userName in user.get("userName"):
                result_data.append({
                    "ユーザID": user.get("userId", ""),
                    "ユーザ名": user.get("userName", ""),
                    "メールアドレス": user.get("mailAddress", ""),
                    "グループ短縮名": user.get("groupShortName", ""),
                    "役職": user.get("position", ""),
                    "入社日": user.get("joiningDate", "")
                })

        if not result_data:
            return {
                "report_title": "ユーザ情報",
                "description": "該当する社員が見つかりませんでした。",
                "analysis_instruction": "該当者がいない旨をユーザーに伝えてください。",
                "columns": columns,
                "data": [],
            }

        return {
            "report_title": "ユーザ情報",
            "description": "これはユーザ情報です。",
            "analysis_instruction": "質問で求められている情報を文章で回答してください。",
            "columns": columns,
            "data": result_data,
        }
    except Exception as e:
        print(str(e), file=sys.stderr)
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()