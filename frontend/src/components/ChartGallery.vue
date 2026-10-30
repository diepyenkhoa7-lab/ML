<script setup>
import { ref, watch } from "vue";
import { titles } from "../api";
import Icon from "./Icon.vue";
const props = defineProps({
  charts: { type: Array, default: () => [] },
  observed: Boolean,
});
const active = ref("experience");
const loading = ref(true);
watch(
  () => props.charts,
  () => {
    loading.value = true;
  },
);
</script>
<template>
  <section class="panel chart-panel">
    <div class="panel-head">
      <div>
        <span class="eyebrow">{{
          observed ? "THU NHẬP QUAN SÁT" : "THU NHẬP DỰ ĐOÁN"
        }}</span>
        <h3>{{ titles[active] }}</h3>
      </div>
      <span class="soft-badge">Matplotlib · Seaborn</span>
    </div>
    <div class="chart-tabs" aria-label="Loại biểu đồ">
      <button
        v-for="kind in [
          'experience',
          'role',
          'location',
          'skill_income',
          'skills',
        ]"
        :key="kind"
        :class="{ selected: active === kind }"
        @click="
          active = kind;
          loading = true;
        "
      >
        {{
          {
            experience: "Kinh nghiệm",
            role: "Vai trò",
            location: "Khu vực",
            skill_income: "Kỹ năng",
            skills: "Công nghệ",
          }[kind]
        }}
      </button>
    </div>
    <div class="chart-image" :class="{ 'is-loading': loading }">
      <img
        v-if="charts.length"
        :key="charts.find((c) => c.kind === active)?.url"
        :src="charts.find((c) => c.kind === active)?.url"
        :alt="
          titles[active] +
          (observed ? ' từ dữ liệu quan sát' : ' từ dự đoán Qwen')
        "
        @load="loading = false"
        @error="loading = false"
      />
    </div>
    <div class="chart-caption">
      <span>{{
        observed
          ? "Thống kê từ tập train · giữ nguyên từng quan sát."
          : "Ước tính của model cho file đầu vào, không phải thu nhập thực đo."
      }}</span
      ><a
        v-if="charts.length"
        :href="charts.find((c) => c.kind === active)?.url"
        target="_blank"
        rel="noopener"
        :aria-label="'Mở biểu đồ ' + titles[active]"
        ><Icon name="ArrowUpRight" :size="17" /> Mở biểu đồ</a
      >
    </div>
  </section>
</template>
