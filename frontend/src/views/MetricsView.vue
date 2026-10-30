<script setup>
import { computed, onMounted, ref } from "vue";
import { api, label, money, number, unit } from "../api";
import Icon from "../components/Icon.vue";
const props = defineProps({ market: String });
const metrics = ref(null),
  error = ref("");
onMounted(async () => {
  try {
    metrics.value = await api("/metrics");
  } catch (e) {
    error.value = e.message;
  }
});
const llm = computed(() => metrics.value?.llm.by_market[props.market]);
const baseline = computed(
  () => metrics.value?.baseline.by_market[props.market],
);
const improvement = computed(() =>
  baseline.value
    ? ((baseline.value.mae - llm.value.mae) / baseline.value.mae) * 100
    : 0,
);
const groups = computed(() =>
  Object.entries(metrics.value?.llm.by_role || {})
    .filter(
      ([key, value]) =>
        key.startsWith(props.market + " | ") && value.samples >= 10,
    )
    .sort((a, b) => b[1].mae - a[1].mae)
    .slice(0, 5),
);
</script>
<template>
  <div class="view">
    <div class="page-intro compact">
      <div>
        <span class="eyebrow">MEASURED, NOT ASSUMED</span>
        <h1>
          Hiểu model trước khi tin kết quả<span class="accent-dot">.</span>
        </h1>
        <p>So sánh công khai Qwen và TensorFlow linear trên cùng tập test.</p>
      </div>
      <span class="model-badge"
        ><Icon name="ShieldCheck" :size="16" /> Kết quả đo thực tế</span
      >
    </div>
    <p v-if="error" class="alert error" role="alert">{{ error }}</p>
    <template v-if="metrics && llm"
      ><div class="evaluation-banner">
        <span class="icon-tile lime"><Icon name="Target" :size="25" /></span>
        <div>
          <h3>
            {{
              improvement > 0
                ? "Qwen nhỉnh hơn nhẹ ở thị trường này."
                : "Baseline vẫn tốt hơn ở thị trường này."
            }}
          </h3>
          <p>
            MAE của Qwen {{ improvement > 0 ? "thấp" : "cao" }} hơn
            {{ number(Math.abs(improvement), 2) }}% trên
            {{ number(llm.samples) }} hồ sơ {{ label(market) }}. Không suy diễn
            thành độ chính xác tuyệt đối.
          </p>
        </div>
      </div>
      <section class="panel">
        <div class="panel-head">
          <div>
            <span class="eyebrow">DỰ ĐOÁN LƯƠNG · {{ unit(market) }}</span>
            <h3>Đặt hai mô hình cạnh nhau</h3>
          </div>
          <span class="soft-badge">Test · {{ number(llm.samples) }} hồ sơ</span>
        </div>
        <div
          class="table-scroll"
          tabindex="0"
          role="region"
          aria-label="Bảng dữ liệu có thể cuộn ngang"
        >
          <table class="metrics-table">
            <thead>
              <tr>
                <th>Mô hình</th>
                <th>MAE ↓</th>
                <th>RMSE ↓</th>
                <th>R² ↑</th>
              </tr>
            </thead>
            <tbody>
              <tr class="highlight-row">
                <td>
                  <strong>Qwen3-1.7B</strong
                  ><small>Fine-tune LoRA + đầu hồi quy</small>
                </td>
                <td>{{ money(llm.mae, market) }}</td>
                <td>{{ money(llm.rmse, market) }}</td>
                <td>{{ number(llm.r2, 3) }}</td>
              </tr>
              <tr>
                <td>
                  <strong>TensorFlow linear</strong
                  ><small>Mô hình đối chứng</small>
                </td>
                <td>{{ money(baseline.mae, market) }}</td>
                <td>{{ money(baseline.rmse, market) }}</td>
                <td>{{ number(baseline.r2, 3) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="metric-explain">
          <p>
            <strong>MAE</strong>Sai số tuyệt đối trung bình. Càng thấp càng tốt.
          </p>
          <p><strong>RMSE</strong>Nhấn mạnh các dự đoán sai lệch lớn.</p>
          <p><strong>R²</strong>Mức giải thích biến thiên thu nhập.</p>
        </div>
      </section>
      <div class="section-heading">
        <div>
          <span class="eyebrow">KHẢ NĂNG TRÍCH XUẤT</span>
          <h2>Ngôn ngữ thành dữ liệu</h2>
        </div>
        <span class="soft-badge"
          >{{ metrics.language.samples }} mẫu · nhãn silver</span
        >
      </div>
      <div class="stat-grid language-stats">
        <section class="stat-card">
          <span>JSON đúng cấu trúc</span
          ><strong
            >{{ number(metrics.language.json_schema_rate * 100, 1)
            }}<em>%</em></strong
          >
          <p>Đúng schema các trường yêu cầu</p>
        </section>
        <section class="stat-card">
          <span>Khớp vai trò</span
          ><strong
            >{{ number(metrics.language.field_accuracy_by_name.role * 100, 1)
            }}<em>%</em></strong
          >
          <p>{{ metrics.language.known_field_samples.role }} trường có nhãn</p>
        </section>
        <section class="stat-card">
          <span>Khớp kinh nghiệm có nhãn</span
          ><strong
            >{{
              number(
                metrics.language.known_field_accuracy.experience_years * 100,
                1,
              )
            }}<em>%</em></strong
          >
          <p>
            {{ metrics.language.known_field_samples.experience_years }} trường
            đã biết
          </p>
        </section>
        <section class="stat-card">
          <span>Skill F1</span
          ><strong
            >{{ number(metrics.language.skill_f1 * 100, 1) }}<em>%</em></strong
          >
          <p>Cân bằng nhận đúng và bỏ sót kỹ năng</p>
        </section>
      </div>
      <div class="bottom-grid">
        <section class="panel">
          <div class="panel-head">
            <h3>Nhóm còn nhiều sai số</h3>
            <Icon name="Activity" />
          </div>
          <div
            class="table-scroll"
            tabindex="0"
            role="region"
            aria-label="Bảng dữ liệu có thể cuộn ngang"
          >
            <table>
              <thead>
                <tr>
                  <th>Vai trò</th>
                  <th>Mẫu</th>
                  <th class="numeric">MAE</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="[name, group] in groups" :key="name">
                  <td>{{ name.split(" | ")[1] }}</td>
                  <td>{{ group.samples }}</td>
                  <td class="numeric">{{ money(group.mae, market) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="panel-footnote">
            Chỉ hiển thị nhóm có ít nhất 10 hồ sơ, sắp theo MAE giảm dần.
          </p>
        </section>
        <section class="panel source-panel">
          <h3>Giới hạn cần biết</h3>
          <p>
            Dữ liệu Việt Nam là lương chào tuyển, số mẫu test ít. Quốc tế là
            tổng thu nhập tự khai. Nhãn ngôn ngữ silver chưa tương đương nhãn
            được con người duyệt.
          </p>
          <div class="source-fact">
            <Icon name="ShieldCheck" /><span
              >Chọn checkpoint theo validation, rồi đánh giá test cuối. Baseline
              test đã từng được mở trước.</span
            >
          </div>
          <p class="muted">
            {{ metrics.model }} · rank {{ metrics.rank }} · epoch được chọn:
            {{ metrics.selected_epoch }}. Không train qua web.
          </p>
        </section>
      </div></template
    >
  </div>
</template>
