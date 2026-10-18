<script setup>
import { computed, ref } from "vue";
const props = defineProps({ data: Object });
defineEmits(["upload", "advice", "models"]);
const focus = ref("all");
const charts = computed(() =>
  props.data.charts.filter(
    (c) =>
      focus.value === "all" ||
      (focus.value === "skills"
        ? c.id.includes("skill")
        : focus.value === "experience"
          ? c.id.includes("experience")
          : c.id.includes("role") || c.id.includes("location")),
  ),
);
const global = computed(() => props.data.dataset.unit === "USD/year");
const displayUnit = computed(
  () => props.data.dataset.unit_label || "triệu VND/tháng",
);
const decimal = (n) =>
  new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(n);
</script>

<template>
  <div class="research-dashboard">
    <div class="dataset-context">
      <div>
        <span class="pill neutral">{{
          data.dataset.tag || "TRAIN V2 · TIN TUYỂN DỤNG"
        }}</span>
        <h2>{{ data.dataset.name }}</h2>
        <p>{{ data.dataset.target }}</p>
      </div>
      <button class="secondary" @click="$emit('upload')">
        Phân tích file của tôi ↗
      </button>
    </div>
    <div class="research-stats">
      <div>
        <strong>{{ data.dataset.rows }}</strong
        ><span>{{ global ? "phản hồi khảo sát" : "tin có kỳ lương rõ" }}</span>
      </div>
      <div>
        <strong>{{ data.dataset.groups ?? data.dataset.companies }}</strong
        ><span>{{ global ? "nhóm hồ sơ" : "nhóm công ty" }}</span>
      </div>
      <div>
        <strong>{{ Object.keys(data.dataset.role_counts).length }}</strong
        ><span>vai trò trong mẫu</span>
      </div>
      <div>
        <strong>{{ decimal(data.experience_salary_pearson) }}</strong
        ><span>tương quan kinh nghiệm–lương</span>
      </div>
    </div>
    <div class="research-notice">
      <strong>Phạm vi phân tích.</strong> {{ data.dataset.scope }}.
      {{ data.dataset.temporal_note }}
      <span v-if="data.dataset.weak_rows_excluded_from_charts"
        >Không gồm
        {{
          data.dataset.weak_rows_excluded_from_charts.toLocaleString("vi-VN")
        }}
        nhãn train thiếu kỳ lương.</span
      >
    </div>
    <div class="section-heading">
      <div>
        <h2>
          {{
            global
              ? "Kỹ năng và thu nhập trong khảo sát"
              : "Thị trường trong mẫu tuyển dụng"
          }}
        </h2>
        <p>Chọn câu hỏi cần phân tích; tải PNG để dùng khi trình bày.</p>
      </div>
      <div class="chart-focus" role="group" aria-label="Nhóm biểu đồ">
        <button
          v-for="[id, title] in [
            ['all', 'Tất cả'],
            ['skills', 'Công nghệ'],
            ['experience', 'Kinh nghiệm'],
            ['region', 'Vai trò & khu vực'],
          ]"
          :key="id"
          :aria-pressed="focus === id"
          :class="{ active: focus === id }"
          @click="focus = id"
        >
          {{ title }}
        </button>
      </div>
    </div>
    <div class="chart-grid research-charts">
      <article
        v-for="chart in charts"
        :key="chart.id"
        class="panel chart-panel"
      >
        <div>
          <h3>{{ chart.title }}</h3>
          <a
            :href="chart.url"
            :download="chart.id + '.png'"
            :aria-label="`Tải PNG ${chart.title}`"
            >↓</a
          >
        </div>
        <img :src="chart.url" :alt="chart.title" loading="lazy" />
        <p>{{ chart.caption }}</p>
      </article>
    </div>
    <div class="finding-grid">
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>Công nghệ được nhắc nhiều nhất</h2>
            <p>
              {{
                global
                  ? "Số người phản hồi đã sử dụng công nghệ, không phải nhu cầu tuyển dụng."
                  : "Số tin, không phải số vị trí tuyển toàn thị trường."
              }}
            </p>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Công nghệ</th>
              <th>{{ global ? "Phản hồi" : "Tin" }}</th>
              <th>{{ global ? "Nhóm hồ sơ" : "Công ty" }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in data.top_demand" :key="item.skill">
              <td>{{ item.skill }}</td>
              <td>{{ item.jobs }}</td>
              <td>{{ item.groups ?? item.companies }}</td>
            </tr>
          </tbody>
        </table>
      </section>
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>Công nghệ gắn với mức lương cao</h2>
            <p>Trung vị · nhóm đủ số mẫu, không suy nhân quả.</p>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Công nghệ</th>
              <th>{{ displayUnit }}</th>
              <th>{{ global ? "Phản hồi" : "Tin" }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in data.top_salary_skills" :key="item.skill">
              <td>{{ item.skill }}</td>
              <td class="number">
                {{
                  decimal(
                    item.median_salary_display ?? item.median_salary_million,
                  )
                }}
              </td>
              <td>{{ item.jobs }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
    <div class="analysis-next">
      <p>
        <strong>Từ phân tích đến dự đoán</strong><br />Mức lương theo công nghệ
        là liên hệ quan sát. Kiểm tra sai số model trước khi áp dụng vào hồ sơ.
      </p>
      <div>
        <button class="secondary" @click="$emit('models')">
          So sánh Ridge / RF</button
        ><button class="primary" @click="$emit('advice')">
          Dự đoán lương →
        </button>
      </div>
    </div>
    <details class="data-provenance">
      <summary>Nguồn dữ liệu và giới hạn</summary>
      <p>{{ data.training.note }}</p>
      <p>
        {{
          Object.entries(data.dataset.role_counts)
            .map(([role, n]) => `${role}: ${n} tin`)
            .join(" · ")
        }}.
      </p>
      <a
        :href="data.dataset.source_url"
        target="_blank"
        rel="noopener noreferrer"
        >Xem nguồn TiniX ↗</a
      >
    </details>
  </div>
</template>
