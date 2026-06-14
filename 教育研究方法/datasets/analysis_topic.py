# -*- coding: utf-8 -*-
"""选题1 第五版出图：全图宋体(中文)+Times New Roman(西文/数字)
图：玫瑰图 / 气泡相关矩阵 / 云雨图 / 森林图 / 分位数热力图 / 置信带交互图
新增：Bootstrap 系数抽样分布脊线图 / 性别时间画像雷达图
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from scipy.stats import gaussian_kde

# 注册从 Songti.ttc 抽取的宋体 ttf（matplotlib 逐字形回退不支持 .ttc）
from matplotlib import font_manager as _fm
for _f in ('fonts/Songti_SC_Regular.ttf', 'fonts/Songti_SC_Bold.ttf'):
    _fm.fontManager.addfont(_f)
plt.rcParams.update({
    'font.family': ['Times New Roman', 'Songti SC'],  # 显式列表→逐字形回退：西文/数字 Times，中文宋体
    'mathtext.fontset': 'stix',                        # 数学符号 Times 风格
    'axes.unicode_minus': False,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.edgecolor': '#8a9aa0', 'axes.linewidth': 0.8,
    'xtick.color': '#506464', 'ytick.color': '#506464',
    'axes.labelcolor': '#2b3a42', 'text.color': '#2b3a42',
    'font.size': 10.5,
})
M = dict(blue='#466EFF', grey='#506464', purple='#8C6EB4', cyan='#6EAABE',
         red='#DC8282', orange='#FAD2A0', lightcyan='#D1EEEE')
DIVG = LinearSegmentedColormap.from_list('morandi', ['#6EAABE', '#FFFFFF', '#DC8282'])

HOURS = {'TT3G18A': '个人备课', 'TT3G18C': '批改作业', 'TT3G18B': '团队协作与教研',
         'TT3G18G': '专业发展活动', 'TT3G18D': '学生辅导咨询', 'TT3G18E': '参与学校管理',
         'TT3G18F': '一般行政事务', 'TT3G18H': '家长沟通', 'TT3G18I': '课外活动'}
CAT = {'TT3G18A': 'teach', 'TT3G18C': 'teach', 'TT3G18B': 'prof', 'TT3G18G': 'prof',
       'TT3G18D': 'prof', 'TT3G18E': 'nonteach', 'TT3G18F': 'nonteach',
       'TT3G18H': 'nonteach', 'TT3G18I': 'nonteach'}
SHADE = {'TT3G18A': '#3E63E0', 'TT3G18C': '#7A95FF', 'TT3G18D': '#5E9CB2',
         'TT3G18B': '#83B7C9', 'TT3G18G': '#A9CFDC', 'TT3G18E': '#D67676',
         'TT3G18F': '#E09595', 'TT3G18H': '#EAB5B5', 'TT3G18I': '#F2D2D2'}
CAT_COLOR = {'teach': M['blue'], 'prof': M['cyan'], 'nonteach': M['red']}
RES = {'T3STUD': '师生关系', 'T3SELF': '自我效能感', 'T3STAKE': '参与学校决策', 'T3EXCH': '同事交流合作'}

df = pd.read_csv('datasets/code/TALIS-2018-Teacher-Shanghai.csv', low_memory=False)
d = df[['IDSCHOOL', 'TT3G01', 'TT3G03', 'TT3G11B', 'T3WLOAD', 'T3WELS', 'TCHWGT']
       + list(HOURS) + list(RES)].copy()
d['female'] = (d['TT3G01'] == 1).astype(float)
d['master'] = (d['TT3G03'] >= 6).astype(float)
d['exper'] = d['TT3G11B']
for c in HOURS:
    lo, hi = d[c].quantile([0.01, 0.99])
    d[c] = d[c].clip(lo, hi)
d = d.dropna()
w = d['TCHWGT']
print('N =', len(d))

def wm(x, ww=None): return np.average(x, weights=w if ww is None else ww)
def zs(s): return (s - s.mean()) / s.std()

Z = pd.DataFrame({'female': d['female'], 'master': d['master'], 'exper': zs(d['exper'])})
for c in list(HOURS) + list(RES):
    Z[c] = zs(d[c])
CTRL = ['female', 'master', 'exper']
y = zs(d['T3WLOAD'])
M2 = sm.WLS(y, sm.add_constant(Z[CTRL + list(HOURS)]), weights=w).fit(cov_type='HC1')
M3 = sm.WLS(y, sm.add_constant(Z[CTRL + list(HOURS) + list(RES)]), weights=w).fit(cov_type='HC1')
rng = np.random.default_rng(42)

# ============ 玫瑰图 ============
import math
items = sorted(HOURS, key=lambda c: -wm(d[c]))
vals = np.array([wm(d[c]) for c in items])
theta = np.linspace(0.0, 2 * np.pi, len(items), endpoint=False) + np.pi / 2
width = 2 * np.pi / len(items) * 0.92
fig = plt.figure(figsize=(7.6, 7.2))
ax = fig.add_subplot(111, projection='polar')
ax.set_theta_direction(-1)
ax.bar(theta, np.sqrt(vals), width=width, bottom=0.55,
       color=[SHADE[c] for c in items], edgecolor='white', linewidth=2, zorder=3)
ax.set_xticks([]); ax.set_yticks([])
ax.spines['polar'].set_visible(False)
for g in [np.sqrt(v) + 0.55 for v in (2, 4, 8)]:
    ax.plot(np.linspace(0, 2 * np.pi, 200), [g] * 200, color='#c8d4d6', lw=0.6, ls=(0, (2, 3)), zorder=1)
t_tick = theta[-1] + width / 2 + 0.10      # 半径刻度放在最短花瓣旁的空隙
for v, lab in [(2, '2h'), (4, '4h'), (8, '8h')]:
    ax.text(t_tick, np.sqrt(v) + 0.55, lab, fontsize=7.5,
            color='#9fb0b5', ha='center', va='center', zorder=6)
ring = np.sqrt(vals.max()) + 0.55          # 统一外环：标签整齐排列
ax.plot(np.linspace(0, 2 * np.pi, 240), [0.55] * 240, color='white', lw=2.2, zorder=5)
for t, v, c in zip(theta, vals, items):
    vr = math.floor(v * 10 + 0.5) / 10
    x = np.cos(np.pi / 2 - t)              # theta_direction=-1 下的屏幕横坐标方向
    ha = 'center' if abs(x) < 0.35 else ('left' if x > 0 else 'right')
    vcol = '#b06a6a' if c in ('TT3G18H', 'TT3G18I', 'TT3G18F') else SHADE[c]
    ax.text(t, ring + 0.30, f'{HOURS[c]}\n{vr:.1f} h', fontsize=9.6, ha=ha, va='center',
            color='#2b3a42', linespacing=1.45, zorder=6)
    ax.plot([t, t], [np.sqrt(v) + 0.62, ring + 0.16], color='#c8d4d6', lw=0.55, zorder=2)
ax.text(0, 0, '38.1 h\n课外任务/周', fontsize=11.5, ha='center', va='center',
        color='#2b3a42', fontweight='bold', linespacing=1.5)
ax.set_rmax(ring + 0.78)
handles = [plt.Rectangle((0, 0), 1, 1, fc=CAT_COLOR[k], alpha=0.85) for k in ['teach', 'prof', 'nonteach']]
ax.legend(handles, ['教学性 16.1h', '专业/育人 12.2h', '非教学 9.8h'],
          loc='lower left', bbox_to_anchor=(-0.12, -0.06), fontsize=9, frameon=False)
plt.tight_layout(); plt.savefig('figv6_rose.pdf', bbox_inches='tight'); plt.close()


# ============ 气泡相关矩阵 ============
corr_vars = ['T3WLOAD', 'T3WELS'] + list(HOURS) + list(RES)
cd = d[corr_vars].rename(columns={**HOURS, **RES, 'T3WLOAD': '工作负荷压力', 'T3WELS': '职业幸福与压力'})
cm = cd.corr()
n = len(cm)
fig, ax = plt.subplots(figsize=(8.8, 7.6))
for i in range(n):
    for j in range(i):
        r = cm.iloc[i, j]
        ax.scatter(j, i, s=2400 * abs(r) + 12, c=[r], cmap=DIVG, vmin=-0.6, vmax=0.6,
                   edgecolors='#b9c8cb', linewidths=0.5, zorder=3)
        if abs(r) >= 0.18:
            ax.text(j, i, f'{r:.2f}'.replace('0.', '.'), fontsize=7, ha='center', va='center',
                    zorder=4, color='white' if abs(r) > 0.42 else '#506464')
ax.set_xticks(range(n)); ax.set_yticks(range(n))
ax.set_xticklabels(cm.columns, rotation=45, ha='right', fontsize=8.8)
ax.set_yticklabels(cm.columns, fontsize=8.8)
ax.set_xlim(-0.6, n - 0.5); ax.set_ylim(n - 0.5, -0.6)
ax.set_aspect('equal')
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(length=0)
ax.grid(color='#eef3f3', lw=0.7, zorder=0)
sm_ = plt.cm.ScalarMappable(cmap=DIVG, norm=plt.Normalize(-0.6, 0.6))
cb = fig.colorbar(sm_, ax=ax, shrink=0.7, pad=0.02)
cb.set_label('Pearson 相关系数 $r$', fontsize=9); cb.outline.set_visible(False)
plt.tight_layout(); plt.savefig('figv6_corrbubble.pdf', bbox_inches='tight'); plt.close()

# ============ 云雨图 ============
q = d['TT3G18C'].quantile([0.25, 0.5, 0.75]).values
grp = np.digitize(d['TT3G18C'], q)
glabels = [f'Q1 ≤{q[0]:.0f}h', f'Q2 {q[0]:.0f}–{q[1]:.0f}h', f'Q3 {q[1]:.0f}–{q[2]:.0f}h', f'Q4 >{q[2]:.0f}h']
gcolors = ['#83B7C9', '#A9B8D8', '#C99AAB', '#DC8282']
fig, ax = plt.subplots(figsize=(8.2, 5.0))
for gi in range(4):
    yy = d.loc[grp == gi, 'T3WLOAD'].values
    ww = w[grp == gi].values
    base = 3 - gi
    kde = gaussian_kde(yy, weights=ww)
    xs = np.linspace(6, 15, 240)
    dens = kde(xs); dens = dens / dens.max() * 0.42
    ax.fill_between(xs, base + 0.06, base + 0.06 + dens, color=gcolors[gi], alpha=0.75, lw=0, zorder=3)
    ax.plot(xs, base + 0.06 + dens, color='white', lw=0.8, zorder=4)
    sel = rng.choice(len(yy), min(260, len(yy)), replace=False)
    ax.scatter(yy[sel] + rng.normal(0, 0.05, len(sel)), base - 0.16 + rng.uniform(-0.1, 0.1, len(sel)),
               s=5, color=gcolors[gi], alpha=0.35, lw=0, zorder=2)
    q1, med, q3 = np.percentile(yy, [25, 50, 75])
    ax.plot([q1, q3], [base, base], color='#2b3a42', lw=2.6, solid_capstyle='round', zorder=5)
    ax.plot(med, base, 'o', mfc='white', mec='#2b3a42', ms=5.5, mew=1.4, zorder=6)
    mu = np.average(yy, weights=ww)
    ax.plot(mu, base, 'D', color='#2b3a42', ms=4, zorder=6)
    ax.text(15.05, base + 0.18, f'加权均值 {mu:.2f}', fontsize=8.6, color=gcolors[gi],
            fontweight='bold', va='center')
ax.set_yticks([3, 2, 1, 0]); ax.set_yticklabels(glabels, fontsize=9.5)
ax.set_xlabel('工作负荷压力指数 T3WLOAD')
ax.set_ylabel('每周批改作业时数（四分位组）')
ax.set_xlim(6, 16.6); ax.set_ylim(-0.65, 3.75)
ax.grid(axis='x', alpha=0.3, ls=':'); ax.set_axisbelow(True)
leg = [Line2D([], [], marker='o', mfc='white', mec='#2b3a42', ls='', label='中位数'),
       Line2D([], [], marker='D', color='#2b3a42', ls='', ms=4, label='加权均值'),
       Line2D([], [], color='#2b3a42', lw=2.6, label='四分位距')]
ax.legend(handles=leg, fontsize=8.4, loc='upper left', frameon=False)
plt.tight_layout(); plt.savefig('figv6_raincloud.pdf'); plt.close()

# ============ 森林图 ============
fig, ax = plt.subplots(figsize=(7.6, 4.9))
order = list(HOURS)
ypos = np.arange(len(order))[::-1]
ax.axvline(0, color=M['grey'], lw=1.0, ls=(0, (4, 3)), alpha=0.8)
for i, c in enumerate(order):
    ax.axhspan(ypos[i] - 0.5, ypos[i] + 0.5, color='#f4f7f7' if i % 2 else 'white', zorder=0)
for off, mdl, mk, alpha, lw in [(0.18, M2, 'o', 0.40, 1.2), (-0.18, M3, 's', 1.0, 1.6)]:
    bs = mdl.params[order]; ci = mdl.conf_int().loc[order]
    for i, c in enumerate(order):
        ax.errorbar(bs[c], ypos[i] + off,
                    xerr=[[bs[c] - ci.loc[c, 0]], [ci.loc[c, 1] - bs[c]]],
                    fmt=mk, color=CAT_COLOR[CAT[c]], alpha=alpha, ms=6, capsize=2.8, lw=lw, zorder=3)
b = M3.params['TT3G18C']
ax.annotate(f'β={b:.3f}***', xy=(b, ypos[1] - 0.18), xytext=(b - 0.012, ypos[1] - 0.95),
            fontsize=9, color=M['blue'], fontweight='bold', ha='center')
ax.set_yticks(ypos); ax.set_yticklabels(HOURS.values(), fontsize=10)
ax.set_xlabel('标准化回归系数 β（因变量：工作负荷压力）')
handles = [Line2D([], [], marker='o', ls='', color=M['grey'], alpha=0.4, label='M2：仅工作要求'),
           Line2D([], [], marker='s', ls='', color=M['grey'], label='M3：要求＋资源'),
           Line2D([], [], marker='s', ls='', color=M['blue'], label='教学性'),
           Line2D([], [], marker='s', ls='', color=M['cyan'], label='专业/育人性'),
           Line2D([], [], marker='s', ls='', color=M['red'], label='非教学性')]
ax.legend(handles=handles, fontsize=8.4, loc='lower right', framealpha=0.9, ncol=2)
ax.grid(axis='x', alpha=0.3, ls=':'); ax.set_axisbelow(True)
plt.tight_layout(); plt.savefig('figv6_forest.pdf'); plt.close()

# ============ 分位数热力图 ============
taus = np.round(np.arange(0.1, 0.91, 0.1), 1)
Xq = sm.add_constant(Z[CTRL + list(HOURS)])
B = np.zeros((len(HOURS), len(taus))); P = np.ones_like(B)
for j, t in enumerate(taus):
    r = sm.QuantReg(y, Xq).fit(q=t)
    for i, c in enumerate(HOURS):
        B[i, j] = r.params[c]; P[i, j] = r.pvalues[c]
fig, ax = plt.subplots(figsize=(8.8, 4.6))
im = ax.imshow(B, cmap=DIVG, vmin=-0.36, vmax=0.36, aspect='auto')
for j in range(B.shape[1] + 1):                       # 白色细网格分隔单元格
    ax.axvline(j - 0.5, color='white', lw=1.4)
for i in range(B.shape[0] + 1):
    ax.axhline(i - 0.5, color='white', lw=1.4)
for i in range(B.shape[0]):
    for j in range(B.shape[1]):
        star = '***' if P[i, j] < 0.001 else '**' if P[i, j] < 0.01 else '*' if P[i, j] < 0.05 else ''
        col = 'white' if abs(B[i, j]) > 0.22 else '#506464'
        ax.text(j, i, f'{B[i, j]:.2f}{star}', ha='center', va='center', fontsize=7.3, color=col)
for i, c in enumerate(HOURS):                          # 左侧任务类别色条
    ax.add_patch(plt.Rectangle((-0.78, i - 0.36), 0.16, 0.72, clip_on=False,
                               facecolor=CAT_COLOR[CAT[c]], edgecolor='none'))
ax.set_xticks(range(len(taus))); ax.set_xticklabels([f'τ={t}' for t in taus], fontsize=8.6)
ax.set_yticks(range(len(HOURS))); ax.set_yticklabels(HOURS.values(), fontsize=9.2)
ax.tick_params(axis='y', pad=14)
ax.set_xlabel('工作负荷压力分位点')
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(length=0)
ax.add_patch(plt.Rectangle((-0.5, 0.5), len(taus), 1, fill=False, edgecolor=M['blue'], lw=2.2))
cb = fig.colorbar(im, ax=ax, shrink=0.82, pad=0.015)
cb.set_label('分位数回归系数 β(τ)', fontsize=9); cb.outline.set_visible(False)
plt.tight_layout(); plt.savefig('figv6_qheat.pdf', bbox_inches='tight'); plt.close()

# ============ 性别调节（置信带） ============
X = Z[CTRL + list(HOURS) + list(RES)].assign(inter=Z['TT3G18C'] * Z['female'])
Xc = sm.add_constant(X)
mi = sm.WLS(y, Xc, weights=w).fit(cov_type='HC1')
bm, bi = mi.params['TT3G18C'], mi.params['inter']
mu, sd = d['TT3G18C'].mean(), d['TT3G18C'].std()
xs = np.linspace(Z['TT3G18C'].quantile(0.02), Z['TT3G18C'].quantile(0.98), 60)
V = mi.cov_params()
fig, ax = plt.subplots(figsize=(7.2, 4.4))
sel = rng.choice(len(d), 900, replace=False)
ax.scatter(d['TT3G18C'].values[sel] + rng.normal(0, 0.12, 900), y.values[sel],
           s=4, color='#9fb0b5', alpha=0.16, lw=0, zorder=1)
for f, col, lab in [(0, M['blue'], f'男教师（β = {bm:.3f}）'), (1, M['red'], f'女教师（β = {bm+bi:.3f}）')]:
    pred, se = [], []
    for x in xs:
        row = pd.Series(0.0, index=Xc.columns)
        row['const'] = 1; row['TT3G18C'] = x; row['female'] = f; row['inter'] = x * f
        row['master'] = d['master'].mean()
        pred.append(float(row @ mi.params)); se.append(float(np.sqrt(row @ V @ row)))
    pred, se = np.array(pred), np.array(se)
    ax.fill_between(mu + xs * sd, pred - 1.96 * se, pred + 1.96 * se, color=col, alpha=0.13, lw=0, zorder=2)
    ax.plot(mu + xs * sd, pred, color=col, lw=2.4, label=lab, zorder=3)
ax.set_xlabel('每周批改作业小时数'); ax.set_ylabel('预测工作负荷压力（标准化）')
ax.set_ylim(-1.1, 1.35)
ax.legend(fontsize=9.2, title='批改作业 × 性别交互：p = 0.031', title_fontsize=9, loc='upper left')
ax.grid(alpha=0.3, ls=':'); ax.set_axisbelow(True)
plt.tight_layout(); plt.savefig('figv6_inter.pdf'); plt.close()

# ============ 新图1：Bootstrap 系数抽样分布脊线图 ============
Bn = 1000
Xb = sm.add_constant(Z[CTRL + list(HOURS) + list(RES)]).values
cols = ['const'] + CTRL + list(HOURS) + list(RES)
idx_tasks = [cols.index(c) for c in HOURS]
yv, wv = y.values, w.values
boot = np.zeros((Bn, len(HOURS)))
nobs = len(yv)
for b_ in range(Bn):
    ii = rng.integers(0, nobs, nobs)
    sw = np.sqrt(wv[ii])[:, None]
    beta, *_ = np.linalg.lstsq(Xb[ii] * sw, yv[ii] * sw.ravel(), rcond=None)
    boot[b_] = beta[idx_tasks]
order_b = np.argsort(boot.mean(0))[::-1]
fig, ax = plt.subplots(figsize=(8.0, 5.6))
xs = np.linspace(-0.20, 0.32, 400)
for rank, oi in enumerate(order_b):
    c = list(HOURS)[oi]
    base = len(order_b) - 1 - rank
    kde = gaussian_kde(boot[:, oi])
    dens = kde(xs); dens = dens / dens.max() * 0.85
    col = CAT_COLOR[CAT[c]]
    ax.fill_between(xs, base, base + dens, color=col, alpha=0.55, lw=0, zorder=3)
    ax.plot(xs, base + dens, color='white', lw=1.0, zorder=4)
    lo_, mu_, hi_ = np.percentile(boot[:, oi], [2.5, 50, 97.5])
    ax.plot([lo_, hi_], [base + 0.02, base + 0.02], color='#2b3a42', lw=1.6, zorder=5)
    ax.plot(mu_, base + 0.02, 'o', mfc='white', mec='#2b3a42', ms=4.4, mew=1.2, zorder=6)
    ax.text(0.335, base + 0.30, f'{HOURS[c]}', fontsize=9.6, va='center', color='#2b3a42')
    ax.text(0.335, base + 0.04, f'[{lo_:.2f}, {hi_:.2f}]', fontsize=7.8, va='center', color='#8a9aa0')
ax.axvline(0, color=M['grey'], lw=1.0, ls=(0, (4, 3)), zorder=2)
ax.set_xlim(-0.20, 0.46); ax.set_ylim(-0.25, len(order_b) + 0.6)
ax.set_yticks([])
ax.set_xlabel('全模型（M3 设定）标准化系数 β 的 Bootstrap 抽样分布（B = 1000）')
ax.spines['left'].set_visible(False)
ax.grid(axis='x', alpha=0.3, ls=':'); ax.set_axisbelow(True)
plt.tight_layout(); plt.savefig('figv6_boot.pdf'); plt.close()
lo_, hi_ = np.percentile(boot[:, list(HOURS).index('TT3G18C')], [2.5, 97.5])
print(f'Bootstrap 批改作业 95%CI: [{lo_:.3f}, {hi_:.3f}]')

# ============ 新图2：性别时间画像雷达图 ============
male_m = [wm(d.loc[d.female == 0, c], w[d.female == 0]) for c in HOURS]
fem_m = [wm(d.loc[d.female == 1, c], w[d.female == 1]) for c in HOURS]
print('雷达图数据 男/女:')
for c, a, b_ in zip(HOURS, male_m, fem_m):
    print(f'  {HOURS[c]}: 男 {a:.2f}  女 {b_:.2f}')
ang = np.linspace(0, 2 * np.pi, len(HOURS), endpoint=False).tolist()
ang += ang[:1]
fig = plt.figure(figsize=(6.8, 6.4))
ax = fig.add_subplot(111, projection='polar')
ax.set_theta_offset(np.pi / 2); ax.set_theta_direction(-1)
for valsg, col, lab in [(male_m, M['blue'], '男教师'), (fem_m, M['red'], '女教师')]:
    vv = valsg + valsg[:1]
    ax.plot(ang, vv, color=col, lw=2.0, label=lab, zorder=3)
    ax.fill(ang, vv, color=col, alpha=0.12, zorder=2)
    ax.scatter(ang[:-1], valsg, s=18, color=col, zorder=4)
ax.set_xticks(ang[:-1])
ax.set_xticklabels([HOURS[c] for c in HOURS], fontsize=9.6)
i_c = list(HOURS).index('TT3G18C')                     # 标注差异最大的批改作业轴
ax.annotate(f'{fem_m[i_c]:.1f} h', xy=(ang[i_c], fem_m[i_c]), xytext=(ang[i_c] + 0.16, fem_m[i_c] + 0.7),
            fontsize=9, color=M['red'], fontweight='bold')
ax.annotate(f'{male_m[i_c]:.1f} h', xy=(ang[i_c], male_m[i_c]), xytext=(ang[i_c] + 0.20, male_m[i_c] - 1.15),
            fontsize=9, color=M['blue'], fontweight='bold')
ax.set_rlabel_position(200)
ax.set_yticks([2, 4, 6, 8])
ax.set_yticklabels(['2h', '4h', '6h', '8h'], fontsize=7.5, color='#9fb0b5')
ax.set_ylim(0, 9.6)
ax.grid(color='#d8e2e4', lw=0.7)
ax.spines['polar'].set_color('#d8e2e4')
ax.legend(loc='lower right', bbox_to_anchor=(1.12, -0.04), fontsize=9.5, frameon=False)
plt.tight_layout(); plt.savefig('figv6_radar.pdf', bbox_inches='tight'); plt.close()

print('图已保存: figv6_rose / corrbubble / raincloud / forest / qheat / inter / boot / radar .pdf')
