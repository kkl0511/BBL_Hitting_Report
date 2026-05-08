"""
build_metadata.py
=================
코호트 분포 통계량 + Bat Speed 예측 다중회귀 모델 학습 →
metadata_batting.js에 들어갈 JSON 객체 산출.

투수 리포트 v33.21의 VELO_REGRESSION_v33_21와 동일한 흐름:
  1. 코호트 데이터 + 체력 데이터 병합
  2. 핵심 메카닉 + 체력 변수로 Bat Speed 다중회귀 학습 (OLS)
  3. 비표준화·표준화 계수, R², LOO-CV R² 산출
  4. metadata.js 입력용 JSON 출력

사용법:
    python build_metadata.py
출력:
    data/cohort_distributions.json — 변수별 mean·sd·median·q25·q75·n
    data/bat_speed_regression.json — 회귀 계수, R², LOO-CV
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path


DATA_DIR = Path(__file__).parent / 'data'

# ============================================================================
# 1. 데이터 로드
# ============================================================================
cohort = pd.read_csv(DATA_DIR / 'cohort_batting_per_session.csv')
fitness = pd.read_csv(DATA_DIR / 'master_fitness_batting.csv')
df = cohort.merge(fitness, on='athlete_id', suffixes=('', '_fit'))
print(f"Merged: {len(df)} batters × {len(df.columns)} cols")


# ============================================================================
# 2. 코호트 분포 통계량 산출
# ============================================================================
# 모든 numeric 변수의 mean/sd/median/q25/q75/n
NUMERIC_VARS = [c for c in df.columns
                if df[c].dtype in (np.float64, np.float32, np.int64, np.int32)
                and not c.startswith('fault_')          # binary fault는 별도
                and c not in ('session_seq',)]

distributions = {}
for v in NUMERIC_VARS:
    s = df[v].dropna()
    if len(s) < 5:
        continue
    distributions[v] = {
        'mean':   round(float(s.mean()), 4),
        'sd':     round(float(s.std()), 4),
        'median': round(float(s.median()), 4),
        'q25':    round(float(s.quantile(0.25)), 4),
        'q75':    round(float(s.quantile(0.75)), 4),
        'min':    round(float(s.min()), 4),
        'max':    round(float(s.max()), 4),
        'n':      int(len(s)),
    }

# Fault 변수는 prevalence(발생률)만
FAULT_VARS = [c for c in df.columns if c.startswith('fault_')]
fault_prevalence = {}
for v in FAULT_VARS:
    s = df[v].dropna()
    if len(s) > 0:
        fault_prevalence[v] = {
            'prevalence': round(float(s.mean()), 4),
            'n_positive': int(s.sum()),
            'n':          int(len(s)),
        }

print(f"\nDistributions computed: {len(distributions)} numeric vars + {len(fault_prevalence)} faults")

# 저장
with open(DATA_DIR / 'cohort_distributions.json', 'w', encoding='utf-8') as f:
    json.dump({
        'distributions': distributions,
        'fault_prevalence': fault_prevalence,
        'n_total': len(df),
    }, f, ensure_ascii=False, indent=2)


# ============================================================================
# 3. Bat Speed 다중회귀 (OLS) 학습
# ============================================================================
# 투수 리포트의 v33.21 핵심 모델 = 메카닉 5 + 신체 5 (10 변수)
# 타격 버전:  메카닉 6 + 체력 4 (10 변수)

mech_predictors = [
    'upper_arm_rotation_velo_at_swing_dps',  # Driveline Swing Rotation, high importance
    'torso_rotation_velo_at_swing_dps',       # Driveline Swing Rotation, high
    'cog_decel_mps',                          # Driveline CoG, high
    'max_x_factor',                           # Hip-Shoulder separation
    'pelvis_to_trunk_velocity_speedup',       # Kinetic chain efficiency
    'on_plane_efficiency',                    # Bat path
]
fitness_predictors = [
    'grip_strength_kg',
    'cmj_pp_bm',
    'rotation_pp_w_kg',
    'height_cm',
]
predictors = mech_predictors + fitness_predictors
target = 'bat_speed_mph'

# 결측 없는 행만
sub = df[predictors + [target]].dropna()
X = sub[predictors].values
y = sub[target].values
n = len(y)
print(f"\nRegression sample: n={n}")

# OLS via numpy lstsq
X_aug = np.column_stack([np.ones(n), X])
beta, *_ = np.linalg.lstsq(X_aug, y, rcond=None)
intercept = float(beta[0])
coefs = {p: float(beta[i+1]) for i, p in enumerate(predictors)}

# R²
y_pred = X_aug @ beta
ss_res = float(np.sum((y - y_pred)**2))
ss_tot = float(np.sum((y - y.mean())**2))
r2 = 1 - ss_res / ss_tot
adj_r2 = 1 - (1 - r2) * (n - 1) / (n - len(predictors) - 1)

# 표준화 계수 (β)
X_std = (X - X.mean(0)) / X.std(0)
y_std = (y - y.mean()) / y.std()
X_std_aug = np.column_stack([np.ones(n), X_std])
beta_std, *_ = np.linalg.lstsq(X_std_aug, y_std, rcond=None)
beta_std_dict = {p: float(beta_std[i+1]) for i, p in enumerate(predictors)}

# Leave-one-out CV
loo_residuals = []
for i in range(n):
    mask = np.ones(n, dtype=bool); mask[i] = False
    X_train = np.column_stack([np.ones(mask.sum()), X[mask]])
    y_train = y[mask]
    b, *_ = np.linalg.lstsq(X_train, y_train, rcond=None)
    y_hat_i = b[0] + X[i] @ b[1:]
    loo_residuals.append(y[i] - y_hat_i)
loo_residuals = np.array(loo_residuals)
loo_ss_res = float(np.sum(loo_residuals**2))
loo_r2 = 1 - loo_ss_res / ss_tot

print(f"\n=== Bat Speed Regression (n={n}) ===")
print(f"  R²        = {r2:.4f}")
print(f"  adj R²    = {adj_r2:.4f}")
print(f"  LOO-CV R² = {loo_r2:.4f}")
print(f"\n  intercept = {intercept:.4f}")
print(f"\n  비표준화 계수 + 표준화 β:")
# 표준화 β 절대값 큰 순으로 정렬
sorted_p = sorted(predictors, key=lambda p: abs(beta_std_dict[p]), reverse=True)
for p in sorted_p:
    print(f"    {p:45s}  coef={coefs[p]:+.4f}  β={beta_std_dict[p]:+.3f}")

# JSON 저장
regression = {
    'model': 'BAT_SPEED_REGRESSION_v1',
    'target': target,
    'predictors': predictors,
    'intercept': round(intercept, 6),
    'coefs': {k: round(v, 6) for k, v in coefs.items()},
    'beta_standardized': {k: round(v, 4) for k, v in beta_std_dict.items()},
    'R2': round(r2, 4),
    'adj_R2': round(adj_r2, 4),
    'LOO_CV_R2': round(loo_r2, 4),
    'n': n,
    'predictor_means': {p: round(float(sub[p].mean()), 4) for p in predictors},
    'predictor_sds':   {p: round(float(sub[p].std()),  4) for p in predictors},
}

with open(DATA_DIR / 'bat_speed_regression.json', 'w', encoding='utf-8') as f:
    json.dump(regression, f, ensure_ascii=False, indent=2)


# ============================================================================
# 4. 변수 elite 기준값 산출 (Driveline 5-카테고리 + Uplift extras)
# ============================================================================
# 코호트 상위 25% (q75)을 elite proxy로
# 일부 변수는 "낮을수록 좋음"(예: time_to_contact, attack_angle_sd) → q25 사용
elite_key_vars = {
    # Driveline Stride Posture
    'max_pelvis_rotation_at_stride_deg':   {'direction': 'lower_is_better', 'unit': 'deg'},
    'torso_rotation_at_fp_deg':            {'direction': 'two_sided', 'unit': 'deg'},
    'rear_shoulder_adduction_at_fp_deg':   {'direction': 'two_sided', 'unit': 'deg'},
    'lead_hip_posterior_tilt_at_fp_deg':   {'direction': 'two_sided', 'unit': 'deg'},
    # Stride Rotation
    'max_pelvis_rotation_velo_at_stride_dps': {'direction': 'higher_is_better', 'unit': 'deg/s'},
    'max_torso_rotation_velo_at_stride_dps':  {'direction': 'higher_is_better', 'unit': 'deg/s'},
    # Swing Posture
    'pelvis_rotation_at_swing_deg':        {'direction': 'higher_is_better', 'unit': 'deg'},
    'lead_hip_posterior_tilt_at_swing_deg':{'direction': 'two_sided', 'unit': 'deg'},
    'lead_hip_adduction_at_fp_deg':        {'direction': 'two_sided', 'unit': 'deg'},
    'lead_hip_adduction_at_swing_deg':     {'direction': 'two_sided', 'unit': 'deg'},
    # Swing Rotation
    'pelvis_rotation_velo_at_swing_dps':   {'direction': 'higher_is_better', 'unit': 'deg/s'},
    'torso_rotation_velo_at_swing_dps':    {'direction': 'higher_is_better', 'unit': 'deg/s'},
    'upper_arm_rotation_velo_at_swing_dps':{'direction': 'higher_is_better', 'unit': 'deg/s'},
    # CoG
    'max_cog_velo_at_stride_mps':          {'direction': 'higher_is_better', 'unit': 'm/s'},
    'max_cog_velo_mps':                    {'direction': 'higher_is_better', 'unit': 'm/s'},
    'cog_decel_mps':                       {'direction': 'higher_is_better', 'unit': 'm/s'},
    # Uplift extras
    'max_x_factor':                        {'direction': 'higher_is_better', 'unit': 'deg'},
    'pelvis_to_trunk_velocity_speedup':    {'direction': 'higher_is_better', 'unit': 'ratio'},
    'trunk_to_arm_velocity_speedup':       {'direction': 'higher_is_better', 'unit': 'ratio'},
    'on_plane_efficiency':                 {'direction': 'higher_is_better', 'unit': '%'},
    'attack_angle':                        {'direction': 'two_sided', 'unit': 'deg'},
    'hip_hinge':                           {'direction': 'two_sided', 'unit': 'deg'},
    'trunk_coil':                          {'direction': 'higher_is_better', 'unit': 'deg'},
    'linear_stretch':                      {'direction': 'higher_is_better', 'unit': '-'},
    # SD (consistency) — 모두 lower_is_better
    'bat_speed_sd_mph':                    {'direction': 'lower_is_better', 'unit': 'mph'},
    'attack_angle_sd_deg':                 {'direction': 'lower_is_better', 'unit': 'deg'},
    'time_to_contact_sd_s':                {'direction': 'lower_is_better', 'unit': 's'},
    'peak_arm_av_sd_dps':                  {'direction': 'lower_is_better', 'unit': 'deg/s'},
    'peak_trunk_av_sd_dps':                {'direction': 'lower_is_better', 'unit': 'deg/s'},
    'max_x_factor_sd_deg':                 {'direction': 'lower_is_better', 'unit': 'deg'},
    # Blast Motion
    'blast_bat_speed_mph':                 {'direction': 'higher_is_better', 'unit': 'mph'},
    'blast_peak_hand_speed_mph':           {'direction': 'higher_is_better', 'unit': 'mph'},
    'blast_rotational_acceleration_g':     {'direction': 'higher_is_better', 'unit': 'g'},
    'blast_time_to_contact_s':             {'direction': 'lower_is_better', 'unit': 's'},
    'blast_attack_angle_deg':              {'direction': 'two_sided', 'unit': 'deg'},
    'blast_on_plane_efficiency_pct':       {'direction': 'higher_is_better', 'unit': '%'},
    'blast_vertical_bat_angle_deg':        {'direction': 'two_sided', 'unit': 'deg'},
    'blast_power_kw':                      {'direction': 'higher_is_better', 'unit': 'kW'},
    'blast_early_connection_deg':          {'direction': 'two_sided', 'unit': 'deg', 'optimal': 90},
    'blast_connection_at_impact_deg':      {'direction': 'two_sided', 'unit': 'deg', 'optimal': 90},
    # 체력
    'grip_strength_kg':    {'direction': 'higher_is_better', 'unit': 'kg'},
    'cmj_height_cm':       {'direction': 'higher_is_better', 'unit': 'cm'},
    'cmj_pp_bm':           {'direction': 'higher_is_better', 'unit': 'W/kg'},
    'imtp_pp_bm':          {'direction': 'higher_is_better', 'unit': 'W/kg'},
    'rotation_pp_w_kg':    {'direction': 'higher_is_better', 'unit': 'W/kg'},
    'sprint_30m_s':        {'direction': 'lower_is_better', 'unit': 's'},
    'broad_jump_cm':       {'direction': 'higher_is_better', 'unit': 'cm'},
    'height_cm':           {'direction': 'higher_is_better', 'unit': 'cm'},
    'weight_kg':           {'direction': 'two_sided', 'unit': 'kg'},
}

variable_metadata = {}
for v, info in elite_key_vars.items():
    if v not in distributions:
        continue
    d = distributions[v]
    direction = info['direction']
    
    # optimal — 방향에 따라 결정
    if 'optimal' in info:
        optimal = info['optimal']
    elif direction == 'higher_is_better':
        optimal = d['q75']
    elif direction == 'lower_is_better':
        optimal = d['q25']
    else:
        optimal = d['median']
    
    # sigma — gaussian 점수 함수의 폭. 보통 코호트 sd 기반
    sigma = max(0.5 * d['sd'], 0.001)
    
    variable_metadata[v] = {
        'direction': direction,
        'unit':      info['unit'],
        'optimal':   round(float(optimal), 4),
        'sigma':     round(float(sigma), 4),
        'mean':      d['mean'],
        'sd':        d['sd'],
        'median':    d['median'],
        'q25':       d['q25'],
        'q75':       d['q75'],
        'n':         d['n'],
    }

with open(DATA_DIR / 'variable_metadata.json', 'w', encoding='utf-8') as f:
    json.dump(variable_metadata, f, ensure_ascii=False, indent=2)

print(f"\nVariable metadata saved: {len(variable_metadata)} variables")
print(f"\nAll outputs in {DATA_DIR.resolve()}/")
