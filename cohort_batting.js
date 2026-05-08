// cohort_batting.js
// =====================================================================
// 타격 리포트 카테고리 정의 (B1~B7, F) — Driveline 5-카테고리 + 확장
// 자동 생성: build_js_files.py
// =====================================================================

const CATEGORIES = {
  "B1_StridePosture": {
    "label_kr": "B1. Stride Posture (스트라이드 자세)",
    "label_en": "Stride Posture",
    "description": "로딩→앞발 착지(FP)까지 골반·고관절·뒷팔의 위치 정확도",
    "driveline_relative_importance": 1.53,
    "variables": [
      {
        "key": "max_pelvis_rotation_at_stride_deg",
        "weight": 0.47
      },
      {
        "key": "torso_rotation_at_fp_deg",
        "weight": 0.44
      },
      {
        "key": "rear_shoulder_adduction_at_fp_deg",
        "weight": 0.35
      },
      {
        "key": "lead_hip_posterior_tilt_at_fp_deg",
        "weight": 0.27
      }
    ]
  },
  "B2_StrideRotation": {
    "label_kr": "B2. Stride Rotation (스트라이드 회전)",
    "label_en": "Stride Rotation",
    "description": "FP 직전까지 트렁크와 골반의 회전 가속",
    "driveline_relative_importance": 1.26,
    "variables": [
      {
        "key": "max_pelvis_rotation_velo_at_stride_dps",
        "weight": 1.0
      },
      {
        "key": "max_torso_rotation_velo_at_stride_dps",
        "weight": 0.26
      }
    ]
  },
  "B3_SwingPosture": {
    "label_kr": "B3. Swing Posture (스윙 자세)",
    "label_en": "Swing Posture",
    "description": "FP→임팩트 동안 자세 유지 능력",
    "driveline_relative_importance": 1.13,
    "variables": [
      {
        "key": "pelvis_rotation_at_swing_deg",
        "weight": 0.84
      },
      {
        "key": "lead_hip_adduction_at_swing_deg",
        "weight": 0.29
      }
    ]
  },
  "B4_SwingRotation": {
    "label_kr": "B4. Swing Rotation (스윙 회전)",
    "label_en": "Swing Rotation",
    "description": "임팩트 구간 트렁크·골반·상완의 출력 — Bat Speed에 가장 영향력 큰 모델",
    "driveline_relative_importance": 1.64,
    "variables": [
      {
        "key": "torso_rotation_velo_at_swing_dps",
        "weight": 0.8
      },
      {
        "key": "upper_arm_rotation_velo_at_swing_dps",
        "weight": 0.5
      },
      {
        "key": "pelvis_rotation_velo_at_swing_dps",
        "weight": 0.34
      }
    ]
  },
  "B5_CoG": {
    "label_kr": "B5. CoG (무게중심)",
    "label_en": "Center of Gravity",
    "description": "무게중심 전진 → block & rotate. CoG Decel이 elite 핵심 차별 변수",
    "driveline_relative_importance": 1.68,
    "variables": [
      {
        "key": "max_cog_velo_at_stride_mps",
        "weight": 0.67
      },
      {
        "key": "cog_decel_mps",
        "weight": 0.67
      },
      {
        "key": "max_cog_velo_mps",
        "weight": 0.34
      }
    ]
  },
  "B6_BatPath": {
    "label_kr": "B6. Bat Path (스윙 궤적, Blast Motion)",
    "label_en": "Bat Path (Blast Motion)",
    "description": "Blast Motion 측정 — 어택 앵글, on-plane efficiency, vertical bat angle",
    "driveline_relative_importance": null,
    "variables": [
      {
        "key": "blast_attack_angle_deg",
        "weight": 1.0
      },
      {
        "key": "blast_on_plane_efficiency_pct",
        "weight": 1.0
      },
      {
        "key": "blast_vertical_bat_angle_deg",
        "weight": 0.5
      },
      {
        "key": "blast_early_connection_deg",
        "weight": 0.5
      },
      {
        "key": "blast_connection_at_impact_deg",
        "weight": 0.5
      }
    ]
  },
  "B7_Consistency": {
    "label_kr": "B7. Consistency (일관성)",
    "label_en": "Consistency",
    "description": "여러 swing 간 SD — 투수 리포트 v33.17·v33.18 분석 동일 철학",
    "driveline_relative_importance": null,
    "variables": [
      {
        "key": "bat_speed_sd_mph",
        "weight": 1.0
      },
      {
        "key": "attack_angle_sd_deg",
        "weight": 0.7
      },
      {
        "key": "time_to_contact_sd_s",
        "weight": 0.7
      },
      {
        "key": "max_x_factor_sd_deg",
        "weight": 0.6
      },
      {
        "key": "peak_arm_av_sd_dps",
        "weight": 0.5
      },
      {
        "key": "peak_trunk_av_sd_dps",
        "weight": 0.5
      }
    ]
  },
  "F_Fitness": {
    "label_kr": "F. Fitness (체력)",
    "label_en": "Fitness",
    "description": "메카닉의 물리적 천장을 결정하는 체력 변수",
    "driveline_relative_importance": null,
    "variables": [
      {
        "key": "grip_strength_kg",
        "weight": 1.0
      },
      {
        "key": "rotation_pp_w_kg",
        "weight": 1.0
      },
      {
        "key": "cmj_pp_bm",
        "weight": 0.8
      },
      {
        "key": "imtp_pp_bm",
        "weight": 0.8
      },
      {
        "key": "cmj_height_cm",
        "weight": 0.5
      },
      {
        "key": "broad_jump_cm",
        "weight": 0.5
      },
      {
        "key": "sprint_30m_s",
        "weight": 0.5
      }
    ]
  }
};


// =====================================================================
// 카테고리 종합 점수 계산
// =====================================================================
// 가중평균: Σ(weight × score) / Σ(weight)
// (점수는 metadata_batting.js의 scoreVariable로 산출)
function categoryScore(catKey, athleteValues) {
  const cat = CATEGORIES[catKey];
  if (!cat) return null;
  let sumWeight = 0;
  let sumScore = 0;
  const detail = [];
  for (const v of cat.variables) {
    const val = athleteValues[v.key];
    const score = scoreVariable(v.key, val);
    if (score == null) {
      detail.push({ key: v.key, value: val, score: null, weight: v.weight });
      continue;
    }
    sumWeight += v.weight;
    sumScore += v.weight * score;
    detail.push({ key: v.key, value: val, score, weight: v.weight });
  }
  return {
    score: sumWeight > 0 ? sumScore / sumWeight : null,
    n_used: detail.filter(d => d.score != null).length,
    detail,
  };
}


// 종합 점수 — 모든 카테고리의 (Driveline 가중치 또는 동일가중) 평균
function overallScore(athleteValues) {
  const cats = ['B1_StridePosture','B2_StrideRotation','B3_SwingPosture',
                'B4_SwingRotation','B5_CoG','B6_BatPath','B7_Consistency','F_Fitness'];
  let sumWeight = 0, sumScore = 0;
  const out = {};
  for (const c of cats) {
    const r = categoryScore(c, athleteValues);
    out[c] = r;
    if (r && r.score != null) {
      const w = CATEGORIES[c].driveline_relative_importance || 1.0;
      sumWeight += w;
      sumScore += w * r.score;
    }
  }
  out.overall = sumWeight > 0 ? sumScore / sumWeight : null;
  return out;
}
