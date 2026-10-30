<script setup>
import { computed, ref } from "vue";
import { label, money, number, unit } from "../api";
import Icon from "./Icon.vue";
import ProfileTable from "./ProfileTable.vue";
import ChartGallery from "./ChartGallery.vue";
const props = defineProps({ job: Object, result: Object });
const chosenMarket = ref("");
const page = ref(1);
const selected = computed(
  () =>
    props.result?.markets.find((m) => m.market === chosenMarket.value) ||
    props.result?.markets[0],
);
const progress = computed(() =>
  props.job?.total ? (props.job.processed / props.job.total) * 100 : 0,
);
const adviceRows = computed(
  () => props.result?.rows.filter((r) => r.advice) || [],
);
</script>
<template>
  <section v-if="job" class="results-section" aria-live="polite">
    <div class="section-heading">
      <div>
        <span class="eyebrow">PHIÊN PHÂN TÍCH</span>
        <h2>{{ job.filename }}</h2>
      </div>
      <span class="status-pill" :class="job.status"
        ><Icon
          :name="
            job.status === 'completed'
              ? 'CheckCircle2'
              : ['failed', 'interrupted'].includes(job.status)
                ? 'XCircle'
                : 'LoaderCircle'
          "
          :class="{ spin: ['queued', 'running'].includes(job.status) }"
          :size="16"
        />{{
          {
            completed: "Hoàn tất",
            running: "Đang phân tích",
            queued: "Trong hàng đợi",
            failed: "Không hoàn tất",
            interrupted: "Đã gián đoạn",
          }[job.status]
        }}</span
      >
    </div>
    <div v-if="job.status !== 'completed'" class="panel progress-panel">
      <div class="progress-label">
        <strong>{{ job.stage }}</strong
        ><span>{{ job.processed }} / {{ job.total }} dòng</span>
      </div>
      <div
        class="progress-track"
        role="progressbar"
        :aria-valuenow="job.processed"
        aria-valuemin="0"
        :aria-valuemax="job.total"
        :aria-label="job.stage"
      >
        <span :style="{ width: progress + '%' }"></span>
      </div>
      <p>
        {{
          job.error ||
          "Lần phân tích đầu cần nạp trọng số. Bạn có thể chuyển trang; tiến độ vẫn được giữ."
        }}
      </p>
    </div>
    <template v-if="result && job.status === 'completed'">
      <div class="result-stats">
        <div>
          <span>Hồ sơ hợp lệ</span
          ><strong
            >{{ job.valid }}<small> / {{ job.total }}</small></strong
          >
        </div>
        <div>
          <span>Cần kiểm tra</span
          ><strong :class="{ 'error-text': job.errors }"
            >{{ job.errors }}<small> dòng</small></strong
          >
        </div>
        <div v-for="market in result.markets" :key="market.market">
          <span>Trung vị dự đoán · {{ label(market.market) }}</span
          ><strong>{{ money(market.median_prediction, market.market) }}</strong
          ><small>{{ unit(market.market) }} · {{ market.samples }} hồ sơ</small>
        </div>
      </div>
      <div class="result-toolbar">
        <p>
          <Icon name="ShieldCheck" :size="17" /> {{ job.model_version }} · Không
          cập nhật trọng số
        </p>
        <div class="button-group">
          <a
            v-for="format in ['csv', 'xlsx', 'json']"
            :key="format"
            class="button secondary small"
            :href="`/api/jobs/${job.id}/download/${format}`"
            ><Icon name="ArrowDownToLine" :size="15" />{{
              format.toUpperCase()
            }}</a
          >
        </div>
      </div>
      <section class="panel">
        <ProfileTable
          :rows="result.rows.slice((page - 1) * 15, page * 15)"
          prediction
        />
        <div v-if="result.rows.length > 15" class="pagination">
          <span>{{ result.rows.length }} dòng</span>
          <div>
            <button
              :disabled="page === 1"
              @click="page--"
              aria-label="Trang trước"
            >
              <Icon name="ChevronLeft" :size="16" /></button
            ><span>{{ page }} / {{ Math.ceil(result.rows.length / 15) }}</span
            ><button
              :disabled="page * 15 >= result.rows.length"
              @click="page++"
              aria-label="Trang sau"
            >
              <Icon name="ChevronRight" :size="16" />
            </button>
          </div>
        </div>
      </section>
      <section v-if="result.markets.length" class="result-charts">
        <div v-if="result.markets.length > 1" class="segment">
          <button
            v-for="market in result.markets"
            :key="market.market"
            :class="{ selected: selected?.market === market.market }"
            @click="chosenMarket = market.market"
          >
            {{ label(market.market) }}
          </button>
        </div>
        <ChartGallery
          v-if="selected"
          :key="selected.market"
          :charts="selected.charts"
        />
      </section>
      <section
        v-if="Object.keys(result.comparison.by_market || {}).length"
        class="panel note-panel"
      >
        <h3>Đối chiếu với thu nhập bạn cung cấp</h3>
        <p
          v-for="(metric, market) in result.comparison.by_market"
          :key="market"
        >
          {{ label(market) }}: MAE {{ money(metric.mae, market) }}, RMSE
          {{ money(metric.rmse, market) }}, R² {{ number(metric.r2, 3) }} ·
          {{ metric.samples }} dòng{{ metric.low_support ? " · ít mẫu" : "" }}.
        </p>
        <p class="muted">
          Đây là đối chiếu trên file của bạn và đơn vị bạn xác nhận, không phải
          benchmark độc lập.
        </p>
      </section>
      <div v-if="adviceRows.length" class="advice-grid">
        <section
          v-for="(row, index) in adviceRows"
          :key="index"
          class="panel advice-card"
        >
          <div class="advice-heading">
            <span class="icon-tile lime"><Icon name="Sparkles" /></span>
            <div>
              <span class="eyebrow">GỢI Ý KỸ NĂNG</span>
              <h3>{{ row.role }}</h3>
              <small>{{ row.location }}</small>
            </div>
          </div>
          <template v-if="row.advice.status === 'insufficient_data'"
            ><p>Chưa đủ dữ liệu cùng vai trò để gợi ý kỹ năng đáng tin cậy.</p>
            <span class="soft-badge">Cần ít nhất 10 mẫu hỗ trợ</span></template
          ><template v-else-if="row.advice.status === 'error'"
            ><p class="error-text">
              Chưa tạo được tư vấn: {{ row.advice.error }}
            </p></template
          ><template v-else
            ><div class="recommendations">
              <div v-for="r in row.advice.recommendations" :key="r.skill">
                <strong>{{ r.skill }}</strong
                ><span>{{ r.support }} mẫu hỗ trợ</span
                ><small
                  >Chênh lệch trung vị quan sát:
                  {{ money(r.observed_difference, row.market) }}</small
                >
              </div>
            </div>
            <p>{{ row.advice.explanation }}</p></template
          >
        </section>
      </div>
      <div class="context-note">
        <Icon name="CircleHelp" :size="18" />
        <p>{{ result.notes.join(" ") }}</p>
      </div>
    </template>
  </section>
</template>
