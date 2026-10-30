<script setup>
import { number, money, label, unit } from "../api";
defineProps({ rows: { type: Array, default: () => [] }, prediction: Boolean });
</script>
<template>
  <div
    class="table-scroll"
    tabindex="0"
    role="region"
    aria-label="Bảng dữ liệu có thể cuộn ngang"
  >
    <table class="profile-table">
      <thead>
        <tr>
          <th>{{ prediction ? "Dòng / Hồ sơ" : "Vai trò" }}</th>
          <th>Khu vực</th>
          <th>Kinh nghiệm</th>
          <th>Kỹ năng</th>
          <th class="numeric">
            {{ prediction ? "Qwen dự đoán" : "Thu nhập" }}
          </th>
          <th v-if="prediction" class="numeric">Đối chứng</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, index) in rows"
          :key="index"
          :class="{ 'error-row': row.error }"
        >
          <template v-if="row.error"
            ><td>
              <span class="row-error-badge">Dòng {{ row.source_row }}</span>
            </td>
            <td colspan="5" class="error-text">{{ row.error }}</td></template
          >
          <template v-else
            ><td>
              <span class="table-title" :title="row.role">{{ row.role }}</span
              ><small
                >{{ prediction ? `Dòng ${row.source_row} · ` : ""
                }}{{ label(row.market) }}</small
              >
            </td>
            <td class="location-cell">{{ row.location }}</td>
            <td>
              {{ number(row.experience_years, 1) }}
              <span class="muted">năm</span>
            </td>
            <td class="skill-cell">
              <span
                v-for="skill in String(row.skills || '')
                  .split(';')
                  .filter(Boolean)
                  .slice(0, 2)"
                :key="skill"
                class="skill-tag"
                >{{ skill }}</span
              ><span
                v-if="String(row.skills || '').split(';').length > 2"
                class="more-skills"
                :title="String(row.skills).split(';').join(', ')"
                >+{{ String(row.skills).split(";").length - 2 }}</span
              >
            </td>
            <td class="numeric">
              <strong>{{
                money(prediction ? row.prediction : row.salary, row.market)
              }}</strong
              ><small>{{ unit(row.market) }}</small>
            </td>
            <td v-if="prediction" class="numeric">
              <span>{{ money(row.baseline_prediction, row.market) }}</span
              ><small>TensorFlow linear</small>
            </td></template
          >
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="prediction ? 6 : 5" class="empty-cell">
            Không có hồ sơ phù hợp. Thử thay đổi bộ lọc.
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
