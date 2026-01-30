import numpy as np
import pandas as pd
import pingouin as pg
import matplotlib.pyplot as plt

df = pd.read_excel('datasets/valid-student.xlsx')

X1 = 'b09'
X2 = 'b29'
X3 = 'b30'
X4 = 'b32'
X5 = 'b35'
X6 = 'c12'
X7 = 'c25'
Y = 'a17'

hashmap_X1 = {'非常困难': 1, '比较困难': 2, '中等': 3, '比较富裕': 4, '很富裕': 5}
hashmap_X2 = {'一点也不多': 1, '比较少': 2, '不多不少': 3, '比较多': 4, '非常多': 5}
hashmap_X3 = {'没有特别要求': 1, '班上的平均水平': 2, '中上': 3, '班上前五名': 4}
hashmap_X4 = {'毫无压力': 1, '有点压力': 2, '一般': 3, '压力比较大': 4, '压力很大': 5}
hashmap_X5 = {'根本没有信心': 1, '不太有信心': 2, '比较有信心': 3, '很有信心': 4}
hashmap_X6 = {'不好': 1, '中下': 2, '中等': 3, '中上': 4, '很好': 5}
hashmap_X7 = {'根本没有信心': 1, '不太有信心': 2, '比较有信心': 3, '很有信心': 4}
hashmap_Y = {'很不好': 1, '不太好': 2, '一般': 3, '比较好': 4, '很好': 5}

df[X1] = df[X1].map(hashmap_X1)
df[X2] = df[X2].map(hashmap_X2)
df[X3] = df[X3].map(hashmap_X3)
df[X4] = df[X4].map(hashmap_X4)
df[X5] = df[X5].map(hashmap_X5)
df[X6] = df[X6].map(hashmap_X6)
df[X7] = df[X7].map(hashmap_X7)
df[Y] = df[Y].map(hashmap_Y)

dims = [X1, X2, X3, X4, X5, X6, X7, Y]
df_analysis = df[dims].dropna()

stats = pg.pairwise_corr(data = df_analysis, method = 'pearson')
print(stats[['X', 'Y', 'r', 'p-unc', 'CI95%', 'BF10', 'power']].to_latex(float_format='%.3f'))

correlation = df_analysis.corr(method = 'pearson')


def plot_bubble_corr(corr):
    plt.rcParams['font.family'] = 'Times New Roman'

    # 1. 将矩阵“拉平”
    df_corr = corr.stack().reset_index()
    df_corr.columns = ['x', 'y', 'value']
    
    # 2. 映射坐标索引
    x_map = {label: i for i, label in enumerate(corr.columns)}
    y_map = {label: i for i, label in enumerate(corr.index)}
    df_corr['x_num'] = df_corr['x'].map(x_map)
    df_corr['y_num'] = df_corr['y'].map(y_map)

    # 3. --- 核心修改：仅保留右下角 (下三角区域) ---
    # 在 Matplotlib 默认坐标系中（y轴向上），右下角对应 x_num > y_num
    # 如果你希望保留左上角，则使用 x_num < y_num
    df_corr = df_corr[df_corr['x_num'] > df_corr['y_num']]
    # --------------------------------------------

    n = len(corr)
    # plt.figure(figsize=(8, 8))

    # 4. 绘制对角斜线
    plt.plot([-0.5, n - 0.5], [-0.5, n - 0.5], 
             color='gray', linestyle='-', linewidth=1.5, alpha=0.5, zorder=1)

    # 5. 绘制气泡
    scatter = plt.scatter(x=df_corr['x_num'], y=df_corr['y_num'], 
                          s=np.abs(df_corr['value']) * 1000, 
                          c=df_corr['value'], cmap='RdBu_r', 
                          edgecolors='none', vmin=-1, vmax=1, zorder=2)

    plt.xticks(list(x_map.values()), list(x_map.keys()), rotation=0, fontsize=12)
    plt.yticks(list(y_map.values()), list(y_map.keys()), fontsize=12)

    plt.xlim(-0.5, n - 0.5)
    plt.ylim(-0.5, n - 0.5)

    cbar = plt.colorbar(scatter)
    cbar.set_label('Correlation Strength', fontsize=12)
    cbar.ax.tick_params(labelsize=12)
    plt.grid(True, color='gray', linestyle='-.', linewidth=0.5, alpha=0.25)

    plt.title('Lower Triangular Pearson Correlation Coefficient', fontsize=12, pad=0)
    plt.show()


plot_bubble_corr(correlation)