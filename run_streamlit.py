import os

# 切換到目前目錄
os.chdir(os.path.dirname(__file__))

# 執行 Streamlit 指令
os.system("streamlit run chart_tool_app.py")