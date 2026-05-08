"""
attach_synthetic_for_target.py
==============================
실제 추출된 선수(s13 엄준상)의 Uplift 메카닉 데이터에
합성 Blast Motion + 체력 데이터를 부착한다.

이 선수의 메카닉 수준을 기반으로 그럴듯한 Blast/체력 값을 생성:
  - upper_arm_rotation_velo_at_swing_dps, peak_arm_av 등이 코호트 분포에서
    어디 위치하는지 percentile 계산 → 그 percentile에 해당하는 Blast/체력 값 생성
"""

import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'
RNG = np.random.default_rng(seed=313)  # s13용 시드

# 추출된 실제 선수 데이터
target = pd.read_csv(DATA_DIR / 'bbl_batting_per_session.csv')
print(f"Target athlete data: {len(target)} session × {len(target.columns)} cols")
print(f"Athlete: {target['athlete_name'].iloc[0]}")
print(f"Handedness: {target['handedness'].iloc[0]}")

# 코호트 분포
cohort = pd.read_csv(DATA_DIR / 'cohort_batting_per_session.csv')


# ----------------------------------------------------------------------------
# 1. 메카닉 수준 추정 (코호트 percentile 평균)
# ----------------------------------------------------------------------------
key_vars = [
    'upper_arm_rotation_velo_at_swing_dps',
    'torso_rotation_velo_at_swing_dps',
    'pelvis_rotation_velo_at_swing_dps',
    'cog_decel_mps',
    'max_x_factor',
    'on_plane_efficiency',
]

percentiles = []
for v in key_vars:
    if v in cohort.columns and v in target.columns:
        target_val = target[v].iloc[0]
        if pd.notna(target_val):
            pct = (cohort[v] < target_val).mean() * 100
            percentiles.append(pct)
            print(f"  {v:50s} target={target_val:.2f}  cohort_pct={pct:.1f}")

mean_pct = np.mean(percentiles)
print(f"\nMechanic skill percentile (cohort-relative): {mean_pct:.1f}")

# percentile → z-score 변환 (대략)
from scipy.stats import norm
skill_z = norm.ppf(np.clip(mean_pct/100, 0.01, 0.99))
print(f"Skill latent z-score: {skill_z:+.2f}")


# ----------------------------------------------------------------------------
# 2. 합성 체력 데이터 (s13)
# ----------------------------------------------------------------------------
# skill_z를 기준으로 체력값 생성 (코호트 분포 mean + skill_z*0.5*sd + noise)
def synth_fitness(mean, sd, skill_corr=0.5, lower=None, upper=None):
    val = mean + sd * (skill_corr * skill_z + np.sqrt(1 - skill_corr**2) * RNG.normal())
    if lower is not None: val = max(val, lower)
    if upper is not None: val = min(val, upper)
    return val

s13_fitness = {
    'athlete_id':       's13',
    'athlete_name':     'S13 엄준상',
    'height_cm':        round(synth_fitness(178, 6.5, 0.2, 160, 195), 1),
    'weight_kg':        round(synth_fitness(80, 9, 0.25, 58, 110), 1),
    'grip_strength_kg': round(synth_fitness(50, 8, 0.55, 25, 75), 1),
    'cmj_height_cm':    round(synth_fitness(48, 7, 0.5, 25, 70), 1),
    'cmj_pp_bm':        round(synth_fitness(54, 7, 0.5, 30, 80), 2),
    'imtp_pp_bm':       round(synth_fitness(28, 4, 0.5, 15, 45), 2),
    'rotation_pp_w_kg': round(synth_fitness(7.0, 1.5, 0.55, 2.5, 12), 2),
    'sprint_30m_s':     round(synth_fitness(4.30, 0.25, -0.45, 3.7, 5.2), 2),
    'broad_jump_cm':    round(synth_fitness(245, 25, 0.5, 170, 320), 1),
}
print(f"\n=== s13 Fitness (synthetic) ===")
for k, v in s13_fitness.items():
    print(f"  {k:20s} = {v}")


# ----------------------------------------------------------------------------
# 3. 합성 Blast Motion (s13)
# ----------------------------------------------------------------------------
# Bat Speed: 회귀식 사용
import json
with open(DATA_DIR / 'bat_speed_regression.json', 'r') as f:
    reg = json.load(f)

# 회귀 예측 — 결측은 코호트 mean으로 imputation
pred_inputs = {}
for p in reg['predictors']:
    if p in target.columns:
        v = target[p].iloc[0]
        pred_inputs[p] = v if pd.notna(v) else reg['predictor_means'][p]
    elif p in s13_fitness:
        pred_inputs[p] = s13_fitness[p]
    else:
        pred_inputs[p] = reg['predictor_means'][p]

predicted_bat_speed = reg['intercept']
for p in reg['predictors']:
    predicted_bat_speed += reg['coefs'][p] * pred_inputs[p]

print(f"\nPredicted Bat Speed (regression): {predicted_bat_speed:.2f} mph")

# 실제 Blast 측정값 — 예측값 + 잔차(skill 효율성)
# skill이 높을수록 잔차 +값일 가능성
residual = 1.5 * skill_z + RNG.normal(0, 1.5)
actual_bat_speed = float(predicted_bat_speed + residual)
actual_bat_speed = max(50, min(90, actual_bat_speed))

s13_blast = {
    'blast_bat_speed_mph':              round(actual_bat_speed, 2),
    'blast_peak_hand_speed_mph':        round(0.32 * actual_bat_speed + RNG.normal(0, 1), 2),
    'blast_rotational_acceleration_g':  round(synth_fitness(14, 3.5, 0.55, 5, 25), 2),
    'blast_time_to_contact_s':          round(synth_fitness(0.155, 0.025, -0.4, 0.10, 0.25), 4),
    'blast_attack_angle_deg':           round(target['attack_angle'].iloc[0] + RNG.normal(0, 2), 2),
    'blast_on_plane_efficiency_pct':    round(target['on_plane_efficiency'].iloc[0] + RNG.normal(0, 4), 2),
    'blast_vertical_bat_angle_deg':     round(synth_fitness(-32, 5, 0.0, -50, -15), 2),
    'blast_power_kw':                   round(0.06 * actual_bat_speed + RNG.normal(0, 0.3), 3),
    'blast_early_connection_deg':       round(synth_fitness(88, 6, 0.25, 65, 110), 2),
    'blast_connection_at_impact_deg':   round(synth_fitness(91, 6, 0.30, 65, 110), 2),
}

print(f"\n=== s13 Blast Motion (synthetic) ===")
for k, v in s13_blast.items():
    print(f"  {k:40s} = {v}")


# ----------------------------------------------------------------------------
# 4. SD 변수 합성 (한 swing 데이터지만 SD를 보여주려면 추가 swing 가정)
# ----------------------------------------------------------------------------
# 일관성 SD — skill이 높을수록 SD가 작음 (음 상관)
s13_sd = {
    'bat_speed_sd_mph':       round(synth_fitness(2.2, 0.7, -0.55, 0.4, 5.0), 3),
    'attack_angle_sd_deg':    round(synth_fitness(3.5, 1.2, -0.50, 0.5, 8.0), 3),
    'time_to_contact_sd_s':   round(synth_fitness(0.012, 0.005, -0.45, 0.002, 0.030), 5),
    'peak_arm_av_sd_dps':     round(synth_fitness(120, 50, -0.5, 20, 300), 1),
    'peak_trunk_av_sd_dps':   round(synth_fitness(50, 22, -0.55, 10, 150), 1),
    'max_x_factor_sd_deg':    round(synth_fitness(3.5, 1.6, -0.55, 0.5, 10), 3),
}

# ----------------------------------------------------------------------------
# 5. s13 메카닉 + Blast + SD 합치기 → bbl_batting_per_session.csv 갱신
# ----------------------------------------------------------------------------
target_full = target.copy()
target_full['athlete_id'] = 's13'
target_full['athlete_name'] = 'S13 엄준상'

for k, v in s13_blast.items():
    target_full[k] = v
for k, v in s13_sd.items():
    target_full[k] = v

# 기존 파일 덮어쓰기 (s13만 들어있는 파일)
target_full.to_csv(DATA_DIR / 'bbl_batting_per_session.csv', index=False)
print(f"\nSaved: bbl_batting_per_session.csv (s13 with Blast + SD added)")

# 체력 마스터에 s13 추가
fitness_master = pd.read_csv(DATA_DIR / 'master_fitness_batting.csv')
# 이미 s13가 있으면 제거 후 추가
fitness_master = fitness_master[fitness_master['athlete_id'] != 's13']
new_row = pd.DataFrame([s13_fitness])
new_row['bat_speed_mph'] = s13_blast['blast_bat_speed_mph']
fitness_master = pd.concat([fitness_master, new_row], ignore_index=True)
fitness_master.to_csv(DATA_DIR / 'master_fitness_batting.csv', index=False)
print(f"Saved: master_fitness_batting.csv (s13 added)")

# 합성 코호트에도 일부 SD/Blast 변수가 있으니 확인
# (cohort_batting_per_session.csv는 그대로 유지 — s13는 별도 파일)

print(f"\n=== Final s13 summary ===")
print(f"  Bat Speed (Blast):     {s13_blast['blast_bat_speed_mph']:.1f} mph")
print(f"  Predicted (regression): {predicted_bat_speed:.1f} mph")
print(f"  Residual (efficiency):  {residual:+.1f} mph")
print(f"  Skill percentile:       {mean_pct:.0f}th")
