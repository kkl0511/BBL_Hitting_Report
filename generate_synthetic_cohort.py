"""
generate_synthetic_cohort.py
============================
KBO 고교/대학 수준 타자 80명의 합성 코호트 생성.

목적: 투수 리포트의 BBL n=169 sessions 같은 코호트 분포를 타격에서도 흉내내기.
실제 데이터가 쌓이기 전까지는 이 합성 코호트의 분포를 percentile 기준으로 사용.

생성 데이터:
  1. data/cohort_batting_per_session.csv  — 메카닉 스칼라 (Uplift 추출 + Blast Motion)
  2. data/master_fitness_batting.csv      — 체력 데이터 (각 선수 1행)

설계 핵심:
  - 80명 batters, 각 선수 1개 session
  - "잠재 능력(latent_skill)"이라는 숨은 변수로 메카닉 + 체력 + Bat Speed에
    상관관계를 부여 (현실에서 잘 치는 선수가 회전속도도 빠르고 그립도 강한 경향)
  - 노이즈 추가로 100% 결정론적이지 않게
  - 마지막에 Bat Speed를 "잠재 능력 + 일부 메카닉/체력 변수의 선형 결합 + 노이즈"로 산출
    → 다중회귀 모델 학습 가능하게
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

# Stride Rotation
mech['max_pelvis_rotation_velo_at_stride_dps'] = correlated(420, 110, 0.55, lower=100, upper=900)
mech['max_torso_rotation_velo_at_stride_dps']  = correlated(470, 130, 0.45, lower=100, upper=1000)

# Swing Posture
mech['pelvis_rotation_at_swing_deg']        = correlated(72, 14, 0.3, lower=20, upper=130)
mech['lead_hip_posterior_tilt_at_swing_deg']= correlated(8, 9, 0.15, lower=-20, upper=40)
mech['lead_hip_adduction_at_fp_deg']        = correlated(20, 10, 0.1, lower=-10, upper=50)
mech['lead_hip_adduction_at_swing_deg']     = correlated(28, 11, 0.15, lower=-10, upper=60)

# Swing Rotation
mech['pelvis_rotation_velo_at_swing_dps']   = correlated(620, 110, 0.55, lower=200, upper=1000)
mech['torso_rotation_velo_at_swing_dps']    = correlated(860, 130, 0.65, lower=300, upper=1300)
mech['upper_arm_rotation_velo_at_swing_dps']= correlated(1500, 350, 0.6, lower=500, upper=3000)

# CoG
mech['max_cog_velo_at_stride_mps']  = correlated(1.05, 0.22, 0.35, lower=0.2, upper=2.0)
mech['max_cog_velo_mps']            = correlated(1.10, 0.25, 0.4, lower=0.2, upper=2.2)
mech['cog_decel_mps']               = correlated(1.05, 0.32, 0.55, lower=0.2, upper=2.5)  # high importance!

# Uplift extras
mech['peak_pelvis_angular_velocity'] = mech['pelvis_rotation_velo_at_swing_dps'] + RNG.normal(0, 30, N)
mech['peak_trunk_angular_velocity']  = mech['torso_rotation_velo_at_swing_dps']  + RNG.normal(0, 35, N)
mech['peak_arm_angular_velocity']    = mech['upper_arm_rotation_velo_at_swing_dps'] + RNG.normal(0, 50, N)
mech['max_x_factor']                 = correlated(30, 10, 0.45, lower=5, upper=70)
mech['pelvis_to_trunk_velocity_speedup'] = correlated(1.45, 0.25, 0.5, lower=0.6, upper=2.5)
mech['trunk_to_arm_velocity_speedup']    = correlated(1.78, 0.35, 0.45, lower=0.6, upper=3.0)

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
# 신체 — 잠재능력과 일부 상관 (체격 좋은 선수가 잘 치는 경향)
height_cm = correlated(178, 6.5, 0.2, lower=160, upper=195)
weight_kg = correlated(80, 9, 0.25, lower=58, upper=110)
height_m  = height_cm / 100.0

# 파워/근력 — 잠재능력과 강한 상관
grip_strength_kg = correlated(50, 8, 0.55, lower=25, upper=75)         # 악력
cmj_height_cm    = correlated(48, 7, 0.5, lower=25, upper=70)          # CMJ 점프 높이
cmj_pp_bm        = correlated(54, 7, 0.5, lower=30, upper=80)          # CMJ peak power per BM (W/kg)
imtp_pp_bm       = correlated(28, 4, 0.5, lower=15, upper=45)          # IMTP relative power
rotation_pp_w_kg = correlated(7.0, 1.5, 0.55, lower=2.5, upper=12)     # 회전 파워 (medball 등)
sprint_30m_s     = correlated(4.30, 0.25, -0.45, lower=3.7, upper=5.2) # 30m 빠를수록 좋음 → 음 상관
broad_jump_cm    = correlated(245, 25, 0.5, lower=170, upper=320)


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
# 다중회귀 학습이 의미 있게 되도록 일부 변수 선형 결합
bat_speed_mph = (
    65.0  # baseline
    + 4.0 * latent_skill  # 강한 잠재능력 효과
    + 0.008 * (mech['upper_arm_rotation_velo_at_swing_dps'] - 1500)
    + 0.012 * (mech['torso_rotation_velo_at_swing_dps'] - 860)
    + 0.06  * (grip_strength_kg - 50)
    + 0.08  * (cmj_pp_bm - 54)
    + 0.10  * (mech['max_x_factor'] - 30)
    + 1.5   * (mech['cog_decel_mps'] - 1.05)
    + RNG.normal(0, 2.5, N)  # 잔차
)
bat_speed_mph = np.clip(bat_speed_mph, 50, 90)
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
mech['bat_speed_sd_mph']       = correlated(2.2, 0.7, -0.55, lower=0.4, upper=5.0)
mech['attack_angle_sd_deg']    = correlated(3.5, 1.2, -0.50, lower=0.5, upper=8.0)
mech['time_to_contact_sd_s']   = correlated(0.012, 0.005, -0.45, lower=0.002, upper=0.030)
mech['peak_arm_av_sd_dps']     = correlated(120, 50, -0.5, lower=20, upper=300)
mech['peak_trunk_av_sd_dps']   = correlated(50, 22, -0.55, lower=10, upper=150)
mech['max_x_factor_sd_deg']    = correlated(3.5, 1.6, -0.55, lower=0.5, upper=10)


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
