import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

df = pd.read_excel('datasets/valid-student.xlsx')
dfp = pd.read_excel('datasets/valid-parent.xlsx')

# X1 = 'b09'
X2 = 'b29'
X3 = 'b30'
X4 = 'b32'
X5 = 'b35'
X6 = 'c12'
X7 = 'c25'

C1 = 'a01'
C2 = 'b01'
C3 = 'b11'
C4 = 'ba02'
C5 = 'be19'
C6 = 'be20'

Y = 'a17'

hashmap_C1 = {'女': 0, '男': 1}
hashmap_C2 = {'不是': 0, '是': 1}
hashmap_C3 = {'没有': 0, '有': 1}
hashmap_C4 = {'没有': 0, '有': 1}
hashmap_C5 = {'非常困难': 0, '比较困难': 1, '中等': 2, '比较富裕': 3, '很富裕': 4}
hashmap_C6 = {'否': 0, '是': 1}

hashmap_X1 = {'非常困难': 1, '比较困难': 2, '中等': 3, '比较富裕': 4, '很富裕': 5}
hashmap_X2 = {'一点也不多': 1, '比较少': 2, '不多不少': 3, '比较多': 4, '非常多': 5}
hashmap_X3 = {'没有特别要求': 1, '班上的平均水平': 2, '中上': 3, '班上前五名': 4}
hashmap_X4 = {'毫无压力': 1, '有点压力': 2, '一般': 3, '压力比较大': 4, '压力很大': 5}
hashmap_X5 = {'根本没有信心': 1, '不太有信心': 2, '比较有信心': 3, '很有信心': 4}
hashmap_X6 = {'不好': 1, '中下': 2, '中等': 3, '中上': 4, '很好': 5}
hashmap_X7 = {'根本没有信心': 1, '不太有信心': 2, '比较有信心': 3, '很有信心': 4}

hashmap_Y = {'很不好': 1, '不太好': 2, '一般': 3, '比较好': 4, '很好': 5}

df[C1] = df[C1].map(hashmap_C1)
df[C2] = df[C2].map(hashmap_C2)
df[C3] = df[C3].map(hashmap_C3)
dfp[C4] = dfp[C4].map(hashmap_C4)
dfp[C5] = dfp[C5].map(hashmap_C5)
dfp[C6] = dfp[C6].map(hashmap_C6)

# df[X1] = df[X1].map(hashmap_X1)
df[X2] = df[X2].map(hashmap_X2)
df[X3] = df[X3].map(hashmap_X3)
df[X4] = df[X4].map(hashmap_X4)
df[X5] = df[X5].map(hashmap_X5)
df[X6] = df[X6].map(hashmap_X6)
df[X7] = df[X7].map(hashmap_X7)

df[Y] = df[Y].map(hashmap_Y)

dims = [Y, C1, C2, C3, X2, X3, X4, X5, X6, X7]
dimsp = [C4, C5, C6]

df_analysis = pd.concat([df[dims].dropna(), dfp[dimsp].dropna()], axis = 1)


baseline = f'{Y} ~ {C1} + {C2} + {C3} + {C4} + {C5} + {C6}'
formula_m1 = f'{baseline} + {X4} + {X6} + {X7}'
formula_m2 = f'{baseline} + {X2} + {X3} + {X5}'

res1 = smf.ols(baseline, data = df_analysis).fit()
res2 = smf.ols(formula_m2, data = df_analysis).fit()

# print(res1.summary())
print(res2.summary())

r2_m1 = res1.rsquared
r2_m2 = res2.rsquared
delta_r2 = r2_m2 - r2_m1

print('\x1b[32m')
print(f'baseline R2 = {r2_m1:.5f}')
print(f'full model R2 = {r2_m2:.5f}')
print(f'Delta R2 = {delta_r2:.5f}')
print('\x1b[0m')



rmse = np.sqrt(res1.mse_resid)

cols = df_analysis[[C1, C2, C3, C4, C5, C6, X2, X3, X5]]
vif = pd.Series(
    data = [variance_inflation_factor(cols.values, i) for i in range(cols.shape[1])],
    index = cols.columns
)
print(f"RMSE: {rmse}")
print("VIF Values:\n", vif)