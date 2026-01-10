from mcp.server.fastmcp import FastMCP
from typing import Dict
from pathlib import Path
import json
import requests
import os

BASE_DIR = Path(__file__).resolve().parent
mcp = FastMCP("NeWarp MCP Server")

with open(BASE_DIR / 'config' / 'url.json', 'r', encoding='utf-8') as f:
    newarp_url = json.load(f)

def login_prog(session: requests.Session):
    with open(BASE_DIR / 'config' / 'logininfo.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)

    payload = {
        "engageCode": user_info["ENGAGE_CODE"],
        "userId": user_info["USER_ID"],
        "pass": user_info["PASSWORD"]
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = session.post(newarp_url["LOGIN"], json=payload, headers=headers)
    response.raise_for_status() # 200番台以外は例外を投げる

def download_json(session: requests.Session, url: str, payload, save_filepath: str):
    response = session.post(url, json=payload)
    response.raise_for_status()

    response_json = response.json()
    data_only = response_json.get('data')
    with open(save_filepath, 'w', encoding='utf-8') as f:
        json.dump(data_only, f, ensure_ascii=False, indent=2)

# 事業部マスタ
def dewonload_division_master(session: requests.Session):
    url = newarp_url["GET_DIVISION_MASTER"]
    payload = {
        "divisionName": "",
        "divisionShortName": ""
    }
    download_json(session, url, payload, BASE_DIR / "newarp_data" / "事業部マスタ.json")

# 部門マスタ
def dewonload_department_master(session: requests.Session):
    url = newarp_url["GET_DEPARTMENT_MASTER"]
    payload = {
        "departmentKey": "",
        "departmentName": "",
        "departmentShortName": ""
    }
    download_json(session, url, payload, BASE_DIR / "newarp_data" / "部門マスタ.json")

# 課マスタ
def dewonload_group_master(session: requests.Session):
    url = newarp_url["GET_GROUP_MASTER"]
    payload = {
        "divisionKey": "",
        "departmentKey": "",
        "groupName": "",
        "groupShortName": ""
    }
    download_json(session, url, payload, BASE_DIR / "newarp_data" / "課マスタ.json")

@mcp.tool(
    name="get_company_organization_master",
    description=(
        "会社の組織マスタを返すツールです。"
        "質問内容に関係する組織のデータを必ず返してください。"
        "返却はJSON形式でrows配列を返します。"
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
                login_prog(session)
                dewonload_division_master(session)
                dewonload_department_master(session)
                dewonload_group_master(session)

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
            "description": "これは会社組織情報です。事業部→部門→グループの構造を表しています。",
            "analysis_instruction": "このデータを使って、質問に対する答えを考えてください。",
            "columns": columns,
            "data": result_data,
        }
    except Exception as e:
        print(str(e))
        return {"error": str(e)}
    
@mcp.tool(
    name="get_division_master",
    description=(
        "指定された事業部に所属する会社の組織マスタを返すツールです。"
        "質問内容に関係する組織のデータを必ず返してください。"
        "返却はJSON形式でrows配列を返します。"
    )
)
def get_division_master(divisionShortName: str) -> dict:
    result = get_company_organization_master()
    if "error" in result:
        return result
    
    all_data = result["data"]
    result_data = []
    for data in all_data:
        if data["事業部短縮名"] == divisionShortName:
            result_data.append(data)

    return {
            "report_title": "指定された事業部の情報",
            "description": "これは指定された事業部の情報です。事業部→部門→グループの構造を表しています。",
            "analysis_instruction": "このデータを使って、質問に対する答えを考えてください。",
            "columns": result["columns"],
            "data": result_data,
        }
    
@mcp.tool(
    name="get_department_master",
    description=(
        "指定された部門に所属する会社の組織マスタを返すツールです。"
        "質問内容に関係する組織のデータを必ず返してください。"
        "返却はJSON形式でrows配列を返します。"
    )
)
def get_department_master(departmentShortName: str) -> dict:
    print("arg:" + departmentShortName)
    result = get_company_organization_master()
    if "error" in result:
        return result
    
    all_data = result["data"]
    result_data = []
    for data in all_data:
        if data["部門短縮名"] == departmentShortName:
            result_data.append(data)

    return {
            "report_title": "指定されたグループの情報",
            "description": "これは指定されたグループの情報です。事業部→部門→グループの構造を表しています。",
            "analysis_instruction": "このデータを使って、質問に対する答えを考えてください。",
            "columns": result["columns"],
            "data": result_data,
        }
    
@mcp.tool(
    name="get_group_master",
    description=(
        "指定されたグループの組織マスタを返すツールです。"
        "質問内容に関係する組織のデータを必ず返してください。"
        "返却はJSON形式でrows配列を返します。"
    )
)
def get_group_master(groupShortName: str) -> dict:
    result = get_company_organization_master()
    if "error" in result:
        return result
    
    all_data = result["data"]
    result_data = []
    for data in all_data:
        if data["グループ短縮名"] == groupShortName:
            result_data.append(data)

    return {
            "report_title": "指定されたグループの情報",
            "description": "これは指定されたグループの情報です。事業部→部門→グループの構造を表しています。",
            "analysis_instruction": "このデータを使って、質問に対する答えを考えてください。",
            "columns": result["columns"],
            "data": result_data,
        }

if __name__ == "__main__":
    mcp.run()