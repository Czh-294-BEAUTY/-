import os
import json
import pandas as pd
from dash import Dash, dcc, html,Input,Output
import plotly.express as px

def is_stock_related(text):
    # 检查文本中是否包含与股票相关的关键词
    keywords = ["上涨", "下跌", "股", "%"]
    return any(keyword in text for keyword in keywords)

def process_files(file_paths):
    stock_related_data = []
    other_data = []

    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:
                    try:
                        # 将每一行转换为字典，假设文本文件中的每一行都是有效的JSON字符串
                        data = json.loads(line)
                        if isinstance(data, dict):
                            if is_stock_related(data.get("text", "")):
                                stock_related_data.append(data)
                            else:
                                other_data.append(data)
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON from line: {line}")
    return stock_related_data, other_data


def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def main():
    initial_file_paths_1 = [
        r"D:\\pythoncode\\initial_data\\stream_01.txt",
        r"D:\\pythoncode\\initial_data\\stream_02.txt",
        r"D:\\pythoncode\\initial_data\\stream_03.txt",
        r"D:\\pythoncode\\initial_data\\stream_04.txt",
        r"D:\\pythoncode\\initial_data\\stream_05.txt"
    ]

    initial_file_paths_2 = [
        r"D:\\pythoncode\\initial_data\\update_01.txt",
        r"D:\\pythoncode\\initial_data\\update_02.txt"
    ]

    # 创建data和.cache文件夹
    os.makedirs(r"D:\\pythoncode\\initial_data\\data", exist_ok=True)
    os.makedirs(r"D:\\pythoncode\\initial_data\\.cache", exist_ok=True)

    # 处理第一个文件组
    stock_data_1, other_data_1 = process_files(initial_file_paths_1)
    save_json(stock_data_1, r"D:\\pythoncode\\initial_data\\data\\2024-12-04.json")

    # 将其他数据保存到.cache文件夹
    save_json(other_data_1, r"D:\\pythoncode\\initial_data\\.cache\\2024-12-04.cache.json")

    # 处理第二个文件组
    stock_data_2, other_data_2 = process_files(initial_file_paths_2)
    save_json(stock_data_2, r"D:\\pythoncode\\initial_data\\data\\2024-12-10.json")

    # 将其他数据保存到.cache文件夹
    save_json(other_data_2, r"D:\\pythoncode\\initial_data\\.cache\\2024-12-10.cache.json")


class DataLoader:
    def __init__(self, data_directory):
        self.data_directory = data_directory

    def load_data(self, filename):
        file_path = os.path.join(self.data_directory, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return pd.DataFrame(data)
                else:
                    raise ValueError("JSON data is not in list format.")
        else:
            raise FileNotFoundError(f"File {filename} not found in {self.data_directory}")

    def filter_by_publish_time(self, df, publish_time):
        return df[df['publishTime'].str.contains(publish_time)]

    def filter_by_match(self, df, match_name):
        return df[df['match'].str.contains(match_name)]

# 创建 Dash 应用实例
app = Dash(__name__)

# 数据加载器的初始化
data_loader = DataLoader(r"D:\\pythoncode\\initial_data\\data")

# 加载数据
df_2024_12_04 = data_loader.load_data("2024-12-04.json")
df_2024_12_10 = data_loader.load_data("2024-12-10.json")

# 合并 DataFrame
combined_df = pd.concat([df_2024_12_04, df_2024_12_10], ignore_index=True)

# Dash 布局
app.layout = html.Div(children=[
    html.H1(children='Stock News Analysis'),

    html.Div(children='''
             Input a stock name or a publish time to filter the data.
         '''),

    dcc.Input(id='stock-name-input', type='text', placeholder='Enter Stock Name'),
    dcc.Input(id='publish-time-input', type='text', placeholder='Enter Publish Time (e.g., 2024-12-04)'),

    html.Button('Submit', id='submit-button', n_clicks=0),

    dcc.Graph(id='filtered-data-graph'),
    html.Div(id='output-message'),
    html.Div(id='details-list')  # 用于显示具体字段的区域
])


# 更新图表和详细信息的回调函数
@app.callback(
    [Output('filtered-data-graph', 'figure'),
     Output('output-message', 'children'),
     Output('details-list', 'children')],  # 新增输出
    Input('submit-button', 'n_clicks'),
    Input('stock-name-input', 'value'),
    Input('publish-time-input', 'value')
)
def update_graph(n_clicks, stock_name, publish_time):
    if n_clicks > 0:
        filtered_df = combined_df

        # 过滤数据
        if stock_name:
            filtered_df = data_loader.filter_by_match(filtered_df, stock_name)
        if publish_time:
            filtered_df = data_loader.filter_by_publish_time(filtered_df, publish_time)

        if filtered_df.empty:
            return px.histogram(), "No results found for the given criteria.", "No details available."

        # 创建图表
        fig = px.histogram(filtered_df, x='publishTime', title='Filtered Publish Time Distribution',
                           labels={'publishTime': 'Publish Time'}, color='match')

        # 获取过滤后的字段并去重
        unique_details = set()
        for _, row in filtered_df.iterrows():
            detail = (f"Website: {row['captureWebsite']}, "
                      f"Text: {row['text']}, "
                      f"Followers: {row['followers']}, "
                      f"Emotion: {row['emotion']}")
            unique_details.add(detail)

        # 创建详细信息列表
        details_display = html.Ul([html.Li(detail) for detail in unique_details])

        return fig, f"Showing results for stock name: {stock_name if stock_name else 'All'} and publish time: {publish_time if publish_time else 'All'}", details_display

    return px.histogram(), "Please enter a stock name or publish time and click Submit.", "No details available."


# 运行 Dash 应用
if __name__ == '__main__':
    app.run_server(debug=True)