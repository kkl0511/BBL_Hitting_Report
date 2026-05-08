"""
extract_uplift_batting_scalars.py
=================================
Uplift 타격 raw CSV(시계열) → per-session 스칼라 변수로 변환

투수 리포트의 extract_uplift_scalars.py와 동일한 역할이며,
타격에 맞춰 Driveline "Hitting Mechanical Composite Scores+" 14변수 +
Uplift 자체 산출 스칼라(attack_angle, on_plane_efficiency 등) +
CoG 모델 변수(max_cog_velo, cog_decel) 모두 추출한다.

사용법:
    python extract_uplift_batting_scalars.py <uplift_csv_path> [output_csv_path]

출력: per-session scalar CSV (1 row per session)
"""

import sys
import os
import numpy as np
import pandas as pd


# =========================================================================
# 1. Event frame 정규화
# =========================================================================
def get_event_frame(df, col):
    """
    Uplift CSV에 event 프레임이 음수로 저장되어 있다.
    e.g. foot_contact_frame = -329  →  실제 frame 329
    
    abs() 해서 실제 frame 인덱스로 변환한다.
    """
    if col not in df.columns:
        return None
    val = df[col].dropna()
    if len(val) == 0:
        return None
    f = int(abs(val.iloc[0]))
    # frame이 데이터 범위를 벗어나면 None
    if f < 0 or f >= len(df):
        return None
    return f


# =========================================================================
# 2. 타격 이벤트 윈도우 정의
# =========================================================================
def get_event_windows(df):
    """
    타격 동작 이벤트 프레임을 추출하고 분석 윈도우를 정의한다.
    
    일반적인 타격 sequence:
      max_foot_raise (앞발 최고 들기)
      → pelvis_initiation (골반 회전 시작)
      → max_x_factor (Hip-Shoulder 분리 최대)
      → foot_contact (앞발 착지, FP)
      → peak velocities (golf-like sequence)
      → ball_contact (볼 임팩트, BC)
    
    Driveline 모델의 분석 구간:
      - "@ Stride"  = max_foot_raise ~ FP (스트라이드 단계)
      - "@ FP"      = FP 시점의 1-frame 값
      - "@ Swing" / "@ Down Swing" = FP ~ BC (스윙 단계)
    """
    events = {
        'max_foot_raise':    get_event_frame(df, 'max_foot_raise_frame'),
        'pelvis_initiation': get_event_frame(df, 'pelvis_initiation_frame'),
        'wrist_init':        get_event_frame(df, 'wrist_movement_initiation_frame'),
        'max_x_factor':      get_event_frame(df, 'max_x_factor_frame'),
        'foot_contact':      get_event_frame(df, 'foot_contact_frame'),
        'ball_contact':      get_event_frame(df, 'ball_contact_frame'),
    }
    
    # Stride 윈도우: max_foot_raise → foot_contact
    if events['max_foot_raise'] is not None and events['foot_contact'] is not None:
        events['stride_window'] = (events['max_foot_raise'], events['foot_contact'])
    elif events['pelvis_initiation'] is not None and events['foot_contact'] is not None:
        # max_foot_raise가 없으면 pelvis_initiation으로 대체
        events['stride_window'] = (events['pelvis_initiation'], events['foot_contact'])
    else:
        events['stride_window'] = None
    
    # Swing 윈도우: foot_contact → ball_contact
    if events['foot_contact'] is not None and events['ball_contact'] is not None:
        events['swing_window'] = (events['foot_contact'], events['ball_contact'])
    else:
        events['swing_window'] = None
    
    return events


# =========================================================================
# 3. 헬퍼 함수
# =========================================================================
def safe_value_at_frame(df, col, frame):
    """특정 frame에서 컬럼 값 반환 (NaN-safe)"""
    if frame is None or col not in df.columns:
        return np.nan
    if frame < 0 or frame >= len(df):
        return np.nan
    return float(df[col].iloc[frame])


def safe_max_in_window(df, col, window):
    """윈도우 구간에서 컬럼의 최대값 (절대값 기준 — 회전속도 등 부호 무관)"""
    if window is None or col not in df.columns:
        return np.nan
    s, e = window
    if s is None or e is None:
        return np.nan
    if s > e:
        s, e = e, s
    seg = df[col].iloc[s:e+1].abs()
    return float(seg.max()) if len(seg) > 0 else np.nan


def safe_max_signed_in_window(df, col, window):
    """윈도우 구간에서 컬럼의 최대값 (부호 포함)"""
    if window is None or col not in df.columns:
        return np.nan
    s, e = window
    if s is None or e is None:
        return np.nan
    if s > e:
        s, e = e, s
    seg = df[col].iloc[s:e+1]
    return float(seg.max()) if len(seg) > 0 else np.nan


# =========================================================================
# 4. CoG 변수 (전체 신체 무게중심)
# =========================================================================
def compute_cog_metrics(df, events):
    """
    CoG 카테고리 변수를 시계열에서 계산한다.
    
    CoG 변수:
      - Max CoG Velo @ Stride: stride 구간 내 무게중심 수평속도 최대
      - Max CoG Velo: 전 구간 무게중심 수평속도 최대
      - CoG Decel: 최고속도 → 그 이후 최저속도까지의 감속량
                   (전방 방향, Driveline 모델의 핵심 변수 — 강한 감속이 elite 신호)
    
    좌표계: x = 투수쪽 전후, y = 좌우, z = 수직
            (정확한 좌표계 확인 필요시 visualize 후 검증 권장)
    """
    fps = float(df['fps'].iloc[0])
    dt = 1.0 / fps
    
    cog_x = df['whole_body_center_of_mass_x'].values
    cog_y = df['whole_body_center_of_mass_y'].values
    
    # 수평면 속도 (vertical 제외 — 무게중심 전진 평가에 적합)
    vx = np.gradient(cog_x, dt)
    vy = np.gradient(cog_y, dt)
    v_horizontal = np.sqrt(vx**2 + vy**2)
    
    # 노이즈 완화를 위해 5-frame moving avg
    if len(v_horizontal) >= 5:
        kernel = np.ones(5) / 5
        v_smooth = np.convolve(v_horizontal, kernel, mode='same')
    else:
        v_smooth = v_horizontal
    
    out = {}
    
    # Max CoG Velo @ Stride
    sw = events['stride_window']
    if sw is not None and sw[0] is not None and sw[1] is not None:
        s, e = sw
        if s > e:
            s, e = e, s
        out['max_cog_velo_at_stride_mps'] = float(v_smooth[s:e+1].max())
    else:
        out['max_cog_velo_at_stride_mps'] = np.nan
    
    # Max CoG Velo (전체)
    out['max_cog_velo_mps'] = float(v_smooth.max())
    
    # CoG Decel: max velocity → 그 이후 min velocity 차이
    # (앞발 착지 후 무게중심이 빠르게 감속하는 정도 — block & rotate)
    peak_idx = int(v_smooth.argmax())
    if peak_idx < len(v_smooth) - 1:
        post_peak = v_smooth[peak_idx:]
        min_after = float(post_peak.min())
        out['cog_decel_mps'] = float(v_smooth[peak_idx]) - min_after
    else:
        out['cog_decel_mps'] = np.nan
    
    return out


# =========================================================================
# 5. 메인 추출 함수
# =========================================================================
def extract_session_scalars(df):
    """
    하나의 session(=한 스윙)의 시계열 DataFrame을 받아
    스칼라 변수 dict를 반환한다.
    """
    out = {}
    
    # ---------- 5.1 메타데이터 ----------
    meta_cols = ['athlete_name', 'athleteid', 'sessionid', 'session_uuid', 'session_seq',
                 'capture_datetime', 'fps', 'handedness', 'footedness',
                 'approved_by_biomech_qa']
    for col in meta_cols:
        if col in df.columns:
            v = df[col].dropna()
            out[col] = v.iloc[0] if len(v) > 0 else None
    
    out['n_frames'] = len(df)
    out['duration_s'] = float(df['time'].iloc[-1] - df['time'].iloc[0]) if 'time' in df.columns else None
    
    # ---------- 5.2 이벤트 프레임 ----------
    events = get_event_windows(df)
    out['frame_max_foot_raise'] = events['max_foot_raise']
    out['frame_pelvis_initiation'] = events['pelvis_initiation']
    out['frame_max_x_factor'] = events['max_x_factor']
    out['frame_foot_contact'] = events['foot_contact']
    out['frame_ball_contact'] = events['ball_contact']
    
    # 핸드니스 결정 — rear arm = dominant (오른손 타자는 right 어깨가 rear)
    handedness = (out.get('handedness') or 'right').lower()
    rear_side = handedness  # 'right' or 'left'
    lead_side = 'left' if rear_side == 'right' else 'right'
    
    fp = events['foot_contact']
    bc = events['ball_contact']
    sw = events['stride_window']
    swing_w = events['swing_window']
    
    # ---------- 5.3 Driveline 카테고리 1: Stride Posture ----------
    # NOTE: Driveline 변수 정의 핵심
    #   "Max Pelvis Rotation @ Stride" = stride 동안 골반이 회전한 "양"(Δ)이지
    #     절대 좌표계의 yaw 값이 아님. (elite 중간값 9° = 작은 회전량)
    #   "Torso Rotation @ FP" = FP 시점에서 trunk가 pelvis 대비 얼마나 회전했는지
    #     (음수 = closed). 즉 X-factor 부호 포함값.
    
    # Max Pelvis Rotation @ Stride: stride 구간에서 pelvis_global_rotation 변화량(Δ)
    if sw is not None and sw[0] is not None and sw[1] is not None:
        s, e = sw
        if s > e: s, e = e, s
        seg = df['pelvis_global_rotation'].iloc[s:e+1]
        out['max_pelvis_rotation_at_stride_deg'] = float(seg.max() - seg.min())
    else:
        out['max_pelvis_rotation_at_stride_deg'] = np.nan
    
    # Torso Rotation @ FP: FP 시점의 trunk - pelvis 회전 차이 (X-factor 부호 포함)
    # closed stance면 trunk가 pelvis보다 덜 회전 → 음수
    trunk_fp = safe_value_at_frame(df, 'trunk_global_rotation', fp)
    pelvis_fp = safe_value_at_frame(df, 'pelvis_global_rotation', fp)
    if not (np.isnan(trunk_fp) or np.isnan(pelvis_fp)):
        out['torso_rotation_at_fp_deg'] = float(trunk_fp - pelvis_fp)
    else:
        out['torso_rotation_at_fp_deg'] = np.nan
    
    # Rear Shoulder Adduction @ FP: rear arm의 어깨 내전 각도
    out['rear_shoulder_adduction_at_fp_deg'] = safe_value_at_frame(
        df, f'{rear_side}_shoulder_adduction', fp)
    
    # Lead Hip Posterior Tilt @ FP: pelvis_global_tilt를 prox로 사용
    # (정확히는 lead hip의 pelvic-tilt angle. Uplift CSV에는 직접 변수 없어 pelvis_tilt로 대체)
    out['lead_hip_posterior_tilt_at_fp_deg'] = safe_value_at_frame(df, 'pelvis_global_tilt', fp)
    
    # ---------- 5.4 Driveline 카테고리 2: Stride Rotation ----------
    out['max_pelvis_rotation_velo_at_stride_dps'] = safe_max_in_window(
        df, 'pelvis_rotational_velocity_with_respect_to_ground', sw)
    out['max_torso_rotation_velo_at_stride_dps'] = safe_max_in_window(
        df, 'trunk_rotational_velocity_with_respect_to_ground', sw)
    
    # ---------- 5.5 Driveline 카테고리 3: Swing Posture ----------
    # Pelvis Rotation @ Swing: FP→BC 사이 골반 회전량(차이값)
    if fp is not None and bc is not None:
        rot_fp = safe_value_at_frame(df, 'pelvis_global_rotation', fp)
        rot_bc = safe_value_at_frame(df, 'pelvis_global_rotation', bc)
        if not (np.isnan(rot_fp) or np.isnan(rot_bc)):
            out['pelvis_rotation_at_swing_deg'] = float(abs(rot_bc - rot_fp))
        else:
            out['pelvis_rotation_at_swing_deg'] = np.nan
    else:
        out['pelvis_rotation_at_swing_deg'] = np.nan
    
    # Lead Hip Posterior Tilt @ Swing
    out['lead_hip_posterior_tilt_at_swing_deg'] = safe_value_at_frame(df, 'pelvis_global_tilt', bc)
    
    # Lead Hip Adduction @ FP / @ Down Swing
    out['lead_hip_adduction_at_fp_deg'] = safe_value_at_frame(
        df, f'{lead_side}_hip_adduction_with_respect_to_pelvis', fp)
    out['lead_hip_adduction_at_swing_deg'] = safe_value_at_frame(
        df, f'{lead_side}_hip_adduction_with_respect_to_pelvis', bc)
    
    # ---------- 5.6 Driveline 카테고리 4: Swing Rotation ----------
    out['pelvis_rotation_velo_at_swing_dps'] = safe_max_in_window(
        df, 'pelvis_rotational_velocity_with_respect_to_ground', swing_w)
    out['torso_rotation_velo_at_swing_dps'] = safe_max_in_window(
        df, 'trunk_rotational_velocity_with_respect_to_ground', swing_w)
    # Upper Arm rotational velocity (rear arm 기준)
    out['upper_arm_rotation_velo_at_swing_dps'] = safe_max_in_window(
        df, f'{rear_side}_arm_rotational_velocity_with_respect_to_ground', swing_w)
    
    # ---------- 5.7 Driveline 카테고리 5: CoG ----------
    cog = compute_cog_metrics(df, events)
    out.update(cog)
    
    # ---------- 5.8 Uplift 자체 산출 스칼라 (이미 계산된 값 그대로 읽기) ----------
    direct_scalars = [
        # 회전 속도 peak (전체 구간)
        'peak_pelvis_angular_velocity', 'peak_trunk_angular_velocity', 'peak_arm_angular_velocity',
        # X-Factor
        'max_x_factor',
        # Speedup
        'pelvis_to_trunk_velocity_speedup', 'trunk_to_arm_velocity_speedup',
        # Stance / Setup
        'hip_hinge', 'trunk_coil', 'trunk_tilt_at_launch', 'rear_scap_load_at_launch',
        # Arm
        'rear_elbow_flexion_at_launch', 'rear_elbow_flexion_at_ball_contact',
        'rear_arm_connection', 'inter_elbow_distance',
        # Lower body
        'lead_knee_angle_at_ball_contact', 'stride_length',
        # Hand
        'shoulder_rotation_plane_flexion', 'shoulder_rotation_plane_tilt',
        'relative_hand_position_towards_pitcher', 'relative_hand_position_up',
        'relative_hand_position_away_from_body',
        # 스트레치 (loading)
        'linear_stretch',
        # Swing 결과 (Bat 미센서, Uplift 추정)
        'attack_angle', 'attack_direction', 'launch_position',
        'sweet_spot_fore_aft_position_at_contact',
        'on_plane_efficiency', 'swing_path_angle',
        # 시간
        'pelvis_acceleration_time', 'pelvis_decceleration_time',
        'time_to_ball_contact', 'time_to_launch',
        # 키네마틱 시퀀스 정확도
        'kinematic_sequence_order',
    ]
    for col in direct_scalars:
        if col in df.columns:
            v = df[col].dropna()
            if len(v) > 0:
                try:
                    out[col] = float(v.iloc[0])
                except (ValueError, TypeError):
                    # 문자열형(kinematic_sequence_order = 'Pelvis-Trunk-Arm' 등)은 그대로 저장
                    out[col] = str(v.iloc[0])
            else:
                out[col] = np.nan
    
    # 키네마틱 시퀀스 정확도: 'Pelvis-Trunk-Arm' = proper, 그 외 = improper
    if 'kinematic_sequence_order' in out:
        ks = out['kinematic_sequence_order']
        out['proper_sequence_binary'] = 1 if (isinstance(ks, str) and ks.strip().lower() == 'pelvis-trunk-arm') else 0
    
    # ---------- 5.9 결함 플래그 (Uplift 자체 판정) ----------
    fault_cols = [
        'sway', 'knee_dominant_swing', 'vertical_pelvis_hike',
        'excessive_lateral_pelvis_tilt', 'drifting_forward', 'sway_leg',
        'leads_with_wrist', 'rear_elbow_drag', 'hand_push', 'crashing',
    ]
    for col in fault_cols:
        if col in df.columns:
            v = df[col].dropna()
            if len(v) > 0:
                # 0/1 binary 또는 정도값으로 저장 — 그대로 사용
                try:
                    out[f'fault_{col}'] = float(v.iloc[0])
                except (ValueError, TypeError):
                    out[f'fault_{col}'] = None
            else:
                out[f'fault_{col}'] = np.nan
    
    # drifting_forward의 magnitude (정도)
    if 'drifting_forward_magnitude' in df.columns:
        v = df['drifting_forward_magnitude'].dropna()
        out['drifting_forward_magnitude'] = float(v.iloc[0]) if len(v) > 0 else np.nan
    
    return out


# =========================================================================
# 6. 메인 실행부
# =========================================================================
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    csv_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) >= 3 else 'bbl_batting_per_session.csv'
    
    print(f"Reading: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"  {len(df)} rows × {len(df.columns)} cols")
    
    # session 단위로 그룹핑 (CSV에 여러 session이 있을 수 있음)
    if 'sessionid' in df.columns and df['sessionid'].nunique() > 1:
        sessions = df.groupby('sessionid')
        rows = []
        for sid, sdf in sessions:
            print(f"  → session {sid} ({len(sdf)} frames)")
            rows.append(extract_session_scalars(sdf))
        out_df = pd.DataFrame(rows)
    else:
        # 단일 session
        scalars = extract_session_scalars(df)
        out_df = pd.DataFrame([scalars])
    
    out_df.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")
    print(f"  → {len(out_df)} sessions × {len(out_df.columns)} scalars")
    
    # 요약 출력
    print("\n=== Extracted Driveline-style scalars ===")
    key_vars = [
        'max_pelvis_rotation_at_stride_deg', 'torso_rotation_at_fp_deg',
        'rear_shoulder_adduction_at_fp_deg', 'lead_hip_posterior_tilt_at_fp_deg',
        'max_pelvis_rotation_velo_at_stride_dps', 'max_torso_rotation_velo_at_stride_dps',
        'pelvis_rotation_at_swing_deg',
        'pelvis_rotation_velo_at_swing_dps', 'torso_rotation_velo_at_swing_dps',
        'upper_arm_rotation_velo_at_swing_dps',
        'max_cog_velo_at_stride_mps', 'max_cog_velo_mps', 'cog_decel_mps',
        'peak_pelvis_angular_velocity', 'peak_trunk_angular_velocity',
        'peak_arm_angular_velocity', 'max_x_factor',
        'attack_angle', 'on_plane_efficiency', 'hip_hinge', 'trunk_coil',
    ]
    for v in key_vars:
        if v in out_df.columns:
            val = out_df[v].iloc[0]
            if isinstance(val, (int, float)):
                print(f"  {v:50s} = {val:.3f}")
            else:
                print(f"  {v:50s} = {val}")


if __name__ == '__main__':
    main()
