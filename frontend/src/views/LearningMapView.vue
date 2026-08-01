<template>
  <section class="view-panel learning-map-view">
    <header class="topbar learning-map-topbar">
      <div>
        <p class="section-kicker">学习地图</p>
        <h2>当前项目知识地图</h2>
        <p>{{ overviewData.scope_notice || "仅表示当前项目、当前来源版本下的项目知识分析。" }}</p>
      </div>
      <div class="learning-map-actions">
        <button type="button" :disabled="busy || !activeProjectId" data-learning-map-action="analyze" @click="emit('analyze')">
          {{ hasAnalysis ? "重新分析" : "分析项目" }}
        </button>
        <button type="button" :disabled="busy || !activeProjectId" data-learning-map-action="refresh" @click="emit('refresh')">
          刷新
        </button>
      </div>
    </header>

    <p v-if="error" class="status-line error">{{ error }}</p>
    <p v-if="busy" class="status-line">正在读取当前项目知识地图...</p>
    <p v-else-if="!activeProjectId" class="status-line">请先选择项目。</p>
    <div v-else-if="stale" class="learning-map-stale" role="alert">
      <strong>项目来源已变化，当前分析已过期。</strong>
      <p>请重新分析后再发起逐点学习或定向评估；历史结果仅供回看。</p>
    </div>

    <section class="learning-map-overview">
      <div>
        <p class="section-kicker">项目理解</p>
        <h3>{{ overviewData.summary ? "分析摘要" : "等待分析" }}</h3>
        <p>{{ overviewData.summary || "导入项目资料后运行分析，生成带来源的项目理解。" }}</p>
        <button
          v-if="(overviewData.source_ids || []).length"
          type="button"
          data-learning-map-action="open-overview-sources"
          @click="openSources('项目理解', overviewData.source_ids)"
        >
          查看项目理解来源
        </button>
      </div>
      <dl class="learning-map-metrics">
        <div>
          <dt>知识点</dt>
          <dd>{{ knowledgePointItems.length }}</dd>
        </div>
        <div>
          <dt>已验证</dt>
          <dd>{{ coverageSummary.assessed_count || 0 }}</dd>
        </div>
        <div>
          <dt>项目覆盖</dt>
          <dd>{{ percent(coverageSummary.coverage_ratio) }}</dd>
        </div>
      </dl>
    </section>

    <div class="learning-map-columns">
      <section class="learning-map-section">
        <div class="section-title-row">
          <div>
            <p class="section-kicker">知识覆盖</p>
            <h3>项目知识点</h3>
          </div>
          <span class="learning-map-scope">当前项目评估</span>
        </div>
        <p v-if="knowledgePointItems.length === 0" class="muted-line">暂无知识点，请先分析项目。</p>
        <ol v-else class="learning-map-list">
          <li v-for="point in knowledgePointItems" :key="point.id">
            <div class="learning-map-card-heading">
              <div>
                <span class="learning-map-category">{{ point.category || "project" }}</span>
                <h4>{{ point.title || point.stable_key }}</h4>
              </div>
              <span class="learning-map-status" :data-status="point.status || 'unassessed'">
                {{ statusLabel(point.status) }}
              </span>
            </div>
            <p>{{ point.summary || "暂无摘要" }}</p>
            <p v-if="point.low_confidence" class="learning-map-confidence">低置信度结果，建议结合来源复核。</p>
            <div class="learning-map-card-actions">
              <button
                type="button"
                :disabled="stale || !canAssess"
                data-learning-map-action="learn-knowledge-point"
                @click="startLearning('knowledge_point', point.id)"
              >
                开始学习
              </button>
              <button
                type="button"
                :disabled="stale || !canAssess"
                data-learning-map-action="assess-knowledge-point"
                @click="startAssessment('knowledge_point', point.id)"
              >
                定向评估
              </button>
              <button
                type="button"
                :disabled="!(point.source_ids || []).length"
                data-learning-map-action="open-knowledge-sources"
                @click="openSources(point.title, point.source_ids)"
              >
                查看来源
              </button>
            </div>
          </li>
        </ol>
      </section>

      <section class="learning-map-section">
        <div class="section-title-row">
          <div>
            <p class="section-kicker">技能差距</p>
            <h3>通用技能辅助映射</h3>
          </div>
        </div>
        <p class="learning-map-scope">{{ skillsData.scope_notice || "技能映射只解释当前项目知识，不代表整体职业能力。" }}</p>
        <p v-if="skillItems.length === 0" class="muted-line">暂无技能映射。</p>
        <ol v-else class="learning-map-list">
          <li v-for="skill in skillItems" :key="skill.id">
            <div class="learning-map-card-heading">
              <div>
                <span class="learning-map-category">{{ skill.category || "skill" }}</span>
                <h4>{{ skill.name || skill.stable_key }}</h4>
              </div>
              <span class="learning-map-status" :data-status="skillDisplayStatus(skill)">
                {{ skillStateLabel(skill) }}
              </span>
            </div>
            <p v-if="skill.assessment_state === 'no_project_evidence' || skill.project_evidence === 'no_project_evidence'">
              当前项目无证据，不能据此得出能力结论。
            </p>
            <p v-else>
              已验证 {{ skill.assessed_knowledge_point_count || 0 }} /
              {{ skill.mapped_knowledge_point_count || mappingCount(skill) }} 个关联知识点。
            </p>
            <div class="learning-map-card-actions">
              <button
                type="button"
                :disabled="stale || !canAssess || skill.project_evidence === 'no_project_evidence'"
                data-learning-map-action="learn-skill"
                @click="startLearning('skill', skill.id)"
              >
                开始学习
              </button>
              <button
                type="button"
                :disabled="stale || !canAssess || skill.project_evidence === 'no_project_evidence'"
                data-learning-map-action="assess-skill"
                @click="startAssessment('skill', skill.id)"
              >
                定向评估
              </button>
              <button
                type="button"
                :disabled="!(skill.source_ids || []).length"
                data-learning-map-action="open-skill-sources"
                @click="openSources(skill.name, skill.source_ids)"
              >
                查看来源
              </button>
            </div>
          </li>
        </ol>
      </section>
    </div>

    <section class="learning-map-section learning-map-history">
      <p class="section-kicker">评估记录</p>
      <h3>当前项目最近评估</h3>
      <p v-if="recentAssessments.length === 0" class="muted-line">暂无评估记录。</p>
      <ol v-else class="learning-map-history-list">
        <li v-for="result in recentAssessments" :key="result.id">
          <div>
            <strong>{{ statusLabel(result.status) }}</strong>
            <span>{{ percent(result.score) }} / 置信度 {{ percent(result.confidence) }}</span>
            <span v-if="!result.valid_for_current_sources">来源已变化，仅作历史记录</span>
          </div>
          <button
            type="button"
            :disabled="!(result.source_ids || []).length"
            data-learning-map-action="open-assessment-sources"
            @click="openSources('评估记录', result.source_ids)"
          >
            查看来源
          </button>
        </li>
      </ol>
    </section>
  </section>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  projectId: {
    type: String,
    default: "",
  },
  selectedProjectId: {
    type: String,
    default: "",
  },
  overview: {
    type: Object,
    default: () => ({}),
  },
  knowledgePoints: {
    type: Object,
    default: () => ({}),
  },
  skills: {
    type: Object,
    default: () => ({}),
  },
  coverage: {
    type: Object,
    default: () => ({}),
  },
  loading: {
    type: Boolean,
    default: false,
  },
  analyzing: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["analyze", "refresh", "start-assessment", "start-learning", "open-sources"]);

const activeProjectId = computed(() => props.projectId || props.selectedProjectId);
const overviewData = computed(() => props.overview?.overview || props.overview || {});
const knowledgePointsData = computed(() => props.knowledgePoints?.knowledge_points || props.knowledgePoints || {});
const skillsData = computed(() => props.skills?.skills || props.skills || {});
const coverageData = computed(() => props.coverage?.coverage || props.coverage || {});
const busy = computed(() => props.loading || props.analyzing);
const hasAnalysis = computed(() => Boolean(overviewData.value.analysis?.id || overviewData.value.status));
const stale = computed(() => Boolean(
  overviewData.value.stale
  || knowledgePointsData.value.stale
  || skillsData.value.stale
  || coverageData.value.stale,
));
const canAssess = computed(() => coverageData.value.can_assess !== false && !stale.value);
const coverageSummary = computed(() => coverageData.value.summary || {});
const recentAssessments = computed(() => coverageData.value.recent_assessments || []);

const knowledgePointItems = computed(() => {
  const base = knowledgePointsData.value.items || [];
  const coverageById = Object.fromEntries(
    (coverageData.value.knowledge_points || []).map((point) => [point.id, point]),
  );
  return base.map((point) => ({ ...point, ...(coverageById[point.id] || {}) }));
});

const skillItems = computed(() => {
  const base = skillsData.value.items || [];
  const coverageById = Object.fromEntries(
    (coverageData.value.skills || []).map((skill) => [skill.id, skill]),
  );
  return base.map((skill) => ({ ...skill, ...(coverageById[skill.id] || {}) }));
});

function startAssessment(targetType, targetId) {
  emit("start-assessment", { target_type: targetType, target_id: targetId });
}

function startLearning(targetType, targetId) {
  emit("start-learning", {
    target_type: targetType,
    target_id: targetId,
    origin_type: "learning_map",
  });
}

function openSources(title, sourceIds = []) {
  const sources = {
    ...(overviewData.value.sources || {}),
    ...(knowledgePointsData.value.sources || {}),
    ...(skillsData.value.sources || {}),
    ...(coverageData.value.sources || {}),
  };
  emit("open-sources", { title, source_ids: sourceIds, sources });
}

function statusLabel(status) {
  const labels = {
    unassessed: "未验证",
    needs_work: "需补强",
    developing: "发展中",
    mastered: "已掌握",
  };
  return labels[status] || labels.unassessed;
}

function skillDisplayStatus(skill) {
  if (skill.assessment_state === "no_project_evidence" || skill.project_evidence === "no_project_evidence") {
    return "no_project_evidence";
  }
  return skill.status || "unassessed";
}

function skillStateLabel(skill) {
  if (skill.assessment_state === "no_project_evidence" || skill.project_evidence === "no_project_evidence") {
    return "当前项目无证据";
  }
  return statusLabel(skill.status);
}

function mappingCount(skill) {
  return Array.isArray(skill.mappings) ? skill.mappings.length : 0;
}

function percent(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? `${Math.round(numeric * 100)}%` : "0%";
}
</script>

<style scoped>
.learning-map-view {
  overflow-y: auto;
}

.learning-map-topbar,
.learning-map-actions,
.learning-map-card-heading,
.learning-map-card-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.learning-map-actions,
.learning-map-card-actions {
  align-items: center;
  justify-content: flex-start;
}

.learning-map-stale {
  margin: var(--space-4) 0;
  padding: var(--space-4);
  color: var(--warning);
  background: var(--warning-soft);
  border-radius: var(--radius-lg);
}

.learning-map-stale p {
  margin-bottom: 0;
}

.learning-map-overview,
.learning-map-section {
  margin-top: var(--space-4);
  padding: var(--space-5);
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.learning-map-overview {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-5);
}

.learning-map-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(80px, 1fr));
  gap: var(--space-3);
  margin: 0;
}

.learning-map-metrics div {
  padding: var(--space-3);
  text-align: center;
  background: var(--surface-sunken);
  border-radius: var(--radius);
}

.learning-map-metrics dt,
.learning-map-scope {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.learning-map-metrics dd {
  margin: var(--space-1) 0 0;
  font-size: var(--text-lg);
}

.learning-map-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.learning-map-list,
.learning-map-history-list {
  display: grid;
  gap: var(--space-3);
  padding: 0;
  list-style: none;
}

.learning-map-list li {
  padding: var(--space-4);
  background: var(--surface-sunken);
  border-radius: var(--radius);
}

.learning-map-card-heading h4 {
  margin: var(--space-1) 0;
}

.learning-map-category,
.learning-map-status {
  color: var(--text-secondary);
  font-size: var(--text-xs);
}

.learning-map-status {
  flex: 0 0 auto;
  padding: var(--space-1) var(--space-2);
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
}

.learning-map-confidence {
  color: var(--warning);
}

.learning-map-history-list li {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-3);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--border);
}

.learning-map-history-list li > div {
  display: grid;
  gap: var(--space-1);
}

@media (max-width: 900px) {
  .learning-map-columns,
  .learning-map-overview {
    grid-template-columns: 1fr;
  }
}
</style>
