import pandas as pd
import pingouin as pg

df = pd.read_excel('datasets/valid-student.xlsx')

X = 'c25'
Y = 'a17'

hashmap = {'根本没有信心': 1, '不太有信心': 2, '比较有信心': 3, '很有信心': 4}
hashmap_health = {'很不好': 1, '不太好': 2, '一般': 3, '比较好': 4, '很好': 5}

df[X] = df[X].map(hashmap)
df[Y] = df[Y].map(hashmap_health)

# valid_df = df.dropna(subset=[X, Y])
valid_df = df
k = valid_df[X].nunique()
N = valid_df[X].count()
df1 = k - 1
df2 = N - k
print(f"Levene 检验自由度: df1={df1}, df2={df2}")

normality = pg.normality(data = df, group = X, dv = Y)
print('\x1b[32mnormality\x1b[0m')
print(normality)

# .to_latex(index=True)
NORMALITY_P_VAL = 1

if NORMALITY_P_VAL >= 0.05:
    homogeneity = pg.homoscedasticity(data = df, group = X, dv = Y)
    print('\x1b[32mhomogeneity\x1b[0m')
    print(homogeneity)
    if homogeneity['pval'].item() >= 0.5:
        anova = pg.anova(data = df, between = X, dv = Y, detailed = True)
        print('\x1b[32mANOVA\x1b[0m')
        print(anova)
        if anova['p-unc'].item() < 0.05:
            tukey = pg.pairwise_tukey(data = df, between = X, dv = Y)
            print('\x1b[32mTukey\x1b[0m')
            print(tukey)
        else:
            print('无显著性.')
    else:
        welch_anova = pg.welch_anova(data = df, between = X, dv = Y)
        print('\x1b[32mWelch ANOVA\x1b[0m')
        print(welch_anova)
        if welch_anova['p-unc'].item() < 0.05:
            gameshowell = pg.pairwise_gameshowell(data = df, between = X, dv = Y)
            print('\x1b[32mGames-Howell\x1b[0m')
            print(gameshowell.to_latex(index=True,float_format='%.3f'))
        else:
            print('无显著性.')
else:
    kruskal = pg.kruskal(data = df, between = X, dv = Y, detailed = True)
    print('\x1b[32mKruskal\x1b[0m')
    print(kruskal)
    if kruskal['p-unc'].item() < 0.05:
        mwu = pg.pairwise_tests(
            data = df,
            between = X,
            dv = Y,
            parametric = False,
            padjust = 'bonferroni'
        )
        print('\x1b[32mMWU\x1b[0m')
        print(mwu)
    else:
        print('无显著性.')