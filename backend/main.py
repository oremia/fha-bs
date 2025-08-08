# main.py
# -*- coding: utf-8 -*-
import pandas as pd
import io
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ------------------- 知识库 (来自 fha_core_logic.py) -------------------
FAILURE_MODE_LIBRARY = {
    "通用": ["功能完全丧失", "功能间歇性工作", "功能性能下降", "功能非预期启动"],
    "传感器": ["持续输出错误信息", "输出数据冻结/卡死", "数据跳变/噪声过大", "输出数据延迟"],
    "数据传输": ["数据包丢失", "数据完整性破坏 (误码)", "通信中断"],
    "执行机构": ["无响应/卡死", "响应延迟/迟钝", "动作超调/不到位", "反向运动"],
    "电源": ["电压/电流异常", "供电中断"],
    "导航": ["定位精度下降", "航向错误", "速度信息错误"],
    "飞控算法": ["算法发散", "模式切换错误"]
}


# ------------------- FHA核心数据模型 (来自 fha_core_logic.py, 稍作修改以适应Web应用) -------------------
class FHA_Model:
    """FHA功能的数据模型，负责所有数据操作 (作为单例服务)。"""
    TABLE_COLUMNS = [
        '编号', '一级功能', '二级功能', '三级功能', '功能类型', '飞行阶段',
        '失效状态', '对于飞行器的影响', '对于地面/空域的影响', '对于地面控制组的影响',
        '危害性分类', '理由/备注',
    ]
    ARP4761_CATEGORIES = [
        "", "灾难的 (Catastrophic)", "危险的 (Hazardous)", "严重的 (Major)",
        "轻微的 (Minor)", "无安全影响 (No Safety Effect)"
    ]

    def __init__(self):
        self.dataframe = self.new_blank_dataframe()

    def new_blank_dataframe(self):
        df = pd.DataFrame(columns=self.TABLE_COLUMNS)
        for col in self.TABLE_COLUMNS:
            df[col] = df[col].astype(str)
        return df

    def get_dataframe_as_dict(self):
        return self.dataframe.to_dict('records')

    def new_project(self, skeleton: List[Dict[str, Any]]):
        self.dataframe = self.new_blank_dataframe()
        if skeleton:
            self.add_fha_entries(skeleton)

    def load_dataframe(self, df):
        df_reindexed = df.reindex(columns=self.TABLE_COLUMNS).fillna('')
        self.dataframe = df_reindexed.astype(str)
        self.re_number_ids()

    def add_fha_entries(self, entries_list: List[Dict[str, Any]]):
        if not entries_list:
            return

        new_rows = [{k: entry.get(k, '') for k in self.TABLE_COLUMNS if k != '编号'} for entry in entries_list]
        new_df = pd.DataFrame(new_rows, columns=[col for col in self.TABLE_COLUMNS if col != '编号'])

        self.dataframe = pd.concat([self.dataframe, new_df], ignore_index=True)
        self.re_number_ids()

    def update_fha_entry(self, index: int, entry_data: Dict[str, Any]):
        if index < 0 or index >= len(self.dataframe):
            raise IndexError("Index out of bounds")
        for key, value in entry_data.items():
            if key in self.dataframe.columns:
                self.dataframe.loc[index, key] = value
        self.re_number_ids()

    def update_fha_entries_from_wizard(self, source_index: int, wizard_results: List[Dict[str, Any]]):
        if not wizard_results:
            return

        source_row_data = self.dataframe.loc[source_index].copy()

        df_before = self.dataframe.iloc[:source_index]
        df_after = self.dataframe.iloc[source_index + 1:]

        updated_entries = []
        for result in wizard_results:
            new_entry = source_row_data.copy()
            # 清空旧的分析结果字段
            for key in ['失效状态', '对于飞行器的影响', '对于地面/空域的影响', '对于地面控制组的影响', '危害性分类',
                        '理由/备注']:
                new_entry[key] = ''
            new_entry.update(result)
            updated_entries.append(new_entry)

        df_updated = pd.DataFrame(updated_entries, columns=self.TABLE_COLUMNS)

        self.dataframe = pd.concat([df_before, df_updated, df_after], ignore_index=True)
        self.re_number_ids()

    def delete_rows(self, row_indices: List[int]):
        if not row_indices: return
        self.dataframe.drop(row_indices, inplace=True)
        self.re_number_ids()

    def re_number_ids(self):
        self.dataframe.reset_index(drop=True, inplace=True)
        for i in range(len(self.dataframe)):
            self.dataframe.loc[i, '编号'] = f"FHA-{i + 1:03d}"


# ------------------- FastAPI 应用实例和FHA模型单例 -------------------
app = FastAPI(title="FHA 结构化分析系统 - API")
fha_service = FHA_Model()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------- Pydantic 数据模型 -------------------
class NewProjectSkeleton(BaseModel):
    skeleton: List[Dict[str, Any]]


class WizardResults(BaseModel):
    source_index: int
    results: List[Dict[str, Any]]


class DeleteIndices(BaseModel):
    indices: List[int]


class UpdateEntry(BaseModel):
    index: int
    data: Dict[str, Any]


# ------------------- API Endpoints -------------------
@app.get("/api/config", summary="获取应用配置信息")
def get_app_config():
    return {
        "failure_mode_library": FAILURE_MODE_LIBRARY,
        "arp4761_categories": FHA_Model.ARP4761_CATEGORIES,
        "mission_phases": ["地面检查", "启动", "垂直起飞", "过渡飞行", "巡航", "悬停作业", "返航", "垂直降落", "关机"],
        "function_types": ["电源", "传感器", "执行机构", "数据传输", "飞控算法", "导航", "通信", "其他"]
    }


@app.get("/api/fha-data", summary="获取所有FHA数据")
def get_fha_data():
    return fha_service.get_dataframe_as_dict()


@app.post("/api/new-project", summary="新建FHA项目")
def new_project(payload: NewProjectSkeleton):
    fha_service.new_project(payload.skeleton)
    return {"message": "新项目创建成功", "data": fha_service.get_dataframe_as_dict()}


@app.post("/api/import-excel", summary="从Excel导入数据")
async def import_from_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="文件格式不正确，请上传 .xlsx 或 .xls 文件。")
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl').fillna('').astype(str)
        fha_service.load_dataframe(df)
        return {"message": f"成功从 {file.filename} 加载数据。", "data": fha_service.get_dataframe_as_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件解析失败: {e}")


@app.get("/api/export-excel", summary="导出数据到Excel")
def export_to_excel():
    df = fha_service.dataframe
    if df.empty:
        raise HTTPException(status_code=404, detail="没有可导出的数据。")

    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    headers = {'Content-Disposition': 'attachment; filename="FHA_Report.xlsx"'}
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers=headers)


@app.post("/api/add-row", summary="添加一个空行")
def add_new_row():
    fha_service.add_fha_entries([{}])
    return {"message": "新行已添加", "data": fha_service.get_dataframe_as_dict()}


@app.post("/api/delete-rows", summary="删除指定的行")
def delete_rows(payload: DeleteIndices):
    sorted_indices = sorted(payload.indices, reverse=True)
    fha_service.delete_rows(sorted_indices)
    return {"message": "选中行已删除", "data": fha_service.get_dataframe_as_dict()}


@app.put("/api/update-entry", summary="更新单个条目")
def update_entry(payload: UpdateEntry):
    try:
        fha_service.update_fha_entry(payload.index, payload.data)
        return {"message": "条目已更新", "data": fha_service.get_dataframe_as_dict()}
    except IndexError:
        raise HTTPException(status_code=404, detail="条目未找到")


@app.post("/api/run-wizard", summary="运行引导式分析")
def run_wizard(payload: WizardResults):
    try:
        fha_service.update_fha_entries_from_wizard(payload.source_index, payload.results)
        return {"message": "分析完成，表格已更新。", "data": fha_service.get_dataframe_as_dict()}
    except IndexError:
        raise HTTPException(status_code=404, detail="源条目未找到")


@app.get("/api/dashboard-data", summary="获取仪表盘数据")
def get_dashboard_data():
    df = fha_service.dataframe
    if df.empty:
        return {"kpis": {"total": 0, "catastrophic": 0, "hazardous": 0}, "sunburst_data": {},
                "cross_analysis": {"rows": [], "columns": [], "data": []}, "summary_text": "暂无数据。"}

    df_analyzed = df[df['失效状态'] != ''].copy()

    hazard_counts = df_analyzed['危害性分类'].value_counts()
    kpis = {
        "total": int(len(df_analyzed)),
        "catastrophic": int(hazard_counts.get("灾难的 (Catastrophic)", 0)),
        "hazardous": int(hazard_counts.get("危险的 (Hazardous)", 0))
    }

    df_filtered = df_analyzed[(df_analyzed['一级功能'] != '') & (df_analyzed['危害性分类'] != '') & (
                df_analyzed['危害性分类'] != '无安全影响 (No Safety Effect)')]

    sunburst_data = {"name": "FHA风险", "children": []}
    if not df_filtered.empty:
        color_map = {
            "灾难的 (Catastrophic)": "#D32F2F", "危险的 (Hazardous)": "#FFA000",
            "严重的 (Major)": "#388E3C", "轻微的 (Minor)": "#1976D2",
        }
        func_groups = df_filtered.groupby('一级功能')
        for name, group in func_groups:
            hazard_counts_group = group['危害性分类'].value_counts()
            children = []
            for hazard, count in hazard_counts_group.items():
                children.append({
                    "name": hazard.split(' ')[0],
                    "value": count,
                    "itemStyle": {"color": color_map.get(hazard)}
                })
            sunburst_data["children"].append({"name": name, "children": children})

    cross_tab_data = {"rows": [], "columns": [], "data": []}
    summary_text = ""
    df_cross = df_analyzed[(df_analyzed['一级功能'] != '') & (df_analyzed['危害性分类'] != '')]
    if not df_cross.empty:
        cross_tab = pd.crosstab(df_cross['一级功能'], df_cross['危害性分类'])
        ordered_cols = [col for col in FHA_Model.ARP4761_CATEGORIES if
                        col in cross_tab.columns and col != "" and col != '无安全影响 (No Safety Effect)']
        cross_tab = cross_tab.reindex(columns=ordered_cols, fill_value=0)

        cross_tab_data['rows'] = cross_tab.index.tolist()
        cross_tab_data['columns'] = [col.split(' ')[0] for col in cross_tab.columns]
        cross_tab_data['data'] = cross_tab.values.tolist()

        high_risk_items_count = kpis["catastrophic"] + kpis["hazardous"]
        summary_text += f"当前共识别出 {high_risk_items_count} 项高风险条目（灾难级或危险级）。\n\n"

        if not cross_tab.empty:
            high_risk_cols = [col for col in ["灾难的 (Catastrophic)", "危险的 (Hazardous)"] if
                              col in cross_tab.columns]
            if high_risk_cols:
                cross_tab['high_risk_sum'] = cross_tab[high_risk_cols].sum(axis=1)
                if not cross_tab['high_risk_sum'].empty:
                    top_func = cross_tab['high_risk_sum'].idxmax()
                    top_func_cat_count = int(cross_tab.loc[
                                                 top_func, "灾难的 (Catastrophic)"]) if "灾难的 (Catastrophic)" in cross_tab.columns else 0
                    top_func_haz_count = int(cross_tab.loc[
                                                 top_func, "危险的 (Hazardous)"]) if "危险的 (Hazardous)" in cross_tab.columns else 0
                    summary_text += f"核心关注点：\n风险主要集中在 “{top_func}” 系统中，其中包含 {top_func_cat_count} 个“灾难级”和 {top_func_haz_count} 个“危险级”风险。\n\n"

        summary_text += "行动建议：\n请结合下方交叉分析矩阵，优先审查高风险区域对应的功能模块，并为这些风险制定缓解措施和验证计划。"
    else:
        summary_text = "暂无已完成分析的条目，无法生成摘要。"

    return {"kpis": kpis, "sunburst_data": sunburst_data, "cross_analysis": cross_tab_data,
            "summary_text": summary_text.strip()}


# 用于本地开发启动
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)