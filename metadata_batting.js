// metadata_batting.js
// =====================================================================
// 타격 리포트 변수 정의 + 코호트 분포 + Bat Speed 회귀 모델
// 자동 생성: build_js_files.py
//
// 투수 리포트의 metadata.js v33.21 구조 차용:
//   - VARIABLE_METADATA: 변수별 optimal·sigma·mean·sd·percentile 기준
//   - BAT_SPEED_REGRESSION: Bat Speed 다중회귀 (예측 + 효율 잔차)
//   - VARIABLE_LABELS: 한글/영문 라벨
//   - FAULT_LABELS: 결함 한글 라벨
// =====================================================================

const COHORT_INFO = {
  n_total: 80,
  source: 'synthetic_v1 (placeholder until real data accumulated)',
};

const VARIABLE_METADATA = {
  "max_pelvis_rotation_at_stride_deg": {
    "direction": "lower_is_better",
    "unit": "deg",
    "optimal": 29.4109,
    "sigma": 7.2497,
    "mean": 40.0894,
    "sd": 14.4995,
    "median": 38.1641,
    "q25": 29.4109,
    "q75": 48.5736,
    "n": 80,
    "label_kr": "Stride 중 골반 회전량",
    "label_en": "Max Pelvis Rotation @ Stride"
  },
  "torso_rotation_at_fp_deg": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": -16.2474,
    "sigma": 4.588,
    "mean": -15.6288,
    "sd": 9.1761,
    "median": -16.2474,
    "q25": -20.667,
    "q75": -10.4083,
    "n": 80,
    "label_kr": "FP 시점 트렁크 회전(X-factor)",
    "label_en": "Torso Rotation @ FP"
  },
  "rear_shoulder_adduction_at_fp_deg": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": -35.7137,
    "sigma": 7.2129,
    "mean": -37.4378,
    "sd": 14.4258,
    "median": -35.7137,
    "q25": -46.6219,
    "q75": -26.9492,
    "n": 80,
    "label_kr": "FP 시점 뒤쪽 어깨 내전",
    "label_en": "Rear Shoulder Adduction @ FP"
  },
  "lead_hip_posterior_tilt_at_fp_deg": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": 5.4179,
    "sigma": 4.345,
    "mean": 4.3256,
    "sd": 8.69,
    "median": 5.4179,
    "q25": -1.56,
    "q75": 9.6435,
    "n": 80,
    "label_kr": "FP 시점 골반 후방경사",
    "label_en": "Lead Hip Posterior Tilt @ FP"
  },
  "max_pelvis_rotation_velo_at_stride_dps": {
    "direction": "higher_is_better",
    "unit": "deg/s",
    "optimal": 481.16,
    "sigma": 54.3184,
    "mean": 418.7347,
    "sd": 108.6368,
    "median": 420.8703,
    "q25": 365.4385,
    "q75": 481.16,
    "n": 80,
    "label_kr": "Stride 중 골반 최고 회전속도",
    "label_en": "Max Pelvis Rot Velo @ Stride"
  },
  "max_torso_rotation_velo_at_stride_dps": {
    "direction": "higher_is_better",
    "unit": "deg/s",
    "optimal": 554.1043,
    "sigma": 60.9018,
    "mean": 452.8724,
    "sd": 121.8036,
    "median": 451.1453,
    "q25": 362.3225,
    "q75": 554.1043,
    "n": 80,
    "label_kr": "Stride 중 트렁크 최고 회전속도",
    "label_en": "Max Torso Rot Velo @ Stride"
  },
  "pelvis_rotation_at_swing_deg": {
    "direction": "higher_is_better",
    "unit": "deg",
    "optimal": 80.7225,
    "sigma": 7.5089,
    "mean": 70.7718,
    "sd": 15.0178,
    "median": 69.6218,
    "q25": 61.0849,
    "q75": 80.7225,
    "n": 80,
    "label_kr": "Down Swing 중 골반 회전량",
    "label_en": "Pelvis Rotation @ Swing"
  },
  "lead_hip_posterior_tilt_at_swing_deg": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": 9.1079,
    "sigma": 4.4272,
    "mean": 8.4114,
    "sd": 8.8543,
    "median": 9.1079,
    "q25": 0.8078,
    "q75": 14.9611,
    "n": 80,
    "label_kr": "BC 시점 골반 후방경사",
    "label_en": "Lead Hip Posterior Tilt @ Swing"
  },
  "lead_hip_adduction_at_fp_deg": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": 20.0404,
    "sigma": 5.017,
    "mean": 20.1199,
    "sd": 10.034,
    "median": 20.0404,
    "q25": 14.7117,
    "q75": 24.6416,
    "n": 80,
    "label_kr": "FP 시점 리드 고관절 내전",
    "label_en": "Lead Hip Adduction @ FP"
  },
  "lead_hip_adduction_at_swing_deg": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": 26.7862,
    "sigma": 5.2508,
    "mean": 26.8206,
    "sd": 10.5017,
    "median": 26.7862,
    "q25": 19.1561,
    "q75": 33.2294,
    "n": 80,
    "label_kr": "Down Swing 중 리드 고관절 내전",
    "label_en": "Lead Hip Adduction @ Swing"
  },
  "pelvis_rotation_velo_at_swing_dps": {
    "direction": "higher_is_better",
    "unit": "deg/s",
    "optimal": 694.8345,
    "sigma": 48.014,
    "mean": 620.5709,
    "sd": 96.0279,
    "median": 617.0964,
    "q25": 570.1133,
    "q75": 694.8345,
    "n": 80,
    "label_kr": "Down Swing 골반 회전속도",
    "label_en": "Pelvis Rot Velo @ Swing"
  },
  "torso_rotation_velo_at_swing_dps": {
    "direction": "higher_is_better",
    "unit": "deg/s",
    "optimal": 947.4177,
    "sigma": 58.3591,
    "mean": 871.3175,
    "sd": 116.7183,
    "median": 877.9572,
    "q25": 802.0505,
    "q75": 947.4177,
    "n": 80,
    "label_kr": "Down Swing 트렁크 회전속도",
    "label_en": "Torso Rot Velo @ Swing"
  },
  "upper_arm_rotation_velo_at_swing_dps": {
    "direction": "higher_is_better",
    "unit": "deg/s",
    "optimal": 1684.5448,
    "sigma": 163.4095,
    "mean": 1484.5847,
    "sd": 326.819,
    "median": 1526.518,
    "q25": 1269.8882,
    "q75": 1684.5448,
    "n": 80,
    "label_kr": "Down Swing 상완 회전속도",
    "label_en": "Upper Arm Rot Velo @ Swing"
  },
  "max_cog_velo_at_stride_mps": {
    "direction": "higher_is_better",
    "unit": "m/s",
    "optimal": 1.2206,
    "sigma": 0.1123,
    "mean": 1.0479,
    "sd": 0.2245,
    "median": 1.0405,
    "q25": 0.9075,
    "q75": 1.2206,
    "n": 80,
    "label_kr": "Stride 중 무게중심 최고속도",
    "label_en": "Max CoG Velo @ Stride"
  },
  "max_cog_velo_mps": {
    "direction": "higher_is_better",
    "unit": "m/s",
    "optimal": 1.2534,
    "sigma": 0.13,
    "mean": 1.0918,
    "sd": 0.2601,
    "median": 1.1373,
    "q25": 0.8937,
    "q75": 1.2534,
    "n": 80,
    "label_kr": "무게중심 최고속도 (전구간)",
    "label_en": "Max CoG Velo"
  },
  "cog_decel_mps": {
    "direction": "higher_is_better",
    "unit": "m/s",
    "optimal": 1.2991,
    "sigma": 0.1593,
    "mean": 1.0825,
    "sd": 0.3187,
    "median": 1.0862,
    "q25": 0.8734,
    "q75": 1.2991,
    "n": 80,
    "label_kr": "무게중심 감속량 (FP 후 block)",
    "label_en": "CoG Decel"
  },
  "max_x_factor": {
    "direction": "higher_is_better",
    "unit": "deg",
    "optimal": 34.3425,
    "sigma": 4.6299,
    "mean": 28.5652,
    "sd": 9.2597,
    "median": 28.5869,
    "q25": 23.145,
    "q75": 34.3425,
    "n": 80,
    "label_kr": "최대 X-Factor (Hip-Shoulder 분리)",
    "label_en": "Max X-Factor"
  },
  "pelvis_to_trunk_velocity_speedup": {
    "direction": "higher_is_better",
    "unit": "ratio",
    "optimal": 1.5719,
    "sigma": 0.133,
    "mean": 1.4322,
    "sd": 0.266,
    "median": 1.4384,
    "q25": 1.2807,
    "q75": 1.5719,
    "n": 80,
    "label_kr": "골반→트렁크 속도 증폭",
    "label_en": "Pelvis→Trunk Speedup"
  },
  "trunk_to_arm_velocity_speedup": {
    "direction": "higher_is_better",
    "unit": "ratio",
    "optimal": 2.0068,
    "sigma": 0.1741,
    "mean": 1.7466,
    "sd": 0.3481,
    "median": 1.7885,
    "q25": 1.4842,
    "q75": 2.0068,
    "n": 80,
    "label_kr": "트렁크→팔 속도 증폭",
    "label_en": "Trunk→Arm Speedup"
  },
  "on_plane_efficiency": {
    "direction": "higher_is_better",
    "unit": "%",
    "optimal": 87.6558,
    "sigma": 3.613,
    "mean": 83.2155,
    "sd": 7.226,
    "median": 83.4623,
    "q25": 77.6097,
    "q75": 87.6558,
    "n": 80,
    "label_kr": "스윙 플레인 효율",
    "label_en": "On Plane Efficiency"
  },
  "attack_angle": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": 3.2486,
    "sigma": 4.0865,
    "mean": 4.7173,
    "sd": 8.173,
    "median": 3.2486,
    "q25": -0.9719,
    "q75": 9.9656,
    "n": 80,
    "label_kr": "어택 앵글 (Uplift)",
    "label_en": "Attack Angle (Uplift)"
  },
  "hip_hinge": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": 44.6472,
    "sigma": 5.7449,
    "mean": 45.2396,
    "sd": 11.4898,
    "median": 44.6472,
    "q25": 36.8232,
    "q75": 52.0527,
    "n": 80,
    "label_kr": "힙 힌지 (셋업)",
    "label_en": "Hip Hinge"
  },
  "trunk_coil": {
    "direction": "higher_is_better",
    "unit": "deg",
    "optimal": 37.8332,
    "sigma": 6.5453,
    "mean": 29.7721,
    "sd": 13.0906,
    "median": 30.9686,
    "q25": 19.2456,
    "q75": 37.8332,
    "n": 80,
    "label_kr": "트렁크 코일",
    "label_en": "Trunk Coil"
  },
  "linear_stretch": {
    "direction": "higher_is_better",
    "unit": "-",
    "optimal": 0.9367,
    "sigma": 0.0583,
    "mean": 0.8642,
    "sd": 0.1167,
    "median": 0.8706,
    "q25": 0.8036,
    "q75": 0.9367,
    "n": 80,
    "label_kr": "선형 신장 (loading)",
    "label_en": "Linear Stretch"
  },
  "bat_speed_sd_mph": {
    "direction": "lower_is_better",
    "unit": "mph",
    "optimal": 1.8035,
    "sigma": 0.3383,
    "mean": 2.2237,
    "sd": 0.6766,
    "median": 2.1988,
    "q25": 1.8035,
    "q75": 2.5788,
    "n": 80,
    "label_kr": "Bat Speed 일관성 (SD)",
    "label_en": "Bat Speed SD"
  },
  "attack_angle_sd_deg": {
    "direction": "lower_is_better",
    "unit": "deg",
    "optimal": 2.9155,
    "sigma": 0.5524,
    "mean": 3.6833,
    "sd": 1.1048,
    "median": 3.8444,
    "q25": 2.9155,
    "q75": 4.4954,
    "n": 80,
    "label_kr": "어택앵글 일관성 (SD)",
    "label_en": "Attack Angle SD"
  },
  "time_to_contact_sd_s": {
    "direction": "lower_is_better",
    "unit": "s",
    "optimal": 0.0093,
    "sigma": 0.0022,
    "mean": 0.0124,
    "sd": 0.0043,
    "median": 0.0117,
    "q25": 0.0093,
    "q75": 0.0152,
    "n": 80,
    "label_kr": "컨택 타이밍 일관성 (SD)",
    "label_en": "Time to Contact SD"
  },
  "peak_arm_av_sd_dps": {
    "direction": "lower_is_better",
    "unit": "deg/s",
    "optimal": 89.4433,
    "sigma": 22.1374,
    "mean": 119.3876,
    "sd": 44.2747,
    "median": 126.5591,
    "q25": 89.4433,
    "q75": 148.713,
    "n": 80,
    "label_kr": "Peak Arm Vel 일관성 (SD)",
    "label_en": "Peak Arm Vel SD"
  },
  "peak_trunk_av_sd_dps": {
    "direction": "lower_is_better",
    "unit": "deg/s",
    "optimal": 33.9975,
    "sigma": 9.2851,
    "mean": 48.1876,
    "sd": 18.5701,
    "median": 49.7292,
    "q25": 33.9975,
    "q75": 62.4788,
    "n": 80,
    "label_kr": "Peak Trunk Vel 일관성 (SD)",
    "label_en": "Peak Trunk Vel SD"
  },
  "max_x_factor_sd_deg": {
    "direction": "lower_is_better",
    "unit": "deg",
    "optimal": 2.8623,
    "sigma": 0.7241,
    "mean": 3.5123,
    "sd": 1.4482,
    "median": 3.6809,
    "q25": 2.8623,
    "q75": 4.3497,
    "n": 80,
    "label_kr": "X-Factor 일관성 (SD)",
    "label_en": "Max X-Factor SD"
  },
  "blast_bat_speed_mph": {
    "direction": "higher_is_better",
    "unit": "mph",
    "optimal": 68.9946,
    "sigma": 3.4604,
    "mean": 64.6655,
    "sd": 6.9208,
    "median": 64.951,
    "q25": 60.3836,
    "q75": 68.9946,
    "n": 80,
    "label_kr": "Bat Speed (Blast)",
    "label_en": "Bat Speed"
  },
  "blast_peak_hand_speed_mph": {
    "direction": "higher_is_better",
    "unit": "mph",
    "optimal": 22.3466,
    "sigma": 1.2082,
    "mean": 20.6104,
    "sd": 2.4163,
    "median": 20.8598,
    "q25": 19.0692,
    "q75": 22.3466,
    "n": 80,
    "label_kr": "Peak Hand Speed",
    "label_en": "Peak Hand Speed"
  },
  "blast_rotational_acceleration_g": {
    "direction": "higher_is_better",
    "unit": "g",
    "optimal": 16.2045,
    "sigma": 1.5872,
    "mean": 14.1231,
    "sd": 3.1744,
    "median": 14.3122,
    "q25": 11.831,
    "q75": 16.2045,
    "n": 80,
    "label_kr": "회전 가속도",
    "label_en": "Rotational Acceleration"
  },
  "blast_time_to_contact_s": {
    "direction": "lower_is_better",
    "unit": "s",
    "optimal": 0.1416,
    "sigma": 0.0131,
    "mean": 0.1583,
    "sd": 0.0261,
    "median": 0.1587,
    "q25": 0.1416,
    "q75": 0.173,
    "n": 80,
    "label_kr": "Time to Contact",
    "label_en": "Time to Contact"
  },
  "blast_attack_angle_deg": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": 4.2423,
    "sigma": 4.1963,
    "mean": 4.3606,
    "sd": 8.3925,
    "median": 4.2423,
    "q25": -0.783,
    "q75": 9.7934,
    "n": 80,
    "label_kr": "어택 앵글 (Blast)",
    "label_en": "Attack Angle (Blast)"
  },
  "blast_on_plane_efficiency_pct": {
    "direction": "higher_is_better",
    "unit": "%",
    "optimal": 89.3165,
    "sigma": 4.6988,
    "mean": 83.0073,
    "sd": 9.3976,
    "median": 83.7752,
    "q25": 75.9457,
    "q75": 89.3165,
    "n": 80,
    "label_kr": "On Plane Efficiency (Blast)",
    "label_en": "On Plane Efficiency"
  },
  "blast_vertical_bat_angle_deg": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": -33.2006,
    "sigma": 2.6412,
    "mean": -33.1735,
    "sd": 5.2824,
    "median": -33.2006,
    "q25": -36.2892,
    "q75": -29.8082,
    "n": 80,
    "label_kr": "Vertical Bat Angle",
    "label_en": "Vertical Bat Angle"
  },
  "blast_power_kw": {
    "direction": "higher_is_better",
    "unit": "kW",
    "optimal": 4.2881,
    "sigma": 0.3311,
    "mean": 3.8524,
    "sd": 0.6623,
    "median": 3.8923,
    "q25": 3.3915,
    "q75": 4.2881,
    "n": 80,
    "label_kr": "Power",
    "label_en": "Power"
  },
  "blast_early_connection_deg": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": 90.0,
    "sigma": 3.0177,
    "mean": 87.7311,
    "sd": 6.0355,
    "median": 87.7547,
    "q25": 84.0188,
    "q75": 92.6149,
    "n": 80,
    "label_kr": "Early Connection",
    "label_en": "Early Connection"
  },
  "blast_connection_at_impact_deg": {
    "direction": "two_sided",
    "unit": "deg",
    "optimal": 90.0,
    "sigma": 3.0661,
    "mean": 91.0547,
    "sd": 6.1321,
    "median": 90.1194,
    "q25": 87.3951,
    "q75": 95.0165,
    "n": 80,
    "label_kr": "Connection @ Impact",
    "label_en": "Connection @ Impact"
  },
  "grip_strength_kg": {
    "direction": "higher_is_better",
    "unit": "kg",
    "optimal": 54.825,
    "sigma": 3.8074,
    "mean": 49.5625,
    "sd": 7.6149,
    "median": 48.6,
    "q25": 44.7,
    "q75": 54.825,
    "n": 80,
    "label_kr": "악력",
    "label_en": "Grip Strength"
  },
  "cmj_height_cm": {
    "direction": "higher_is_better",
    "unit": "cm",
    "optimal": 50.925,
    "sigma": 3.4434,
    "mean": 47.0538,
    "sd": 6.8868,
    "median": 47.0,
    "q25": 42.0,
    "q75": 50.925,
    "n": 80,
    "label_kr": "CMJ 점프 높이",
    "label_en": "CMJ Height"
  },
  "cmj_pp_bm": {
    "direction": "higher_is_better",
    "unit": "W/kg",
    "optimal": 57.0475,
    "sigma": 3.385,
    "mean": 53.6628,
    "sd": 6.77,
    "median": 54.105,
    "q25": 48.5625,
    "q75": 57.0475,
    "n": 80,
    "label_kr": "CMJ 상대 파워",
    "label_en": "CMJ Peak Power/BM"
  },
  "imtp_pp_bm": {
    "direction": "higher_is_better",
    "unit": "W/kg",
    "optimal": 29.5225,
    "sigma": 1.5844,
    "mean": 28.1028,
    "sd": 3.1688,
    "median": 27.96,
    "q25": 26.2425,
    "q75": 29.5225,
    "n": 80,
    "label_kr": "IMTP 상대 파워",
    "label_en": "IMTP Peak Power/BM"
  },
  "rotation_pp_w_kg": {
    "direction": "higher_is_better",
    "unit": "W/kg",
    "optimal": 7.8575,
    "sigma": 0.6985,
    "mean": 6.9475,
    "sd": 1.397,
    "median": 6.935,
    "q25": 6.1725,
    "q75": 7.8575,
    "n": 80,
    "label_kr": "회전 파워",
    "label_en": "Rotational Power"
  },
  "sprint_30m_s": {
    "direction": "lower_is_better",
    "unit": "s",
    "optimal": 4.1375,
    "sigma": 0.1308,
    "mean": 4.3216,
    "sd": 0.2616,
    "median": 4.35,
    "q25": 4.1375,
    "q75": 4.49,
    "n": 80,
    "label_kr": "30m 스프린트",
    "label_en": "30m Sprint"
  },
  "broad_jump_cm": {
    "direction": "higher_is_better",
    "unit": "cm",
    "optimal": 261.475,
    "sigma": 12.2375,
    "mean": 247.5025,
    "sd": 24.4749,
    "median": 245.55,
    "q25": 233.875,
    "q75": 261.475,
    "n": 80,
    "label_kr": "제자리 멀리뛰기",
    "label_en": "Broad Jump"
  },
  "height_cm": {
    "direction": "higher_is_better",
    "unit": "cm",
    "optimal": 183.875,
    "sigma": 3.4588,
    "mean": 179.3688,
    "sd": 6.9176,
    "median": 178.65,
    "q25": 174.375,
    "q75": 183.875,
    "n": 80,
    "label_kr": "신장",
    "label_en": "Height"
  },
  "weight_kg": {
    "direction": "two_sided",
    "unit": "kg",
    "optimal": 79.5,
    "sigma": 4.3305,
    "mean": 79.9175,
    "sd": 8.661,
    "median": 79.5,
    "q25": 73.475,
    "q75": 85.225,
    "n": 80,
    "label_kr": "체중",
    "label_en": "Weight"
  }
};

const FAULT_LABELS = {
  "fault_drifting_forward": {
    "kr": "Drifting Forward (앞으로 흘러나감)",
    "severity": "high"
  },
  "fault_excessive_lateral_pelvis_tilt": {
    "kr": "과도한 측방 골반 기울기",
    "severity": "med"
  },
  "fault_knee_dominant_swing": {
    "kr": "Knee Dominant Swing (무릎 의존)",
    "severity": "high"
  },
  "fault_vertical_pelvis_hike": {
    "kr": "골반 수직 하이크 (vertical hike)",
    "severity": "med"
  },
  "fault_sway_leg": {
    "kr": "Sway Leg (뒷다리 흔들림)",
    "severity": "med"
  },
  "fault_leads_with_wrist": {
    "kr": "Leads with Wrist (손목 선행)",
    "severity": "high"
  },
  "fault_rear_elbow_drag": {
    "kr": "Rear Elbow Drag (뒤팔꿈치 끌림)",
    "severity": "high"
  },
  "fault_hand_push": {
    "kr": "Hand Push (손 밀기)",
    "severity": "med"
  },
  "fault_crashing": {
    "kr": "Crashing (자세 무너짐)",
    "severity": "high"
  }
};

const BAT_SPEED_REGRESSION = {
  "model": "BAT_SPEED_REGRESSION_v1",
  "target": "bat_speed_mph",
  "predictors": [
    "upper_arm_rotation_velo_at_swing_dps",
    "torso_rotation_velo_at_swing_dps",
    "cog_decel_mps",
    "max_x_factor",
    "pelvis_to_trunk_velocity_speedup",
    "on_plane_efficiency",
    "grip_strength_kg",
    "cmj_pp_bm",
    "rotation_pp_w_kg",
    "height_cm"
  ],
  "intercept": -4.413976,
  "coefs": {
    "upper_arm_rotation_velo_at_swing_dps": 0.008317,
    "torso_rotation_velo_at_swing_dps": 0.017434,
    "cog_decel_mps": 2.170402,
    "max_x_factor": 0.118384,
    "pelvis_to_trunk_velocity_speedup": 3.144055,
    "on_plane_efficiency": 0.156383,
    "grip_strength_kg": 0.07399,
    "cmj_pp_bm": 0.06589,
    "rotation_pp_w_kg": 0.516242,
    "height_cm": 0.041837
  },
  "beta_standardized": {
    "upper_arm_rotation_velo_at_swing_dps": 0.3927,
    "torso_rotation_velo_at_swing_dps": 0.294,
    "cog_decel_mps": 0.0999,
    "max_x_factor": 0.1584,
    "pelvis_to_trunk_velocity_speedup": 0.1208,
    "on_plane_efficiency": 0.1633,
    "grip_strength_kg": 0.0814,
    "cmj_pp_bm": 0.0645,
    "rotation_pp_w_kg": 0.1042,
    "height_cm": 0.0418
  },
  "R2": 0.8357,
  "adj_R2": 0.8119,
  "LOO_CV_R2": 0.7736,
  "n": 80,
  "predictor_means": {
    "upper_arm_rotation_velo_at_swing_dps": 1484.5847,
    "torso_rotation_velo_at_swing_dps": 871.3175,
    "cog_decel_mps": 1.0825,
    "max_x_factor": 28.5652,
    "pelvis_to_trunk_velocity_speedup": 1.4322,
    "on_plane_efficiency": 83.2155,
    "grip_strength_kg": 49.5625,
    "cmj_pp_bm": 53.6628,
    "rotation_pp_w_kg": 6.9475,
    "height_cm": 179.3688
  },
  "predictor_sds": {
    "upper_arm_rotation_velo_at_swing_dps": 326.819,
    "torso_rotation_velo_at_swing_dps": 116.7183,
    "cog_decel_mps": 0.3187,
    "max_x_factor": 9.2597,
    "pelvis_to_trunk_velocity_speedup": 0.266,
    "on_plane_efficiency": 7.226,
    "grip_strength_kg": 7.6149,
    "cmj_pp_bm": 6.77,
    "rotation_pp_w_kg": 1.397,
    "height_cm": 6.9176
  }
};


// =====================================================================
// 점수 함수 (Gaussian + percentile hybrid)
// =====================================================================
// 투수 리포트의 LITERATURE_OVERRIDE + Gaussian 점수와 동일 철학:
//   - direction='higher_is_better': 값이 클수록 점수 높음 → 코호트 percentile 사용
//   - direction='lower_is_better':  값이 작을수록 점수 높음 → (100 - percentile) 사용
//   - direction='two_sided':        optimal 근처가 만점 → Gaussian 점수
//
function scoreVariable(varKey, value) {
  if (value == null || isNaN(value)) return null;
  const m = VARIABLE_METADATA[varKey];
  if (!m) return null;
  const dir = m.direction;

  if (dir === 'higher_is_better' || dir === 'lower_is_better') {
    // percentile 기반: 값이 코호트 분포에서 어디 위치하는지
    // 정확한 percentile은 cohort 데이터를 따로 로드해야 하지만,
    // 여기서는 mean·sd 기반 z-score → 정규분포 근사 percentile 사용
    const z = (value - m.mean) / m.sd;
    let pct = 100 * normCdf(z);
    if (dir === 'lower_is_better') pct = 100 - pct;
    return Math.max(0, Math.min(100, pct));
  }
  if (dir === 'two_sided') {
    // Gaussian: optimal에서 멀어질수록 점수 하락
    const z = (value - m.optimal) / m.sigma;
    return 100 * Math.exp(-0.5 * z * z);
  }
  return null;
}

// 표준 정규분포 누적분포함수 (Abramowitz-Stegun 근사, 충분히 정확)
function normCdf(z) {
  const t = 1 / (1 + 0.2316419 * Math.abs(z));
  const d = 0.3989423 * Math.exp(-z * z / 2);
  let p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
  return z > 0 ? 1 - p : p;
}


// =====================================================================
// Bat Speed 예측 함수
// =====================================================================
function predictBatSpeed(values) {
  // values: object mapping variable_key to numeric value
  // 결측 시 코호트 mean으로 imputation
  let result = BAT_SPEED_REGRESSION.intercept;
  for (const p of BAT_SPEED_REGRESSION.predictors) {
    let v = values[p];
    if (v == null || isNaN(v)) {
      v = BAT_SPEED_REGRESSION.predictor_means[p];
    }
    result += BAT_SPEED_REGRESSION.coefs[p] * v;
  }
  return result;
}
