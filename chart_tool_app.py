import streamlit as st # type: ignore
import json
from data_visualization import visualize_from_json  # 你剛才寫好的函式

st.title("📊 圖表小工具 - Chart Viewer")

uploaded_file = st.file_uploader("上傳 JSON 檔", type="json")

# 只有在有上傳檔案時才顯示相關設定與圖表
if uploaded_file:
    json_data = json.load(uploaded_file)
    summary_text = json_data.get("summary")
    if summary_text:
        st.header("📌 總結 Summary")
        st.markdown(summary_text)
        st.markdown("---")
    output_data = json_data.get("output")
    charts = [output_data] if isinstance(output_data, dict) else output_data

    for i, chart_item in enumerate(charts):
        try:
            chart = chart_item.get("output", chart_item)
            llm_output = chart_item.get("llm_output", None)
            if isinstance(chart, str):
                chart = json.loads(chart)
            chart_type = chart.get("chart_type")
            if chart_type not in ["bar", "pie", "line", "stacked_bar", "percentage_stacked_bar_xsubgroup", "percentage_stacked_bar_subgroupx", "grouped_bar", "group_line", "multiple_pie"]:
                st.warning(f"⚠️ 不支援的圖表類型：{chart_type}")
                continue

            # 收集 group/subgroup/x for this chart
            all_groups = set()
            all_subgroups = set()
            all_x = set()

            if chart_type not in ["pie"]:  # pie 不用 x
                x_data = chart.get("x")
                if isinstance(x_data, list):
                    all_x.update(x_data)

            if chart_type in ["grouped_bar", "group_line"]:
                for series in chart.get("group_series", []):
                    all_groups.add(series.get("label"))
            if chart_type in ["stacked_bar", "percentage_stacked_bar_xsubgroup", "multiple_pie"]:
                for series in chart.get("stack_series", []):
                    all_subgroups.add(series.get("label"))
                x_data = chart.get("x")
                if isinstance(x_data, list):
                    all_x.update(x_data)

            # 動態顯示篩選器元件
            x_filter = []
            group_filter = []
            subgroup_filter = []

            auto = st.checkbox(f"啟用 group/subgroup 自動篩選 Top N ({chart.get('title', '未命名圖表')})", key=f"chart_{i}_auto")
            top_n = st.number_input(f"顯示前 N 個 group/subgroup ({chart.get('title', '未命名圖表')})", min_value=1, max_value=100, value=5, step=1, key=f"chart_{i}_topn") if auto else None
            auto_x_top = st.checkbox(f"啟用 x 軸 Top N 篩選 ({chart.get('title', '未命名圖表')})", key=f"chart_{i}_auto_x_top")
            x_top_n = st.number_input(f"顯示前 N 個 x 軸分類 ({chart.get('title', '未命名圖表')})", min_value=1, max_value=100, value=10, step=1, key=f"chart_{i}_x_topn") if auto_x_top else None
            use_manual = st.checkbox(f"手動選擇分類 ({chart.get('title', '未命名圖表')})", key=f"chart_{i}_use_manual")

            if use_manual:
                if all_x:
                    x_filter = st.multiselect(f"手動選擇 x 軸分類 ({chart.get('title', '未命名圖表')})", sorted(all_x), key=f"chart_{i}_x_filter")
                if all_groups:
                    group_filter = st.multiselect(f"手動選擇 group 類別 ({chart.get('title', '未命名圖表')})", sorted(all_groups), key=f"chart_{i}_group_filter")
                if all_subgroups:
                    subgroup_filter = st.multiselect(f"手動選擇 subgroup 類別 ({chart.get('title', '未命名圖表')})", sorted(all_subgroups), key=f"chart_{i}_subgroup_filter")

            # 如果資料過大，進行裁切以避免產生過大圖片
            max_data_length = 1000
            if len(chart.get("x", [])) > max_data_length:
                st.warning(f"⚠️ 資料筆數過多（{len(chart['x'])} 筆），僅顯示前 {max_data_length} 筆資料以避免圖片過大錯誤")
                chart["x"] = chart["x"][:max_data_length]
                if "y" in chart and isinstance(chart["y"], list):
                    chart["y"] = chart["y"][:max_data_length]
                if "group_series" in chart:
                    for series in chart["group_series"]:
                        if "data" in series and isinstance(series["data"], list):
                            series["data"] = series["data"][:max_data_length]
                if "stack_series" in chart:
                    for series in chart["stack_series"]:
                        if "data" in series and isinstance(series["data"], list):
                            series["data"] = series["data"][:max_data_length]

            st.subheader(chart.get("title", "未命名圖表"))
            visualize_from_json(
                json.dumps(chart),
                group_filter=group_filter or None,
                subgroup_filter=subgroup_filter or None,
                x_filter=x_filter or None,
                auto_filter=auto,
                top_n=top_n,
                auto_x_filter=auto_x_top,
                x_top_n=x_top_n
            )



            # 顯示文字摘要
            if llm_output:
                st.info(f"文字摘要：\n\n{llm_output}")

        except Exception as e:
            st.error(f"⚠️ 無法顯示圖表：{e}")