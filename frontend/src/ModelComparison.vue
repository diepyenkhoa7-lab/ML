<script setup>
import { computed, ref } from "vue";
const props = defineProps({
  metrics: Object,
  selected: String,
  unit: { default: "VND/month" },
  scope: String,
});
const metric = ref("mae");
const names = {
  ridge: "Ridge Regression",
  random_forest: "Random Forest",
  median_baseline: "Baseline trung vị",
};
const usd = computed(() => props.unit === "USD/year");
const unitLabel = computed(() =>
  usd.value ? "nghìn USD/năm" : "triệu VND/tháng",
);
const number = (v) =>
  v == null || !Number.isFinite(v)
    ? "—"
    : new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(
        v / (usd.value ? 1000 : 1e6),
      );
const value = (item, key) => item[key + (usd.value ? "_usd_year" : "_vnd")];
const entries = computed(() => Object.entries(props.metrics || {}));
const maximum = computed(() =>
  Math.max(1, ...entries.value.map(([, m]) => value(m, metric.value))),
);
</script>

<template>
  <div class="model-comparison">
    <div class="scope-strip">
      <span class="pill neutral">{{ scope }}</span
      ><span>{{ unitLabel }} · cùng tập đánh giá</span>
    </div>
    <div class="comparison-layout">
      <section class="panel benchmark-table">
        <div class="panel-heading">
          <div>
            <h2>Kết quả của các mô hình</h2>
            <p>MAE và RMSE càng thấp càng tốt; R² càng cao càng tốt.</p>
          </div>
        </div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Mô hình</th>
                <th>Số mẫu</th>
                <th>MAE</th>
                <th>RMSE</th>
                <th>R²</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="[name, item] in entries"
                :key="name"
                :class="{ 'selected-model-row': name === selected }"
              >
                <td>
                  <strong>{{ names[name] || name }}</strong
                  ><small v-if="name === selected">Mô hình đã chọn</small>
                </td>
                <td>{{ item.samples }}</td>
                <td class="number">{{ number(value(item, "mae")) }}</td>
                <td>{{ number(value(item, "rmse")) }}</td>
                <td>
                  {{
                    item.r2 == null ? "Không đủ dữ liệu" : item.r2.toFixed(3)
                  }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="source-note">
          Đơn vị MAE/RMSE: {{ unitLabel }}. Không chuyển metric thành phần trăm
          “độ chính xác”.
        </p>
      </section>
      <section class="panel metric-visual">
        <div class="panel-heading">
          <h2>So sánh sai số</h2>
          <label
            >Chỉ số<select v-model="metric">
              <option value="mae">MAE</option>
              <option value="rmse">RMSE</option>
            </select></label
          >
        </div>
        <div
          class="metric-bars"
          role="img"
          :aria-label="`So sánh ${metric.toUpperCase()} của các mô hình, ${unitLabel}`"
        >
          <div
            v-for="[name, item] in entries"
            :key="name"
            class="metric-bar-row"
          >
            <div>
              <span>{{ names[name] || name }}</span
              ><strong>{{ number(value(item, metric)) }}</strong>
            </div>
            <div class="metric-track">
              <span
                :class="name"
                :style="{ width: (value(item, metric) / maximum) * 100 + '%' }"
              ></span>
            </div>
          </div>
        </div>
      </section>
    </div>
    <div class="metric-glossary">
      <p>
        <strong>MAE</strong> · Sai lệch tuyệt đối trung bình, dễ diễn giải theo
        đơn vị lương.
      </p>
      <p><strong>RMSE</strong> · Nhạy hơn với các dự đoán lệch nhiều.</p>
      <p>
        <strong>R²</strong> · So với dự đoán trung bình; có thể âm nếu mô hình
        kém.
      </p>
    </div>
  </div>
</template>
