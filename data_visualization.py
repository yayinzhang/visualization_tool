import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from matplotlib import font_manager  # 新增

# 設定字型
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['font.size'] = 12
font_path = "/System/Library/Fonts/STHeiti Light.ttc"
font_prop = font_manager.FontProperties(fname=font_path)

def visualize_from_json(json_str: str, group_filter: list = None, subgroup_filter: list = None, x_filter: list = None, auto_filter: bool = False, auto_x_filter: bool = False, x_top_n: int = None, top_n: int = None):
    # 限制最大畫布像素寬度（避免 Image size too large 錯誤）
    max_pixel_width = 64000  # 2^16
    base_dpi = 100
    max_fig_width = max_pixel_width / base_dpi
    data = json.loads(json_str)
    
    chart_type = data.get("chart_type")
    # st.write(f"🔍 chart_type: {chart_type}")
    x = data.get("x", [])
    y = data.get("y", [])
    group = data.get("group")
    subgroup = data.get("subgroup")
    title = data.get("title", "圖表")
    xlabel = data.get("xlabel", "")
    ylabel = data.get("ylabel", "")

    # x_filter邏輯：支援所有chart_type（pie除外）
    if auto_x_filter and isinstance(x, list) and x_top_n:
        # 根據 y 或 stack_series/group_series 決定排序依據
        if "y" in data and isinstance(data["y"], list):
            sorted_indices = sorted(range(len(x)), key=lambda i: data["y"][i], reverse=True)[:x_top_n]
        elif "stack_series" in data:
            total_x = [0] * len(x)
            for series in data["stack_series"]:
                for i, v in enumerate(series["values"]):
                    total_x[i] += v if v else 0
            sorted_indices = sorted(range(len(x)), key=lambda i: total_x[i], reverse=True)[:x_top_n]
        elif "group_series" in data:
            total_x = [0] * len(x)
            for series in data["group_series"]:
                for i, v in enumerate(series["values"]):
                    total_x[i] += v if v else 0
            sorted_indices = sorted(range(len(x)), key=lambda i: total_x[i], reverse=True)[:x_top_n]
        else:
            sorted_indices = list(range(len(x)))[:x_top_n]

        x_filter = [x[i] for i in sorted_indices]

    # 支援手動 x_filter: 只要有 x_filter, 就篩選(除了 pie)
    if chart_type != "pie" and x_filter:
        # 篩選符合 x_filter 的資料
        if isinstance(x, list):
            x_filtered_indices = [i for i, xi in enumerate(x) if xi in x_filter]
            x = [x[i] for i in x_filtered_indices]
            # 篩選 y
            if "y" in data and isinstance(y, list) and len(y) == len(x_filtered_indices):
                y = [y[i] for i in x_filtered_indices]
            elif "y" in data and isinstance(y, list) and len(y) == len(x_filter):
                # already filtered
                pass
            # 篩選 group_series
            if "group_series" in data:
                group_series = data.get("group_series", [])
                for series in group_series:
                    series["values"] = [series["values"][i] for i in x_filtered_indices]
            # 篩選 stack_series
            if "stack_series" in data:
                stack_series = data.get("stack_series", [])
                for series in stack_series:
                    series["values"] = [series["values"][i] for i in x_filtered_indices]

    # 動態調整figsize（部分圖表會再覆蓋）
    # 計算顯示項目數量 n
    n = len(x) if isinstance(x, list) else 1
    fig_width = min(0.6 * n, 16)
    fig_height = 6
    plt.figure(figsize=(fig_width, fig_height))
    # plt.title(title, fontproperties=font_prop)  # 移除這裡的標題設定
    if chart_type != "pie":
        plt.xlabel(xlabel, fontproperties=font_prop)
        plt.ylabel(ylabel, fontproperties=font_prop)

    if chart_type == "bar":
        if len(x) != len(y):
            st.warning(f"⚠️ 無法顯示圖表《{title}》，因為 x 與 y 長度不一致：x={len(x)}, y={len(y)}")
            return
        df = pd.DataFrame({"x": x, "y": y})
        plt.bar(df["x"], df["y"])
        plt.title(title, fontproperties=font_prop)
        for i, v in enumerate(df["y"]):
            plt.text(i, v, str(v), ha="center", va="bottom", fontproperties=font_prop)
        plt.xticks(rotation=45, ha="right", fontproperties=font_prop)
    elif chart_type == "pie":
        # 合併小於3%的項目為 "Other"
        total = sum(y)
        new_x = []
        new_y = []
        other_total = 0
        for label, value in zip(x, y):
            if total > 0 and value / total < 0.03:
                other_total += value
            else:
                new_x.append(label)
                new_y.append(value)
        if other_total > 0:
            new_x.append("Other")
            new_y.append(other_total)
        x = new_x
        y = new_y
        plt.pie(y, labels=x, autopct="%1.1f%%", textprops={'fontproperties': font_prop})
        plt.title(title, fontproperties=font_prop)
    elif chart_type == "line":
        df = pd.DataFrame({"x": x, "y": y})
        plt.plot(range(len(df)), df["y"], marker="o")
        plt.title(title, fontproperties=font_prop)
        for i, v in enumerate(df["y"]):
            plt.text(i, v, str(v), ha="center", va="bottom", fontproperties=font_prop)
        plt.xticks(range(len(df)), df["x"], rotation=45, ha="right", fontproperties=font_prop)
    elif chart_type == "grouped_bar":
        group_series = data.get("group_series", [])
        
        # 準備新的 DataFrame 資料
        records = []
        for series in group_series:
            label = series.get("label")
            values = series.get("values", [])
            for xi, value in zip(x, values):
                records.append({
                    "x": xi,
                    "group": label,
                    "y": value
                })
        
        df = pd.DataFrame(records)

        # 根據 x_top_n 決定 top 幾
        if not group_filter and auto_filter:
            top_n = top_n if top_n else (x_top_n if x_top_n else 5)
            top_groups = df.groupby("group")["y"].sum().nlargest(top_n).index.tolist()
            df = df[df["group"].isin(top_groups)]
        elif group_filter:
            df = df[df["group"].isin(group_filter)]
        
        grouped = df.groupby("group")
        width = 0.8 / len(grouped)
        # 自動調整畫布大小
        n = len(x) if isinstance(x, list) else 1
        fig_width = min(0.6 * n, 16)
        fig_height = 6
        plt.figure(figsize=(fig_width, fig_height))
        for i, (gname, gdata) in enumerate(grouped):
            plt.bar([xi + i*width for xi in range(len(gdata))], gdata["y"], width=width, label=gname)
            for i2, (xi, val) in enumerate(zip(range(len(gdata)), gdata["y"])):
                plt.text(xi + i*width, val, str(val), ha="center", va="bottom", fontproperties=font_prop)
        plt.title(title, fontproperties=font_prop)
        plt.xticks(range(len(x)), x, rotation=45, ha="right", fontproperties=font_prop)
        plt.legend(prop=font_prop, loc='lower center', bbox_to_anchor=(0.5, -0.4), ncol=5)

    elif chart_type == "stacked_bar":
        # 畫布寬度限制，避免超過最大像素尺寸
        fig_width = min(16, max(6, len(x) * 0.5))
        fig_dpi = 100
        fig_width = min(fig_width, max_fig_width)
        fig_height = 8
        plt.figure(figsize=(fig_width, fig_height), dpi=fig_dpi)  # 自動調整畫布寬度
        df = pd.DataFrame({"x": x})
        bottom = [0] * len(x)
        stack_series = data["stack_series"]

        # 新增排序邏輯
        total_per_x = [0] * len(x)
        for series in stack_series:
            for idx, val in enumerate(series["values"]):
                if val is not None:
                    total_per_x[idx] += val

        # 自動篩選 x 軸 top n
        if (auto_filter or x_top_n) and len(x) > 1:
            n = x_top_n if x_top_n else 10
            top_x = sorted(zip(x, total_per_x), key=lambda item: item[1], reverse=True)[:n]
            top_x_labels = [label for label, _ in top_x]
            x_indices = [x.index(label) for label in top_x_labels]
            x = top_x_labels
            total_per_x = [total_per_x[i] for i in x_indices]
            for series in stack_series:
                series["values"] = [series["values"][i] for i in x_indices]

        if not subgroup_filter and auto_filter:
            top_n = top_n if top_n else (x_top_n if x_top_n else 5)
            top_items = sorted([(s["label"], sum([v if v is not None else 0 for v in s["values"]])) for s in stack_series], key=lambda x: x[1], reverse=True)[:top_n]
            stack_series = [s for s in stack_series if s["label"] in dict(top_items)]
        elif subgroup_filter:
            stack_series = [s for s in stack_series if s["label"] in subgroup_filter]

        for series_idx, series in enumerate(stack_series):
            cleaned_values = [v if v is not None else 0 for v in series["values"]]
            plt.bar(x, cleaned_values, bottom=bottom, label=series["label"])

            for i, (xi, val) in enumerate(zip(x, cleaned_values)):
                if val <= 0:
                    continue
                y_base = bottom[i]
                is_bottom = all(b == 0 for b in bottom)
                is_top = series_idx == len(stack_series) - 1

                if is_bottom:
                    va = "top"
                    y_pos = y_base + val - 3
                elif is_top:
                    va = "bottom"
                    y_pos = y_base + val + 3
                else:
                    va = "top"
                    y_pos = y_base + val - 3

                plt.text(i, y_pos, str(val), ha="center", va=va, fontproperties=font_prop, fontsize=9)

            bottom = [sum(x) for x in zip(bottom, cleaned_values)]
        plt.title(title, fontproperties=font_prop)
        plt.xticks(rotation=30, ha="right", fontproperties=font_prop)
        plt.gca().tick_params(axis='x', pad=10)
        plt.legend(prop=font_prop, loc='lower center', bbox_to_anchor=(0.5, -0.4), ncol=5)
    elif chart_type in ["percentage_stacked_bar_xsubgroup", "percentage_stacked_bar_subgroupx"]:
        # 調整figsize，避免畫布過長
        height = max(6, min(len(x) * 0.4, 20))
        plt.figure(figsize=(min(12, max_fig_width), height))
        stack_series = data.get("stack_series", [])

        # 先篩選 subgroup
        if not subgroup_filter and auto_filter:
            top_n = top_n if top_n else (x_top_n if x_top_n else 5)
            top_items = sorted([(s["label"], sum(s["values"])) for s in stack_series], key=lambda x: x[1], reverse=True)[:top_n]
            stack_series = [s for s in stack_series if s["label"] in dict(top_items)]
        elif subgroup_filter:
            stack_series = [s for s in stack_series if s["label"] in subgroup_filter]

        # 重新計算每個 x 的總和
        total_per_x = [0] * len(x)
        for series in stack_series:
            for idx, val in enumerate(series["values"]):
                if val is not None:
                    total_per_x[idx] += val

        # 支援 x_top_n 過濾
        if auto_x_filter and x_top_n:
            sorted_indices = sorted(range(len(x)), key=lambda i: total_per_x[i], reverse=True)[:x_top_n]
            x = [x[i] for i in sorted_indices]
            total_per_x = [total_per_x[i] for i in sorted_indices]
            for series in stack_series:
                series["values"] = [series["values"][i] for i in sorted_indices]

        # 小於5%的合併成Other
        if stack_series:
            new_stack_series = []
            other_values = [0] * len(x)
            for series in stack_series:
                temp = []
                for idx, val in enumerate(series["values"]):
                    pct = (val / total_per_x[idx] * 100) if total_per_x[idx] else 0
                    temp.append(pct)
                if all(pct < 5 for pct in temp):
                    for idx, val in enumerate(series["values"]):
                        other_values[idx] += val
                else:
                    new_stack_series.append(series)
            if any(v > 0 for v in other_values):
                new_stack_series.append({"label": "Other", "values": other_values})
            stack_series = new_stack_series

        # 依總和降冪排列 x，若為 quarter 格式（如 2023_q1），則按照 x 自然排序（升冪）
        if all(isinstance(xi, str) and "_q" in xi for xi in x):  # quarter 格式
            def sort_key(x_label):
                y, q = x_label.split("_q")
                return int(y), int(q)
            sorted_indices = sorted(range(len(x)), key=lambda i: sort_key(x[i]), reverse=True)
        else:
            sorted_indices = sorted(range(len(x)), key=lambda i: total_per_x[i], reverse=True)
        x = [x[i] for i in sorted_indices]
        total_per_x = [total_per_x[i] for i in sorted_indices]
        for series in stack_series:
            series["values"] = [series["values"][i] for i in sorted_indices]

        # 畫圖
        bottom = [0] * len(x)
        for series in stack_series:
            values = series["values"]
            percent_values = [
                (v / total if total else 0) * 100 for v, total in zip(values, total_per_x)
            ]
            plt.barh(range(len(x)), percent_values, left=bottom, label=series["label"])
            for i, (val, btm) in enumerate(zip(percent_values, bottom)):
                if val >= 5:
                    plt.text(
                        btm + val / 2,
                        i,
                        f"{val:.1f}%",
                        ha="center",
                        va="center",
                        fontproperties=font_prop,
                        fontsize=9,
                        color="white"
                    )
            bottom = [b + p for b, p in zip(bottom, percent_values)]

        plt.title(title, fontproperties=font_prop)
        plt.xlabel("百分比 (%)", fontproperties=font_prop)
        plt.yticks(range(len(x)), x, fontproperties=font_prop)
        plt.legend(prop=font_prop, loc='lower center', bbox_to_anchor=(0.5, -0.4), ncol=5)
    elif chart_type == "group_line":
        group_series = data.get("group_series", [])
        if not group_filter and auto_filter:
            top_n = top_n if top_n else (x_top_n if x_top_n else 5)
            top_items = sorted([(s["label"], sum(s["values"])) for s in group_series], key=lambda x: x[1], reverse=True)[:top_n]
            group_series = [s for s in group_series if s["label"] in dict(top_items)]
        elif group_filter:
            group_series = [s for s in group_series if s["label"] in group_filter]
        # 動態調整畫布大小
        n_groups = len(group_series)
        height = 6 + (n_groups // 5) * 0.6  # 每多 5 條線就增加 1.2 吋高度
        plt.figure(figsize=(min(12, max_fig_width), height))
        for series in group_series:
            plt.plot(x, series["values"], marker="o", label=series["label"])
            for i, v in enumerate(series["values"]):
                plt.annotate(
                    str(v),
                    (i, v),
                    textcoords="offset points",
                    xytext=(5, 5),
                    ha="left",
                    va="bottom",
                    fontproperties=font_prop,
                    fontsize=9
                )
        
        plt.title(title, fontproperties=font_prop)
        plt.xticks(rotation=45, ha="right", fontproperties=font_prop)
        plt.legend(prop=font_prop, loc='lower center', bbox_to_anchor=(0.5, -0.4), ncol=5)
    elif chart_type == "multiple_pie":
        stack_series = data.get("stack_series", [])
        if not stack_series:
            st.warning("⚠️ 沒有資料可顯示")
            return

        n = len(x)
        ncols = 2
        nrows = (n + ncols - 1) // ncols
        # 避免過大畫布
        max_width = 16
        max_height = 16
        fig_width = min(6 * ncols, max_width)
        fig_height = min(4.5 * nrows, max_height)
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(fig_width, fig_height))
        axes = axes.flatten()

        # 整理每個品牌的數據
        brand_to_values = {brand: [] for brand in x}
        for series in stack_series:
            label = series.get("label")
            for idx, brand in enumerate(x):
                brand_to_values[brand].append((label, series["values"][idx]))

        for ax, brand in zip(axes, x):
            label_values = brand_to_values[brand]
            total = sum(value for _, value in label_values)
            new_labels = []
            new_values = []
            other_total = 0
            for label, value in label_values:
                if total > 0 and value / total < 0.05:
                    other_total += value
                else:
                    new_labels.append(label)
                    new_values.append(value)
            if other_total > 0:
                new_labels.append("Other")
                new_values.append(other_total)
            if sum(new_values) == 0:
                ax.axis('off')
                continue
            wedges, texts, autotexts = ax.pie(
                new_values,
                labels=new_labels,
                autopct="%1.1f%%",
                startangle=90,
                counterclock=False,
                textprops={'fontproperties': font_prop}
            )
            ax.set_title(brand, fontproperties=font_prop, fontsize=14)

        for i in range(len(x), len(axes)):
            axes[i].axis("off")

        plt.suptitle(title, fontproperties=font_prop, fontsize=16)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        # 移除圖例，避免圖例在圖下方占據太多空間
    else:
        st.warning(f"⚠️ 不支援的圖表類型：{chart_type}")

    plt.tight_layout()
    st.pyplot(plt)

# 使用方式（貼上 JSON 字串）
# visualize_from_json(json.dumps({
#     "chart_type": "bar",
#     "title": "範例長條圖",
#     "x": ["A", "B", "C"],
#     "y": [10, 20, 15],
#     "xlabel": "分類",
#     "ylabel": "數量"
# }))


def main(auto_x_filter: bool = False):
    import os

    # 新增：讓使用者輸入 x 軸 Top N 數量
    x_top_n = st.number_input("輸入要顯示的 x 軸 Top N 數量（可選）", min_value=1, value=10)
    auto_x_filter_enabled = x_top_n is not None and x_top_n > 0

    json_path = "test.json"  # 或 "./data/test.json" 根據實際路徑改
    if not os.path.exists(json_path):
        st.warning(f"❌ 找不到檔案: {json_path}")
    else:
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # 支援新格式：從 "output" 讀資料，若沒有則 fallback 到 "data"
        charts = json_data.get("output")
        if not charts:
            charts = json_data.get("data")
        if not charts:
            charts = [json_data]
        # st.write("📁 讀到的欄位：", list(json_data.keys()))

        for chart in charts:
            try:
                # st.write(f"📊 正在顯示圖表：{chart.get('title', '未命名圖表')}")
                visualize_from_json(
                    json.dumps(chart),
                    auto_filter=True,
                    auto_x_filter=True,
                    x_top_n=x_top_n,
                    top_n=x_top_n
                )
            except Exception as e:
                st.error(f"⚠️ 圖表《{chart.get('title', '未命名圖表')}》顯示失敗：{e}")