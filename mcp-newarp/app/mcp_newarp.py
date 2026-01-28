from fastmcp import FastMCP
from pathlib import Path
import json
import requests
import os
import sys
from newarp_access import *

BASE_DIR = Path(__file__).resolve().parent

with open(BASE_DIR / 'config' / 'logininfo.json', 'r', encoding='utf-8') as f:
    NEWARP_USER_INFO = json.load(f)

mcp = FastMCP("NeWarp MCP Server")

def get_company_organization_data() -> dict:
    try:
        required_files = [
            BASE_DIR / "data" / "事業部マスタ.json",
            BASE_DIR / "data" / "部門マスタ.json",
            BASE_DIR / "data" / "課マスタ.json",
        ]
        if any(not os.path.isfile(f) for f in required_files):
            with requests.Session() as session:
                login_newarp(session)
                dewonload_division_master(session, required_files[0])
                dewonload_department_master(session, required_files[1])
                dewonload_group_master(session, required_files[2])

        with open(required_files[0], 'r', encoding='utf-8') as f:
            division_data = json.load(f).get("data")

        with open(required_files[1], 'r', encoding='utf-8') as f:
            department_data = json.load(f).get("data")

        with open(required_files[2], 'r', encoding='utf-8') as f:
            group_data = json.load(f).get("data")

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
            "columns": columns,
            "data": result_data,
        }
    except Exception as e:
        print(f"会社組織情報取得エラー: {e}", file=sys.stderr)
        return {"error": str(e)}
    
def get_user_data() -> dict:
    """
    Args:
        userName: 検索したい社員名（部分一致）
    """
    try:
        user_master_file = BASE_DIR / "data" / "ユーザマスタ.json"
        if not os.path.isfile(user_master_file):
            with requests.Session() as session:
                login_newarp(session)
                download_user_master(session, user_master_file)

        with open(user_master_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f).get("data")

        columns = [
            "ユーザキー", "ユーザID", "ユーザ名", "メールアドレス", "グループ短縮名", "役職", "入社日"
        ]

        result_data = []
        for user in user_data:
            result_data.append({
                "ユーザキー": user.get("userKey", ""),
                "ユーザID": user.get("userId", ""),
                "ユーザ名": user.get("userName", ""),
                "メールアドレス": user.get("mailAddress", ""),
                "グループ短縮名": user.get("groupShortName", ""),
                "役職": user.get("position", ""),
                "入社日": user.get("joiningDate", "")
            })

        return {
            "columns": columns,
            "data": result_data,
        }
    except Exception as e:
        print(f"ユーザ情報取得エラー: {e}", file=sys.stderr)
        return {"error": str(e)}
    
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
    result = get_company_organization_data()
    if "error" in result:
        return result

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
            "columns": result["columns"],
            "data": result["data"],
        }
    
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
    result = get_company_organization_data()
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
    result = get_company_organization_data()
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
    result = get_company_organization_data()
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
    name="get_user_master_user_name",
    description=(
        "社員（ユーザ）情報を検索して返すツールです。"
        "社員名（userName）をもとにユーザマスタを検索します。"
        "userName は部分一致で検索されます。"
        "社員の氏名、メールアドレス、所属グループ、役職などを知りたい質問のときに使用してください。"
        "例: '山田太郎のメールアドレスは？', '佐藤という名前の社員一覧を出して'"
    )
)
def get_user_master_user_name(userName: str) -> dict:
    """
    Args:
        userName: 検索したい社員名（部分一致）
    """
    result = get_user_data()
    if "error" in result:
        return result
    
    all_data = result["data"]
    result_data = []
    for data in all_data:
        if userName in data["ユーザ名"]:
            result_data.append(data)

    if not result_data:
        return {
            "report_title": "ユーザ情報",
            "description": "該当する社員が見つかりませんでした。",
            "analysis_instruction": "該当者がいない旨をユーザーに伝えてください。",
            "columns": result["columns"],
            "data": [],
        }

    return {
        "report_title": "ユーザ情報",
        "description": "これはユーザ情報です。",
        "analysis_instruction": "質問で求められている情報を文章で回答してください。",
        "columns": result["columns"],
        "data": result_data,
    }

@mcp.tool(
    name="get_user_master_group_short_name",
    description=(
        "社員（ユーザ）情報を検索して返すツールです。"
        "グループ短縮名（groupShortName）をもとにユーザマスタを検索します。"
        "グループに所属する社員の氏名、メールアドレス、所属グループ、役職などを知りたい質問のときに使用してください。"
        "例: 'BTIに所属する社員一覧を出して'"
    )
)
def get_user_master_group_short_name(groupShortName: str) -> dict:
    """
    Args:
        group_short_name: 検索対象のグループ短縮名（完全一致）
    """
    result = get_user_data()
    if "error" in result:
        return result
    
    all_data = result["data"]
    result_data = []
    for data in all_data:
        if groupShortName == data.get("グループ短縮名"):
            result_data.append(data)

    if not result_data:
        return {
            "report_title": "ユーザ情報",
            "description": "該当する社員が見つかりませんでした。",
            "analysis_instruction": "該当者がいない旨をユーザーに伝えてください。",
            "columns": result["columns"],
            "data": [],
        }

    return {
        "report_title": "ユーザ情報",
        "description": "これはユーザ情報です。",
        "analysis_instruction": "質問で求められている情報を文章で回答してください。",
        "columns": result["columns"],
        "data": result_data,
    }

@mcp.tool(
    name="get_user_evaluation",
    description=(
        "社員（ユーザ）の評価面談情報を取得して返すツールです。過去の履歴も含めて返します。"
        "社員名（userName）をもとに検索します。"
        "userName は部分一致で検索されます。"
        "社員の自己評価や得意なこと苦手なこと、キャリアプランややりたいことを質問するときに使用してください。"
        "例: '山田太郎の何が得意？', '佐藤のキャリアプランは何？', '佐藤のスキルは何が得意？'"
    )
)
def get_user_evaluation(userName: str) -> dict:
    """
    Args:
        userName: 検索したい社員名（部分一致）
    """
    try:
        user_response = get_user_data()
        if "error" in user_response:
            return user_response
        
        user_all_data = user_response["data"]
        user_result_data = [user_data for user_data in user_all_data if userName in user_data["ユーザ名"]]

        if not user_result_data:
            return {
                "report_title": "評価面談",
                "description": "該当する社員が見つかりませんでした。",
                "analysis_instruction": "該当者がいない旨をユーザーに伝えてください。",
                "columns": user_response.get("columns"),
                "data": user_result_data,
            }
        elif len(user_result_data) > 1:            
            return {
                "report_title": "評価面談",
                "description": "該当する社員が複数見つかりました。",
                "analysis_instruction": "該当者を1名に絞り込める情報を渡すようにユーザーに伝えてください。",
                "columns": user_response.get("columns"),
                "data": user_result_data,
            }
        
        user_key = user_result_data[0].get("ユーザキー")
        user_name = user_result_data[0].get("ユーザ名")

        inverview_year_months = NEWARP_USER_INFO["FB_INTERVIEW_YEAR_MONTH"]
        all_result_data = []
        for year_month in inverview_year_months:
            fb_interview_sheet_file = BASE_DIR / "data" / ("FB面談シート_" + str(user_key) + "_" + year_month + ".json")
            if not os.path.isfile(fb_interview_sheet_file):
                with requests.Session() as session:
                    login_newarp(session)
                    download_fb_interview_sheet(session, fb_interview_sheet_file, user_key, year_month)

            with open(fb_interview_sheet_file, 'r', encoding='utf-8') as f:
                fb_interview_sheet_data = json.load(f).get("data")

            evaluation_abc_file = BASE_DIR / "data" / ("評価ABC_" + str(user_key) + "_" + year_month + ".json")
            if not os.path.isfile(evaluation_abc_file):
                with requests.Session() as session:
                    login_newarp(session)
                    download_evaluation_abc(session, evaluation_abc_file, user_key, year_month)

            with open(evaluation_abc_file, 'r', encoding='utf-8') as f:
                evaluation_abc_data = json.load(f)

            result_data = {}
            result_data["評価年月"] = fb_interview_sheet_data.get("info").get("periodName")

            fb_interview = {}
            fb_interview["将来のあるべき姿"] = fb_interview_sheet_data.get("info").get("vision")
            fb_interview["アピールポイント"] = fb_interview_sheet_data.get("info").get("appeal")
            fb_interview["会社へ一言"] = fb_interview_sheet_data.get("info").get("note")
            fb_interview["技術分類"] = fb_interview_sheet_data.get("info").get("evaluationKind")
            fb_interview["評価ステージ"] = fb_interview_sheet_data.get("info").get("evaluationStage")
            fb_interview["評価クラス"] = fb_interview_sheet_data.get("info").get("evaluationClass")
            fb_interview["管理職からの期待"] = fb_interview_sheet_data.get("info").get("expectation")
            result_data["評価全体情報"] = fb_interview

            past_goals = []        
            for past_goal in fb_interview_sheet_data.get("pastDetails"):
                past_goals.append({
                    "目標": past_goal.get("goal", ""),
                    "達成条件": past_goal.get("condition", ""),
                    "達成度(%)": past_goal.get("assessment", ""),
                    "実行結果コメント": past_goal.get("comment", ""),
                    "管理職からのコメント": past_goal.get("assessmentComment", ""),
                })
            result_data["前期目標振り返り"] = past_goals

            next_goals = []        
            for next_goal in fb_interview_sheet_data.get("pastDetails"):
                next_goals.append({
                    "目標": next_goal.get("goal", ""),
                    "達成条件": next_goal.get("condition", ""),
                })
            result_data["来季目標"] = next_goals

            skill_evaluations = []
            for skill_evaluation_self in evaluation_abc_data.get("data"):
                if skill_evaluation_self["groupName"] == "業績考課" or skill_evaluation_self["groupName"] == "技術考課":
                    continue
                if not skill_evaluation_self["itemPoints"]:
                    continue

                skill_evaluation_not_self = [not_self for not_self in evaluation_abc_data.get("dataNotSelf") if not_self["evaluationKindId"] == skill_evaluation_self["evaluationKindId"]][0]
                skill_evaluations.append({
                    "スキル種類": skill_evaluation_self.get("groupName", ""),
                    "スキル名": skill_evaluation_self.get("evaluationKind", ""),
                    "自己評価得点": skill_evaluation_self.get("itemPoints", ""),
                    "管理職評価得点": skill_evaluation_not_self.get("itemPoints", "")
                })
            result_data["能力評価得点"] = skill_evaluations

            technical_evaluations = []
            for technical_evaluation_self in evaluation_abc_data.get("data"):
                if technical_evaluation_self["groupName"] != "技術考課":
                    continue
                if not technical_evaluation_self["itemPoints"]:
                    continue

                technical_evaluation_not_self = [not_self for not_self in evaluation_abc_data.get("dataNotSelf") if not_self["evaluationKindId"] == technical_evaluation_self["evaluationKindId"]][0]
                technical_evaluations.append({
                    "スキル種類": technical_evaluation_self.get("groupName", ""),
                    "スキル名": technical_evaluation_self.get("evaluationKind", ""),
                    "自己評価得点": technical_evaluation_self.get("itemPoints", ""),
                    "管理職評価得点": technical_evaluation_not_self.get("itemPoints", "")
                })
            result_data["技術評価得点"] = technical_evaluations

            all_result_data.append(result_data)

        return {
            "report_title": "評価面談情報",
            "description": "これは評価面談情報です。対象者の面談情報と評価得点を過去の情報も含めて取得しています。",
            "analysis_instruction": "質問で求められている情報を文章で回答してください。",
            "data": { "対象者名": user_name, "評価情報": all_result_data },
        }
    except Exception as e:
        print(f"評価面談情報取得エラー：{e}", file=sys.stderr)
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=os.getenv("MCP_HTTP_PORT", "8081"))