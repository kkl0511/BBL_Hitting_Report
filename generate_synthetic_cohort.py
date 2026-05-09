"""
generate_synthetic_cohort.py
============================
한국 고교 야구 타자 80명의 합성 코호트 생성 (v2 — HS 베이스라인).

목적: 코호트 분포를 'KBO 고교 야구' 수준으로 보정.
v1(elite-skewed)에서는 측정 선수가 코호트 대비 낮게 보였는데,
v2에서는 우수 고교생(엄준상 같은 상위 타자)이 ~95+ percentile에 위치하도록 재보정.

생성 데이터:
  1. data/cohort_batting_per_session.csv  — 메카닉 스칼라 (Uplift 추출 + Blast Motion)
  2. data/master_fitness_batting.csv      — 체력 데이터 (각 선수 1행)

v2 설계 핵심 (vs v1):
  - 회전 속도 평균 ↓ (HS는 프로/Driveline elite보다 낮음)
    · pelvis_velo_at_swing  v1 620 → v2 470 °/s
    · torso_velo_at_swing   v1 860 → v2 580 °/s
    · upper_arm_velo_at_swing v1 1500 → v2 750 °/s
  - max_x_factor 평균 v1 30 → v2 15°
  - 회전 효율 (speedup) 하향
  - Bat Speed baseline v1 65 → v2 47 mph
  - 엄준상의 측정값(599.7/717.7/947.3, 22°)은 모두 z≈1.6 (상위 ~5%)에 위치
"""

import numpy as np
import pandas as pd
from pathlib import Path

# 재현성
RNG = np.random.default_rng(seed=42)

# ============================================================================
# 코호트 크기
# ============================================================================
N = 80


# ============================================================================
# 1. 잠재 능력 (latent skill) — 메카닉/체력/Bat Speed 모두에 영향
# ============================================================================
latent_skill = RNG.normal(0, 1, N)  # 표준화된 능력치


def correlated(target_mean, target_sd, corr_with_skill, n=N, lower=None, upper=None):
    """
    잠재 능력과 corr_with_skill만큼 상관된 변수를 생성한다.
    
    Args:
        target_mean: 코호트 평균
        target_sd: 코호트 표준편차
        corr_with_skill: 잠재 능력과의 상관계수 (0~1)
        lower, upper: clip 범위 (선택)
    """
    noise = RNG.normal(0, 1, n)
    z = corr_with_skill * latent_skill + np.sqrt(1 - corr_with_skill**2) * noise
    val = target_mean + target_sd * z
    if lower is not None:
        val = np.maximum(val, lower)
    if upper is not None:
        val = np.minimum(val, upper)
    return val


# ============================================================================
# 2. 선수 메타 (s00~s79)
# ============================================================================
ids = [f's{i:02d}' for i in range(N)]
# 80명 중 70명은 우타, 10명은 좌타 (KBO 분포 대략)
handedness = ['right'] * 65 + ['left'] * 15
RNG.shuffle(handedness)


# ============================================================================
# 3. 메카닉 변수 (Uplift 추출 분포)
# ============================================================================
# Driveline 5-카테고리 변수 + Uplift 자체 산출 변수
# 주의: max_pelvis_rotation_at_stride_deg는 Δ(stride 동안 회전량)이라 
# 절대값이 Driveline의 "9°"보다 클 수 있음 — 코호트 내 상대 percentile로 평가

mech = {}

# Stride Posture
mech['max_pelvis_rotation_at_stride_deg'] = correlated(40, 15, 0.3, lower=0, upper=120)
mech['torso_rotation_at_fp_deg']          = correlated(-15, 9, -0.4, lower=-50, upper=20)  # 음수, closed-good
mech['rear_shoulder_adduction_at_fp_deg'] = correlated(-40, 14, -0.25, lower=-80, upper=10)
mech['lead_hip_posterior_tilt_at_fp_deg'] = correlated(5, 9, 0.15, lower=-20, upper=30)

# Stride Rotation (v2: HS baseline)
mech['max_pelvis_rotation_velo_at_stride_dps'] = correlated(420, 110, 0.55, lower=100, upper=800)
mech['max_torso_rotation_velo_at_stride_dps']  = correlated(450, 110, 0.45, lower=100, upper=850)

# Swing Posture
mech['pelvis_rotation_at_swing_deg']        = correlated(60, 12, 0.3, lower=20, upper=110)
mech['lead_hip_posterior_tilt_at_swing_deg']= correlated(6, 8, 0.15, lower=-20, upper=35)
mech['lead_hip_adduction_at_fp_deg']        = correlated(18, 9, 0.1, lower=-10, upper=45)
mech['lead_hip_adduction_at_swing_deg']     = correlated(25, 10, 0.15, lower=-10, upper=55)

# Swing Rotation (v2: HS baseline — 평균은 KBO 고교 우타 typical)
mech['pelvis_rotation_velo_at_swing_dps']   = correlated(470, 80, 0.55, lower=200, upper=750)
mech['torso_rotation_velo_at_swing_dps']    = correlated(580, 85, 0.65, lower=300, upper=850)
mech['upper_arm_rotation_velo_at_swing_dps']= correlated(750, 120, 0.6, lower=400, upper=1200)

# CoG (v2: HS baseline — 약간 하향)
mech['max_cog_velo_at_stride_mps']  = correlated(0.75, 0.20, 0.35, lower=0.2, upper=1.6)
mech['max_cog_velo_mps']            = correlated(0.80, 0.22, 0.40, lower=0.2, upper=1.8)
mech['cog_decel_mps']               = correlated(0.65, 0.20, 0.55, lower=0.15, upper=1.5)

# Uplift extras (v2)
mech['peak_pelvis_angular_velocity'] = mech['pelvis_rotation_velo_at_swing_dps'] + RNG.normal(0, 25, N)
mech['peak_trunk_angular_velocity']  = mech['torso_rotation_velo_at_swing_dps']  + RNG.normal(0, 30, N)
mech['peak_arm_angular_velocity']    = mech['upper_arm_rotation_velo_at_swing_dps'] + RNG.normal(0, 40, N)
mech['max_x_factor']                 = correlated(15, 4.5, 0.45, lower=3, upper=35)
mech['pelvis_to_trunk_velocity_speedup'] = correlated(1.05, 0.10, 0.5, lower=0.7, upper=1.5)
mech['trunk_to_arm_velocity_speedup']    = correlated(1.35, 0.18, 0.45, lower=0.8, upper=2.0)

# Bat path / contact
mech['attack_angle']         = correlated(7, 8, 0.25, lower=-20, upper=30)
mech['on_plane_efficiency']  = correlated(83, 8, 0.5, lower=40, upper=100)
mech['swing_path_angle']     = correlated(-2, 6, 0.0, lower=-25, upper=20)

# Setup / loading
mech['hip_hinge']             = correlated(45, 12, 0.1, lower=10, upper=80)
mech['trunk_coil']            = correlated(30, 12, 0.2, lower=0, upper=70)
mech['trunk_tilt_at_launch']  = correlated(8, 8, 0.0, lower=-15, upper=35)
mech['rear_scap_load_at_launch'] = correlated(2.5, 1.2, 0.2, lower=-2, upper=8)
mech['linear_stretch']        = correlated(0.85, 0.12, 0.3, lower=0.4, upper=1.3)

# Stride
mech['stride_length']         = correlated(0.95, 0.18, 0.2, lower=0.4, upper=1.6)
mech['lead_knee_angle_at_ball_contact'] = correlated(-15, 12, 0.25, lower=-50, upper=20)

# Time
mech['time_to_ball_contact']  = correlated(0.85, 0.12, -0.3, lower=0.5, upper=1.3)
mech['time_to_launch']        = correlated(0.55, 0.10, -0.15, lower=0.3, upper=0.9)

# 결함 binary (잠재능력 낮을수록 결함 발생 확률 높음)
def fault_prob(prob_base, neg_corr=0.4):
    """ 잠재능력이 낮을수록 결함 확률 ↑ """
    z = -neg_corr * latent_skill + RNG.normal(0, 1, N)
    threshold = np.quantile(z, 1 - prob_base)
    return (z > threshold).astype(int)

mech['fault_drifting_forward']         = fault_prob(0.20, 0.5)
mech['fault_excessive_lateral_pelvis_tilt'] = fault_prob(0.15, 0.3)
mech['fault_knee_dominant_swing']      = fault_prob(0.10, 0.4)
mech['fault_vertical_pelvis_hike']     = fault_prob(0.15, 0.3)
mech['fault_sway_leg']                 = fault_prob(0.12, 0.3)
mech['fault_leads_with_wrist']         = fault_prob(0.10, 0.4)
mech['fault_rear_elbow_drag']          = fault_prob(0.18, 0.4)
mech['fault_hand_push']                = fault_prob(0.15, 0.4)
mech['fault_crashing']                 = fault_prob(0.10, 0.3)


# ============================================================================
# 4. 체력 변수 (master_fitness)
# ============================================================================
# 신체 (v2: 한국 고교 야구선수 평균)
height_cm = correlated(176, 6.5, 0.2, lower=158, upper=192)
weight_kg = correlated(75, 9, 0.25, lower=55, upper=105)
height_m  = height_cm / 100.0

# 파워/근력 (v2: HS 평균 — 프로/대학보다 약간 낮음)
grip_strength_kg = correlated(44, 7, 0.55, lower=22, upper=68)         # 악력
cmj_height_cm    = correlated(42, 6, 0.5, lower=25, upper=62)          # CMJ 점프 높이
cmj_pp_bm        = correlated(48, 6, 0.5, lower=28, upper=72)          # CMJ peak power per BM (W/kg)
imtp_pp_bm       = correlated(24, 4, 0.5, lower=14, upper=40)          # IMTP relative power
rotation_pp_w_kg = correlated(5.5, 1.3, 0.55, lower=2.0, upper=10)     # 회전 파워 (medball 등)
sprint_30m_s     = correlated(4.45, 0.25, -0.45, lower=3.9, upper=5.3) # 30m 빠를수록 좋음 → 음 상관
broad_jump_cm    = correlated(225, 22, 0.5, lower=160, upper=295)


# ============================================================================
# 5. Blast Motion 변수 (가상 — 메카닉과 강한 상관)
# ============================================================================
# Blast Motion 핵심 변수:
#   - Bat Speed (mph): 메인 KPI
#   - Rotational Acceleration (g): 0~1초 구간 가속도
#   - Peak Hand Speed (mph)
#   - Time to Contact (sec): 짧을수록 좋음
#   - Attack Angle (deg)
#   - On Plane Efficiency (%)
#   - Vertical Bat Angle (deg, 음수)
#   - Power (kW)
#   - Connection at Impact (deg, ~90 ideal)
#   - Early Connection (deg, ~85-90 ideal)

blast = {}

# Bat Speed: 잠재능력 + 메카닉 + 체력에 의해 결정 (목표 변수)
# v2: HS baseline ~47 mph (KBO 고교 우타 typical), top ~58 mph
bat_speed_mph = (
    47.0  # HS baseline
    + 3.5 * latent_skill  # 강한 잠재능력 효과
    + 0.012 * (mech['upper_arm_rotation_velo_at_swing_dps'] - 750)
    + 0.015 * (mech['torso_rotation_velo_at_swing_dps'] - 580)
    + 0.06  * (grip_strength_kg - 44)
    + 0.08  * (cmj_pp_bm - 48)
    + 0.18  * (mech['max_x_factor'] - 15)
    + 2.0   * (mech['cog_decel_mps'] - 0.65)
    + RNG.normal(0, 2.3, N)  # 잔차
)
bat_speed_mph = np.clip(bat_speed_mph, 35, 70)
blast['bat_speed_mph'] = bat_speed_mph

# Peak Hand Speed: bat speed의 약 30~35% 수준 + 노이즈
blast['peak_hand_speed_mph'] = 0.32 * bat_speed_mph + RNG.normal(0, 1.2, N)

# Rotational Acceleration: 잠재능력 + bat speed와 연관
blast['rotational_acceleration_g'] = correlated(14, 3.5, 0.55, lower=5, upper=25)

# Time to Contact: 짧을수록 좋음 — 잠재능력 음 상관
blast['time_to_contact_s'] = correlated(0.155, 0.025, -0.4, lower=0.10, upper=0.25)

# Attack Angle: Uplift attack_angle과 강한 상관
blast['attack_angle_deg'] = mech['attack_angle'] + RNG.normal(0, 2.5, N)
blast['attack_angle_deg'] = np.clip(blast['attack_angle_deg'], -25, 35)

# On Plane Efficiency
blast['on_plane_efficiency_pct'] = mech['on_plane_efficiency'] + RNG.normal(0, 5, N)
blast['on_plane_efficiency_pct'] = np.clip(blast['on_plane_efficiency_pct'], 30, 100)

# Vertical Bat Angle (수직 배트 각도, 음수)
blast['vertical_bat_angle_deg'] = correlated(-32, 5, 0.0, lower=-50, upper=-15)

# Power (kW) — bat speed와 강한 상관
blast['power_kw'] = 0.06 * bat_speed_mph + correlated(0, 0.5, 0.3) + RNG.normal(0, 0.2, N)
blast['power_kw'] = np.clip(blast['power_kw'], 1.5, 7.5)

# Connection at Impact / Early Connection (~90 ideal)
blast['early_connection_deg']     = correlated(88, 6, 0.25, lower=65, upper=110)
blast['connection_at_impact_deg'] = correlated(91, 6, 0.30, lower=65, upper=110)


# ============================================================================
# 6. 일관성 SD 변수 (선수 내 swing 간 표준편차) — 잠재능력 높을수록 SD 작음
# ============================================================================
# v2: HS는 SD가 더 큼(스윙 일관성 떨어짐). 엄준상 같은 top tier가 z≈-1.6 ⇒ 상위 5%.
mech['bat_speed_sd_mph']       = correlated(3.0, 1.0, -0.55, lower=0.5, upper=6.5)
mech['attack_angle_sd_deg']    = correlated(4.5, 1.5, -0.50, lower=0.7, upper=10.0)
mech['time_to_contact_sd_s']   = correlated(0.014, 0.006, -0.45, lower=0.002, upper=0.035)
mech['peak_arm_av_sd_dps']     = correlated(170, 45, -0.5,  lower=40, upper=320)
mech['peak_trunk_av_sd_dps']   = correlated(70,  22, -0.55, lower=15, upper=160)
mech['max_x_factor_sd_deg']    = correlated(4.5, 1.7, -0.55, lower=0.6, upper=12)


# ============================================================================
# 7. DataFrame 통합 + 저장
# ============================================================================
cohort = pd.DataFrame({
    'athlete_id': ids,
    'athlete_name': [f's{i:02d} synthetic_batter_{i:02d}' for i in range(N)],
    'session_seq': [1] * N,
    'handedness': handedness,
})

# 메카닉
for k, v in mech.items():
    cohort[k] = v

# Blast Motion
for k, v in blast.items():
    cohort['blast_' + k] = v

# 신체/체력 별도 파일
fitness = pd.DataFrame({
    'athlete_id': ids,
    'athlete_name': [f's{i:02d} synthetic_batter_{i:02d}' for i in range(N)],
    'height_cm': height_cm.round(1),
    'weight_kg': weight_kg.round(1),
    'grip_strength_kg': grip_strength_kg.round(1),
    'cmj_height_cm': cmj_height_cm.round(1),
    'cmj_pp_bm': cmj_pp_bm.round(2),
    'imtp_pp_bm': imtp_pp_bm.round(2),
    'rotation_pp_w_kg': rotation_pp_w_kg.round(2),
    'sprint_30m_s': sprint_30m_s.round(2),
    'broad_jump_cm': broad_jump_cm.round(1),
})

# 측정 구속/배트스피드 평가용 마스터에 bat_speed도 포함
fitness['bat_speed_mph'] = bat_speed_mph.round(2)


# 저장
out_dir = Path(__file__).parent / 'data'
out_dir.mkdir(exist_ok=True)
cohort.to_csv(out_dir / 'cohort_batting_per_session.csv', index=False)
fitness.to_csv(out_dir / 'master_fitness_batting.csv', index=False)

print(f"Generated synthetic cohort:")
print(f"  cohort_batting_per_session.csv  — {len(cohort)} batters × {len(cohort.columns)} cols")
print(f"  master_fitness_batting.csv      — {len(fitness)} batters × {len(fitness.columns)} cols")

# 요약 통계
print("\n=== Bat Speed Distribution ===")
print(f"  mean = {bat_speed_mph.mean():.2f} mph")
print(f"  sd   = {bat_speed_mph.std():.2f} mph")
print(f"  range= {bat_speed_mph.min():.1f} ~ {bat_speed_mph.max():.1f}")
print(f"  q25  = {np.percentile(bat_speed_mph, 25):.1f}")
print(f"  q75  = {np.percentile(bat_speed_mph, 75):.1f}")

print("\n=== Top 5 Bat Speed × Mechanics ===")
top5 = cohort.assign(bat_speed=bat_speed_mph).nlargest(5, 'bat_speed')
print(top5[['athlete_id', 'handedness', 
            'upper_arm_rotation_velo_at_swing_dps',
            'torso_rotation_velo_at_swing_dps',
            'cog_decel_mps', 'max_x_factor']].to_string(index=False))
