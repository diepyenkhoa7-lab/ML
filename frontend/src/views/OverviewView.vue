<script setup>
import { ref, watch } from "vue";
import { api, money, number, unit } from "../api";
import Icon from "../components/Icon.vue";
import ChartGallery from "../components/ChartGallery.vue";
const props = defineProps({ market: String });
defineEmits(["navigate"]);
const data = ref(null),
  error = ref(""),
  loading = ref(false);
let requestId = 0;
watch(
  () => props.market,
  async (market) => {
    const id = ++requestId;
    loading.value = true;
    error.value = "";
    data.value = null;
    try {
      const value = await api(`/overview?market=${market}`);
      if (id === requestId) data.value = value;
    } catch (e) {
      error.value = e.message;
    } finally {
      if (id === requestId) loading.value = false;
    }
  },
  { immediate: true },
);
</script>
<template>
  <div class="view overview-view">
    <div class="page-intro">
      <div>
        <div class="eyebrow">
          <span class="tiny-line"></span>CAREER INTELLIGENCE
        </div>
        <h1>
          Thị trường CNTT,<br />qua lăng kính dữ liệu<span class="accent-dot"
            >.</span
          >
        </h1>
        <p>Hiểu kỹ năng, khám phá thu nhập và tìm hướng đi tiếp theo.</p>
      </div>
      <button class="button primary" @click="$emit('navigate', 'upload')">
        <Icon name="FileUp" :size="18" /> Phân tích file của bạn
        <Icon name="ArrowUpRight" :size="17" />
      </button>
    </div>
    <p v-if="error" class="alert error" role="alert">{{ error }}</p>
    <div v-if="loading && !data" class="loading-block">
      <Icon name="LoaderCircle" class="spin" /> Đang đọc dữ liệu…
    </div>
    <template v-if="data">
      <div class="data-strip">
        <span><span class="dot"></span>{{ data.source }}</span
        ><span>{{
          data.source_kind === "survey"
            ? "Công nghệ được sử dụng trong khảo sát"
            : "Nhu cầu trong mẫu tin tuyển dụng"
        }}</span
        ><span class="strip-right">Đơn vị: {{ unit(market) }}</span>
      </div>
      <div class="stat-grid" :class="{ dimmed: loading }">
        <section class="stat-card">
          <div>
            <span>Hồ sơ trong tập train</span
            ><span class="icon-tile mint"
              ><Icon name="Users" :size="19"
            /></span>
          </div>
          <strong>{{ number(data.samples) }}</strong>
          <p>Dữ liệu đã làm sạch, có nguồn</p>
        </section>
        <section class="stat-card">
          <div>
            <span>Thu nhập trung vị</span
            ><span class="icon-tile lime"
              ><Icon name="BarChart3" :size="19"
            /></span>
          </div>
          <strong>{{ money(data.median_salary, market) }}</strong>
          <p>{{ unit(market) }} · thu nhập quan sát</p>
        </section>
        <section class="stat-card">
          <div>
            <span>Kinh nghiệm trung vị</span
            ><span class="icon-tile peach"
              ><Icon name="Layers3" :size="19"
            /></span>
          </div>
          <strong>{{ number(data.median_experience, 1) }}<em>năm</em></strong>
          <p>Kinh nghiệm đã được chuẩn hóa</p>
        </section>
        <section class="stat-card">
          <div>
            <span>Khu vực được ghi nhận</span
            ><span class="icon-tile lavender"
              ><Icon name="Globe2" :size="19"
            /></span>
          </div>
          <strong>{{ number(data.locations) }}</strong>
          <p>
            {{
              market === "vietnam"
                ? "Địa điểm trong tin tuyển dụng"
                : "Quốc gia trong khảo sát"
            }}
          </p>
        </section>
      </div>
      <div class="overview-grid">
        <ChartGallery :charts="data.charts" observed />
        <section class="panel skills-panel">
          <div class="panel-head">
            <div>
              <span class="eyebrow">TECH STACK</span>
              <h3>Kỹ năng nổi bật</h3>
            </div>
            <span class="soft-badge">Top 8</span>
          </div>
          <p class="panel-subtitle">
            {{
              market === "vietnam"
                ? "Số tin có nhắc đến công nghệ"
                : "Số người cho biết đã sử dụng"
            }}
          </p>
          <div class="skill-bars">
            <div
              v-for="(skill, index) in data.top_skills.slice(0, 8)"
              :key="skill.skill"
              class="skill-bar"
            >
              <div>
                <span
                  ><i>{{ String(index + 1).padStart(2, "0") }}</i
                  >{{ skill.skill }}</span
                ><strong>{{ number(skill.count) }}</strong>
              </div>
              <div class="bar-track">
                <span
                  :style="{
                    width: (skill.count / data.top_skills[0].count) * 100 + '%',
                  }"
                ></span>
              </div>
            </div>
          </div>
          <button class="text-button" @click="$emit('navigate', 'data')">
            Khám phá dữ liệu <Icon name="ArrowRight" :size="17" />
          </button>
        </section>
      </div>
      <div class="bottom-grid">
        <section class="next-step">
          <div>
            <span class="eyebrow">BƯỚC TIẾP THEO CỦA BẠN</span>
            <h2>Kỹ năng hôm nay.<br />Cơ hội ngày mai.</h2>
            <p>
              Nhập vai trò, kinh nghiệm và kỹ năng.<br />Để Qwen ước tính lương
              và gợi ý hướng phát triển.
            </p>
            <button class="button light" @click="$emit('navigate', 'career')">
              Khám phá lộ trình của bạn <Icon name="ArrowUpRight" :size="17" />
            </button>
          </div>
          <div class="path-visual" aria-hidden="true">
            <span class="orbit one"></span><span class="orbit two"></span
            ><span class="orbit three"></span
            ><span class="path-node"><Icon name="Sparkles" :size="34" /></span
            ><span class="floating-chip">skills → next step</span>
          </div>
        </section>
        <section class="panel source-panel">
          <div class="panel-head">
            <h3>Đọc dữ liệu đúng ngữ cảnh</h3>
            <Icon name="CircleHelp" :size="19" />
          </div>
          <p>
            {{
              market === "vietnam"
                ? "Mức lương chào tuyển, chuẩn hóa theo tháng. Không gộp với thu nhập năm của khảo sát quốc tế."
                : "Tổng thu nhập tự khai theo năm. Mức sử dụng công nghệ không đồng nghĩa nhu cầu tuyển dụng."
            }}
          </p>
          <div class="source-fact">
            <Icon name="ShieldCheck" :size="18" /><span
              >Biểu đồ từ tập train. Test được giữ riêng để đánh giá
              model.</span
            >
          </div>
          <button class="text-button" @click="$emit('navigate', 'metrics')">
            Xem độ chính xác thực tế <Icon name="ArrowRight" :size="17" />
          </button>
        </section>
      </div>
    </template>
  </div>
</template>
