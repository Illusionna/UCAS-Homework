import pandas as pd

df_student = pd.read_excel('datasets/valid-student.xlsx')
df_parent = pd.read_excel('datasets/valid-parent.xlsx')

dim = 'be07'

df = pd.merge(
    df_student[['ids', 'b31']], 
    df_parent[['ids', dim, 'ba18']], 
    on = 'ids'
)

hashmap = {
    '现在就不要念了': 1,
    '初中毕业': 2,
    '中专/技校': 3,
    '职业高中': 4,
    '普通高中': 5,
    '大学专科': 6,
    '大学本科': 7,
    '研究生': 8,
    '博士': 9,
    '无所谓': 10
}

df['b31'] = df['b31'].map(hashmap)
df['ba18'] = df['ba18'].map(hashmap)

for category in df[dim].unique():
    df_category = df[df[dim] == category]
    total = len(df_category)

    print(f'~ & {category}', end = ' & ')

    a = len(df_category[df_category['ba18'] > df_category['b31']])
    b = len(df_category[df_category['ba18'] < df_category['b31']])
    c = len(df_category[df_category['ba18'] == df_category['b31']])

    print(f"{a} & {(100 * a / total):.2f}\\%", end = ' & ')
    print(f"{b} & {(100 * b / total):.2f}\\%", end = ' & ')
    print(f"{c} & {(100 * c / total):.2f}\\% \\\\")