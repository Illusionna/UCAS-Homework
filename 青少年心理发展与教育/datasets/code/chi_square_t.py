import numpy as np
import scipy.stats
import pandas as pd

# df = pd.read_excel('datasets/valid-student.xlsx')
# df = df['a17']
# hashmap_health = {'很不好': 1, '不太好': 2, '一般': 3, '比较好': 4, '很好': 5}
# df = df.map(hashmap_health)
# df.to_excel('xxxx.xlsx', index=0)

dim = 'a01'

df = pd.read_excel('datasets/valid-student.xlsx')
df = pd.concat([df[dim], df['a17']], axis = 1)

hashmap_category = {'女': 0, '男': 1}
hashmap_health = {'很不好': 1, '不太好': 2, '一般': 3, '比较好': 4, '很好': 5}

df[dim] = df[dim].map(hashmap_category)
df['a17'] = df['a17'].map(hashmap_health)

category_a = df[df[dim] == 0]['a17']
category_b = df[df[dim] == 1]['a17']

t, p = scipy.stats.ttest_ind(a = category_a, b = category_b, nan_policy = 'omit')

hashmap_reverse = {v: k for k, v in hashmap_category.items()}

print('分组\t\t平均值 ± 标准差')
for idx, (label, score) in enumerate([(hashmap_reverse[0], category_a), (hashmap_reverse[1], category_b)]):
    print(f"{idx}: {label} = {len(score)}\t{score.mean():.3f} ± {score.std():.3f}")
print('-' * 32)
print(f"t = {t:.3f} | df = {len(category_a) + len(category_b) - 2} | p = {p:.3f}")

def parameters(a: pd.DataFrame, b: pd.DataFrame, alpha: float = 0.05) -> None:
    n1 = len(a)
    n2 = len(b)
    diff = sum(a) / n1 - sum(b) / n2
    degree_freedom = n1 - 1 + n2 - 1
    s1 = np.var(a, ddof = 1)
    s2 = np.var(b, ddof = 1)
    pooled_std = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / degree_freedom)
    pooled_var = pooled_std ** 2
    SE_diff = pooled_std * np.sqrt(1 / n1 + 1 / n2)
    t_critical = scipy.stats.t.ppf(1 - alpha / 2, degree_freedom)
    print(f"分析项 = a17 | 平均值差值 = {diff:.3f} | {100 * (1 - alpha)}% CI = {(diff - t_critical * SE_diff):.3f} ~ {(diff + t_critical * SE_diff):.3f} | S^2 pooled = {pooled_var:.3f} | Cohen's d = {((np.mean(a) - np.mean(b)) / pooled_std):.3f}")

parameters(category_a, category_b)