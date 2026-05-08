"""
build_js_files.py
=================
Python으로 생성한 JSON(분포·회귀·variable_metadata)을 읽어
브라우저에서 사용할 JS 파일을 생성한다.

생성 파일:
  - metadata_batting.js  : 변수 metadata + 회귀 모델 + 변수 라벨/단위
  - cohort_batting.js    : 카테고리(B1~B6, F) 매핑 + 변수→카테고리 가중치
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'
OUT_DIR = Path(__file__).parent

with open(DATA_DIR / 'variable_metadata.json', 'r', encoding='utf-8') as f:
    var_meta = json.load(f)
with open(DATA_DIR / 'bat_speed_regression.json', 'r', encoding='utf-8') as f:
    reg = json.load(f)
with open(DATA_DIR / 'cohort_distributions.json', 'r', encoding='utf-8') as f:
    cohort_dist = json.load(f)


# ============================================================================
# 변수 라벨 (한글) — 리포트 UI에 표시될 이름
# ============================================================================
VAR_LABELS = {
    # Driveline Stride Posture
    'max_pelvis_rotation_at_stride_deg':    {'kr': 'Stride 중 골반 회전량',         'en': 'Max Pelvis Rotation @ Stride'},
    'torso_rotation_at_fp_deg':             {'kr': 'FP 시점 트렁크 회전(X-factor)', 'en': 'Torso Rotation @ FP'},
    'rear_shoulder_adduction_at_fp_deg':    {'kr': 'FP 시점 뒤쪽 어깨 내전',        'en': 'Rear Shoulder Adduction @ FP'},
    'lead_hip_posterior_tilt_at_fp_deg':    {'kr': 'FP 시점 골반 후방경사',         'en': 'Lead Hip Posterior Tilt @ FP'},
    # Stride Rotation
    'max_pelvis_rotation_velo_at_stride_dps': {'kr': 'Stride 중 골반 최고 회전속도',   'en': 'Max Pelvis Rot Velo @ Stride'},
    'max_torso_rotation_velo_at_stride_dps':  {'kr': 'Stride 중 트렁크 최고 회전속도', 'en': 'Max Torso Rot Velo @ Stride'},
    # Swing Posture
    'pelvis_rotation_at_swing_deg':         {'kr': 'Down Swing 중 골반 회전량',      'en': 'Pelvis Rotation @ Swing'},
    'lead_hip_posterior_tilt_at_swing_deg': {'kr': 'BC 시점 골반 후방경사',          'en': 'Lead Hip Posterior Tilt @ Swing'},
    'lead_hip_adduction_at_fp_deg':         {'kr': 'FP 시점 리드 고관절 내전',       'en': 'Lead Hip Adduction @ FP'},
    'lead_hip_adduction_at_swing_deg':      {'kr': 'Down Swing 중 리드 고관절 내전', 'en': 'Lead Hip Adduction @ Swing'},
    # Swing Rotation
    'pelvis_rotation_velo_at_swing_dps':    {'kr': 'Down Swing 골반 회전속도',       'en': 'Pelvis Rot Velo @ Swing'},
    'torso_rotation_velo_at_swing_dps':     {'kr': 'Down Swing 트렁크 회전속도',     'en': 'Torso Rot Velo @ Swing'},
    'upper_arm_rotation_velo_at_swing_dps': {'kr': 'Down Swing 상완 회전속도',       'en': 'Upper Arm Rot Velo @ Swing'},
    # CoG
    'max_cog_velo_at_stride_mps':           {'kr': 'Stride 중 무게중심 최고속도',    'en': 'Max CoG Velo @ Stride'},
    'max_cog_velo_mps':                     {'kr': '무게중심 최고속도 (전구간)',     'en': 'Max CoG Velo'},
    'cog_decel_mps':                        {'kr': '무게중심 감속량 (FP 후 block)',  'en': 'CoG Decel'},
    # Uplift extras
    'max_x_factor':                         {'kr': '최대 X-Factor (Hip-Shoulder 분리)', 'en': 'Max X-Factor'},
    'pelvis_to_trunk_velocity_speedup':     {'kr': '골반→트렁크 속도 증폭',          'en': 'Pelvis→Trunk Speedup'},
    'trunk_to_arm_velocity_speedup':        {'kr': '트렁크→팔 속도 증폭',            'en': 'Trunk→Arm Speedup'},
    'on_plane_efficiency':                  {'kr': '스윙 플레인 효율',               'en': 'On Plane Efficiency'},
    'attack_angle':                         {'kr': '어택 앵글 (Uplift)',             'en': 'Attack Angle (Uplift)'},
    'hip_hinge':                            {'kr': '힙 힌지 (셋업)',                 'en': 'Hip Hinge'},
    'trunk_coil':                           {'kr': '트렁크 코일',                    'en': 'Trunk Coil'},
    'linear_stretch':                       {'kr': '선형 신장 (loading)',            'en': 'Linear Stretch'},
    # SD
    'bat_speed_sd_mph':                     {'kr': 'Bat Speed 일관성 (SD)',          'en': 'Bat Speed SD'},
    'attack_angle_sd_deg':                  {'kr': '어택앵글 일관성 (SD)',           'en': 'Attack Angle SD'},
    'time_to_contact_sd_s':                 {'kr': '컨택 타이밍 일관성 (SD)',        'en': 'Time to Contact SD'},
    'peak_arm_av_sd_dps':                   {'kr': 'Peak Arm Vel 일관성 (SD)',       'en': 'Peak Arm Vel SD'},
    'peak_trunk_av_sd_dps':                 {'kr': 'Peak Trunk Vel 일관성 (SD)',     'en': 'Peak Trunk Vel SD'},
    'max_x_factor_sd_deg':                  {'kr': 'X-Factor 일관성 (SD)',           'en': 'Max X-Factor SD'},
    # Blast Motion
    'blast_bat_speed_mph':                  {'kr': 'Bat Speed (Blast)',              'en': 'Bat Speed'},
    'blast_peak_hand_speed_mph':            {'kr': 'Peak Hand Speed',                'en': 'Peak Hand Speed'},
    'blast_rotational_acceleration_g':      {'kr': '회전 가속도',                    'en': 'Rotational Acceleration'},
    'blast_time_to_contact_s':              {'kr': 'Time to Contact',                'en': 'Time to Contact'},
    'blast_attack_angle_deg':               {'kr': '어택 앵글 (Blast)',              'en': 'Attack Angle (Blast)'},
    'blast_on_plane_efficiency_pct':        {'kr': 'On Plane Efficiency (Blast)',    'en': 'On Plane Efficiency'},
    'blast_vertical_bat_angle_deg':         {'kr': 'Vertical Bat Angle',             'en': 'Vertical Bat Angle'},
    'blast_power_kw':                       {'kr': 'Power',                          'en': 'Power'},
    'blast_early_connection_deg':           {'kr': 'Early Connection',               'en': 'Early Connection'},
    'blast_connection_at_impact_deg':       {'kr': 'Connection @ Impact',            'en': 'Connection @ Impact'},
    # 체력
    'grip_strength_kg':    {'kr': '악력',           'en': 'Grip Strength'},
    'cmj_height_cm':       {'kr': 'CMJ 점프 높이',  'en': 'CMJ Height'},
    'cmj_pp_bm':           {'kr': 'CMJ 상대 파워',  'en': 'CMJ Peak Power/BM'},
    'imtp_pp_bm':          {'kr': 'IMTP 상대 파워', 'en': 'IMTP Peak Power/BM'},
    'rotation_pp_w_kg':    {'kr': '회전 파워',      'en': 'Rotational Power'},
    'sprint_30m_s':        {'kr': '30m 스프린트',   'en': '30m Sprint'},
    'broad_jump_cm':       {'kr': '제자리 멀리뛰기', 'en': 'Broad Jump'},
    'height_cm':           {'kr': '신장',           'en': 'Height'},
    'weight_kg':           {'kr': '체중',           'en': 'Weight'},
}

# 변수 metadata에 라벨 추가
for v in var_meta:
    if v in VAR_LABELS:
        var_meta[v]['label_kr'] = VAR_LABELS[v]['kr']
        var_meta[v]['label_en'] = VAR_LABELS[v]['en']


# ============================================================================
# Fault 라벨
# ============================================================================
FAULT_LABELS = {
    'fault_drifting_forward':            {'kr': 'Drifting Forward (앞으로 흘러나감)', 'severity': 'high'},
    'fault_excessive_lateral_pelvis_tilt': {'kr': '과도한 측방 골반 기울기', 'severity': 'med'},
    'fault_knee_dominant_swing':         {'kr': 'Knee Dominant Swing (무릎 의존)', 'severity': 'high'},
    'fault_vertical_pelvis_hike':        {'kr': '골반 수직 하이크 (vertical hike)', 'severity': 'med'},
    'fault_sway_leg':                    {'kr': 'Sway Leg (뒷다리 흔들림)', 'severity': 'med'},
    'fault_leads_with_wrist':            {'kr': 'Leads with Wrist (손목 선행)', 'severity': 'high'},
    'fault_rear_elbow_drag':             {'kr': 'Rear Elbow Drag (뒤팔꿈치 끌림)', 'severity': 'high'},
    'fault_hand_push':                   {'kr': 'Hand Push (손 밀기)', 'severity': 'med'},
    'fault_crashing':                    {'kr': 'Crashing (자세 무너짐)', 'severity': 'high'},
}


# ============================================================================
# metadata_batting.js 생성
# ============================================================================
def js_dump(obj):
    """Python dict → JS object literal (JSON 호환 포맷)"""
    return json.dumps(obj, ensure_ascii=False, indent=2)


metadata_js = f"""// metadata_batting.js
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

const COHORT_INFO = {{
  n_total: {cohort_dist['n_total']},
  source: 'synthetic_v1 (placeholder until real data accumulated)',
}};

const VARIABLE_METADATA = {js_dump(var_meta)};

const FAULT_LABELS = {js_dump(FAULT_LABELS)};

const BAT_SPEED_REGRESSION = {js_dump(reg)};


// =====================================================================
// 점수 함수 (Gaussian + percentile hybrid)
// =====================================================================
// 투수 리포트의 LITERATURE_OVERRIDE + Gaussian 점수와 동일 철학:
//   - direction='higher_is_better': 값이 클수록 점수 높음 → 코호트 percentile 사용
//   - direction='lower_is_better':  값이 작을수록 점수 높음 → (100 - percentile) 사용
//   - direction='two_sided':        optimal 근처가 만점 → Gaussian 점수
//
function scoreVariable(varKey, value) {{
  if (value == null || isNaN(value)) return null;
  const m = VARIABLE_METADATA[varKey];
  if (!m) return null;
  const dir = m.direction;

  if (dir === 'higher_is_better' || dir === 'lower_is_better') {{
    // percentile 기반: 값이 코호트 분포에서 어디 위치하는지
    // 정확한 percentile은 cohort 데이터를 따로 로드해야 하지만,
    // 여기서는 mean·sd 기반 z-score → 정규분포 근사 percentile 사용
    const z = (value - m.mean) / m.sd;
    let pct = 100 * normCdf(z);
    if (dir === 'lower_is_better') pct = 100 - pct;
    return Math.max(0, Math.min(100, pct));
  }}
  if (dir === 'two_sided') {{
    // Gaussian: optimal에서 멀어질수록 점수 하락
    const z = (value - m.optimal) / m.sigma;
    return 100 * Math.exp(-0.5 * z * z);
  }}
  return null;
}}

// 표준 정규분포 누적분포함수 (Abramowitz-Stegun 근사, 충분히 정확)
function normCdf(z) {{
  const t = 1 / (1 + 0.2316419 * Math.abs(z));
  const d = 0.3989423 * Math.exp(-z * z / 2);
  let p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
  return z > 0 ? 1 - p : p;
}}


// =====================================================================
// Bat Speed 예측 함수
// =====================================================================
function predictBatSpeed(values) {{
  // values: object mapping variable_key to numeric value
  // 결측 시 코호트 mean으로 imputation
  let result = BAT_SPEED_REGRESSION.intercept;
  for (const p of BAT_SPEED_REGRESSION.predictors) {{
    let v = values[p];
    if (v == null || isNaN(v)) {{
      v = BAT_SPEED_REGRESSION.predictor_means[p];
    }}
    result += BAT_SPEED_REGRESSION.coefs[p] * v;
  }}
  return result;
}}
"""

# escape js literal interpolation issue (`${...}` etc). 우리 코드엔 그런 게 없지만 검증.
# replace `${ var_key:` only matters if used. Our string just embeds JSON which is safe.

(OUT_DIR / 'metadata_batting.js').write_text(metadata_js, encoding='utf-8')
print(f"Wrote: metadata_batting.js  ({len(metadata_js):,} chars)")


# ============================================================================
# cohort_batting.js — 카테고리(B1~B6, C, F) 매핑
# ============================================================================
# Driveline 5-카테고리 + 추가
CATEGORIES = {
    'B1_StridePosture': {
        'label_kr': 'B1. Stride Posture (스트라이드 자세)',
        'label_en': 'Stride Posture',
        'description': '로딩→앞발 착지(FP)까지 골반·고관절·뒷팔의 위치 정확도',
        'driveline_relative_importance': 1.53,  # 합산: 0.47+0.44+0.35+0.27
        'variables': [
            {'key': 'max_pelvis_rotation_at_stride_deg',  'weight': 0.47},
            {'key': 'torso_rotation_at_fp_deg',           'weight': 0.44},
            {'key': 'rear_shoulder_adduction_at_fp_deg',  'weight': 0.35},
            {'key': 'lead_hip_posterior_tilt_at_fp_deg',  'weight': 0.27},
        ],
    },
    'B2_StrideRotation': {
        'label_kr': 'B2. Stride Rotation (스트라이드 회전)',
        'label_en': 'Stride Rotation',
        'description': 'FP 직전까지 트렁크와 골반의 회전 가속',
        'driveline_relative_importance': 1.26,
        'variables': [
            {'key': 'max_pelvis_rotation_velo_at_stride_dps', 'weight': 1.00},
            {'key': 'max_torso_rotation_velo_at_stride_dps',  'weight': 0.26},
        ],
    },
    'B3_SwingPosture': {
        'label_kr': 'B3. Swing Posture (스윙 자세)',
        'label_en': 'Swing Posture',
        'description': 'FP→임팩트 동안 자세 유지 능력',
        'driveline_relative_importance': 1.13,
        'variables': [
            {'key': 'pelvis_rotation_at_swing_deg',         'weight': 0.84},
            {'key': 'lead_hip_adduction_at_swing_deg',      'weight': 0.29},
        ],
    },
    'B4_SwingRotation': {
        'label_kr': 'B4. Swing Rotation (스윙 회전)',
        'label_en': 'Swing Rotation',
        'description': '임팩트 구간 트렁크·골반·상완의 출력 — Bat Speed에 가장 영향력 큰 모델',
        'driveline_relative_importance': 1.64,
        'variables': [
            {'key': 'torso_rotation_velo_at_swing_dps',     'weight': 0.80},
            {'key': 'upper_arm_rotation_velo_at_swing_dps', 'weight': 0.50},
            {'key': 'pelvis_rotation_velo_at_swing_dps',    'weight': 0.34},
        ],
    },
    'B5_CoG': {
        'label_kr': 'B5. CoG (무게중심)',
        'label_en': 'Center of Gravity',
        'description': '무게중심 전진 → block & rotate. CoG Decel이 elite 핵심 차별 변수',
        'driveline_relative_importance': 1.68,
        'variables': [
            {'key': 'max_cog_velo_at_stride_mps', 'weight': 0.67},
            {'key': 'cog_decel_mps',              'weight': 0.67},
            {'key': 'max_cog_velo_mps',           'weight': 0.34},
        ],
    },
    'B6_BatPath': {
        'label_kr': 'B6. Bat Path (스윙 궤적, Blast Motion)',
        'label_en': 'Bat Path (Blast Motion)',
        'description': 'Blast Motion 측정 — 어택 앵글, on-plane efficiency, vertical bat angle',
        'driveline_relative_importance': None,  # Driveline에 없음 (Blast 추가)
        'variables': [
            {'key': 'blast_attack_angle_deg',          'weight': 1.00},
            {'key': 'blast_on_plane_efficiency_pct',   'weight': 1.00},
            {'key': 'blast_vertical_bat_angle_deg',    'weight': 0.5},
            {'key': 'blast_early_connection_deg',      'weight': 0.5},
            {'key': 'blast_connection_at_impact_deg',  'weight': 0.5},
        ],
    },
    'B7_Consistency': {
        'label_kr': 'B7. Consistency (일관성)',
        'label_en': 'Consistency',
        'description': '여러 swing 간 SD — 투수 리포트 v33.17·v33.18 분석 동일 철학',
        'driveline_relative_importance': None,
        'variables': [
            {'key': 'bat_speed_sd_mph',     'weight': 1.00},
            {'key': 'attack_angle_sd_deg',  'weight': 0.7},
            {'key': 'time_to_contact_sd_s', 'weight': 0.7},
            {'key': 'max_x_factor_sd_deg',  'weight': 0.6},
            {'key': 'peak_arm_av_sd_dps',   'weight': 0.5},
            {'key': 'peak_trunk_av_sd_dps', 'weight': 0.5},
        ],
    },
    'F_Fitness': {
        'label_kr': 'F. Fitness (체력)',
        'label_en': 'Fitness',
        'description': '메카닉의 물리적 천장을 결정하는 체력 변수',
        'driveline_relative_importance': None,
        'variables': [
            {'key': 'grip_strength_kg',    'weight': 1.00},
            {'key': 'rotation_pp_w_kg',    'weight': 1.00},
            {'key': 'cmj_pp_bm',           'weight': 0.8},
            {'key': 'imtp_pp_bm',          'weight': 0.8},
            {'key': 'cmj_height_cm',       'weight': 0.5},
            {'key': 'broad_jump_cm',       'weight': 0.5},
            {'key': 'sprint_30m_s',        'weight': 0.5},
        ],
    },
}

cohort_js = f"""// cohort_batting.js
// =====================================================================
// 타격 리포트 카테고리 정의 (B1~B7, F) — Driveline 5-카테고리 + 확장
// 자동 생성: build_js_files.py
// =====================================================================

const CATEGORIES = {js_dump(CATEGORIES)};


// =====================================================================
// 카테고리 종합 점수 계산
// =====================================================================
// 가중평균: Σ(weight × score) / Σ(weight)
// (점수는 metadata_batting.js의 scoreVariable로 산출)
function categoryScore(catKey, athleteValues) {{
  const cat = CATEGORIES[catKey];
  if (!cat) return null;
  let sumWeight = 0;
  let sumScore = 0;
  const detail = [];
  for (const v of cat.variables) {{
    const val = athleteValues[v.key];
    const score = scoreVariable(v.key, val);
    if (score == null) {{
      detail.push({{ key: v.key, value: val, score: null, weight: v.weight }});
      continue;
    }}
    sumWeight += v.weight;
    sumScore += v.weight * score;
    detail.push({{ key: v.key, value: val, score, weight: v.weight }});
  }}
  return {{
    score: sumWeight > 0 ? sumScore / sumWeight : null,
    n_used: detail.filter(d => d.score != null).length,
    detail,
  }};
}}


// 종합 점수 — 모든 카테고리의 (Driveline 가중치 또는 동일가중) 평균
function overallScore(athleteValues) {{
  const cats = ['B1_StridePosture','B2_StrideRotation','B3_SwingPosture',
                'B4_SwingRotation','B5_CoG','B6_BatPath','B7_Consistency','F_Fitness'];
  let sumWeight = 0, sumScore = 0;
  const out = {{}};
  for (const c of cats) {{
    const r = categoryScore(c, athleteValues);
    out[c] = r;
    if (r && r.score != null) {{
      const w = CATEGORIES[c].driveline_relative_importance || 1.0;
      sumWeight += w;
      sumScore += w * r.score;
    }}
  }}
  out.overall = sumWeight > 0 ? sumScore / sumWeight : null;
  return out;
}}
"""

(OUT_DIR / 'cohort_batting.js').write_text(cohort_js, encoding='utf-8')
print(f"Wrote: cohort_batting.js   ({len(cohort_js):,} chars)")
print(f"\nDone. JS files in {OUT_DIR.resolve()}/")
