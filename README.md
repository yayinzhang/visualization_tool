# Dify Chart Tool

這是一個用於將資料視覺化並輸出 PDF 圖文報告的工具，適用於自動化報告生成的應用場景，例如紡織業趨勢分析。

## 🧰 功能特色

* 支援多種圖表類型的產生（長條圖、堆疊圖、圓餅圖等）
* 結合 LLM 分析輸出文字（`llm_output`）
* 自動合併摘要與圖文分析，匯出為 PDF
* Streamlit 前端視覺化展示

## 🗂 專案結構

```
.
├── chart_tool_app.py         # 主程式，可用於 PDF 產生
├── run_streamlit.py          # Streamlit 前端介面
├── data_visualization.py     # 視覺化工具模組
├── test.json                 # 測試用輸入資料（含 llm_output）
├── import json.py            # JSON 格式處理
└── README.md                 # 專案說明文件
```

## 🚀 使用方法

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

如果沒有 `requirements.txt`，可以手動安裝：

```bash
pip install matplotlib reportlab streamlit
```

### 2. 執行 PDF 輸出

```bash
python chart_tool_app.py
```

### 3. 啟動前端介面（可視化）

```bash
streamlit run run_streamlit.py
```

## 📁 輸入檔格式（test.json）

JSON 結構需包含：

```json
{
  "summary": "摘要文字",
  "output": [
    {
      "output": { "chart_type": ..., ... },
      "llm_output": "這張圖的分析解譯..."
    },
    ...
  ]
}
```


## 🔧 TODO

* [ ] 支援上傳自訂 JSON
* [ ] 改善圖表標題樣式與配色
* [ ] 匯出 PDF 或 PowerPoint 格式

---

Created by Ya-Yin
