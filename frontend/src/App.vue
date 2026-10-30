<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { api } from "./api";
import Icon from "./components/Icon.vue";
import OverviewView from "./views/OverviewView.vue";
import DataView from "./views/DataView.vue";
import UploadView from "./views/UploadView.vue";
import CareerView from "./views/CareerView.vue";
import MetricsView from "./views/MetricsView.vue";
const navigation = [
  {
    id: "overview",
    title: "Tổng quan",
    icon: "LayoutDashboard",
    section: "KHÁM PHÁ",
  },
  { id: "data", title: "Dữ liệu thị trường", icon: "Database" },
  {
    id: "upload",
    title: "Phân tích file",
    icon: "FileSpreadsheet",
    section: "LÀM VIỆC VỚI AI",
  },
  { id: "career", title: "Tư vấn nghề nghiệp", icon: "Sparkles" },
  { id: "metrics", title: "Đánh giá mô hình", icon: "ChartNoAxesCombined" },
];
const validPage = (value) =>
  navigation.some((n) => n.id === value) ? value : "overview";
const current = ref(validPage(location.hash.slice(1))),
  market = ref(
    localStorage.getItem("career-market") === "international"
      ? "international"
      : "vietnam",
  );
const menuOpen = ref(false),
  health = ref(null),
  history = ref([]),
  job = ref(null),
  result = ref(null),
  toast = ref("");
const title = computed(
  () => navigation.find((n) => n.id === current.value)?.title,
);
let pollTimer,
  toastTimer,
  session = 0;
function navigate(id) {
  current.value = validPage(id);
  location.hash = current.value;
  menuOpen.value = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
}
function changeMarket(value) {
  market.value = value;
  localStorage.setItem("career-market", value);
}
function showError(message) {
  toast.value = message;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.value = ""), 8000);
}
async function loadHistory() {
  try {
    history.value = await api("/jobs");
  } catch (e) {
    showError(e.message);
  }
}
async function setJob(value) {
  clearTimeout(pollTimer);
  const token = ++session;
  job.value = value;
  result.value = null;
  localStorage.setItem("career-job", value.id);
  loadHistory();
  async function poll() {
    try {
      const next = await api(`/jobs/${value.id}`);
      if (token !== session) return;
      job.value = next;
      if (next.status === "completed") {
        const data = await api(`/jobs/${value.id}/results`);
        if (token !== session) return;
        result.value = data;
        loadHistory();
        return;
      }
      if (["failed", "interrupted"].includes(next.status)) {
        loadHistory();
        return;
      }
    } catch (e) {
      if (token === session) showError(e.message);
    }
    if (token === session) pollTimer = setTimeout(poll, 1500);
  }
  poll();
}
function openHistory(value) {
  navigate("upload");
  setJob(value);
}
function focusMain() {
  document.getElementById("main-content")?.focus();
}
function keyboard(event) {
  if (event.key === "Escape") menuOpen.value = false;
}
function hashChanged() {
  current.value = validPage(location.hash.slice(1));
  menuOpen.value = false;
}
onMounted(async () => {
  window.addEventListener("hashchange", hashChanged);
  window.addEventListener("keydown", keyboard);
  try {
    health.value = await api("/health");
  } catch (e) {
    showError(e.message);
  }
  await loadHistory();
  const saved = localStorage.getItem("career-job"),
    found = history.value.find((j) => j.id === saved);
  if (found) setJob(found);
});
onBeforeUnmount(() => {
  clearTimeout(pollTimer);
  clearTimeout(toastTimer);
  window.removeEventListener("hashchange", hashChanged);
  window.removeEventListener("keydown", keyboard);
});
</script>
<template>
  <a class="skip-link" href="#main-content" @click.prevent="focusMain"
    >Đi tới nội dung</a
  >
  <div class="app-shell">
    <div
      v-if="menuOpen"
      class="sidebar-backdrop"
      @click="menuOpen = false"
    ></div>
    <aside
      class="sidebar"
      :class="{ open: menuOpen }"
      aria-label="Điều hướng chính"
    >
      <a class="brand" href="#overview" @click.prevent="navigate('overview')"
        ><span class="brand-mark"><span></span><span></span><span></span></span
        ><span
          >CareerLens<span class="brand-period">.</span
          ><small>DATA. INSIGHT. DIRECTION.</small></span
        ></a
      >
      <div class="workspace-badge">
        <span class="workspace-icon"><Icon name="Layers3" :size="16" /></span>
        <div>Không gian phân tích<small>Thị trường việc làm CNTT</small></div>
        <span class="workspace-dot"></span>
      </div>
      <nav>
        <template v-for="item in navigation" :key="item.id"
          ><p v-if="item.section" class="nav-section">{{ item.section }}</p>
          <a
            :href="'#' + item.id"
            :class="{ active: current === item.id }"
            :aria-current="current === item.id ? 'page' : undefined"
            @click.prevent="navigate(item.id)"
            ><Icon :name="item.icon" :size="19" /><span>{{ item.title }}</span
            ><span v-if="item.id === 'upload'" class="nav-new">NEW</span
            ><span v-else-if="current === item.id" class="nav-dot"></span></a
        ></template>
      </nav>
      <div v-if="history.length" class="recent-jobs">
        <p class="nav-section">PHÂN TÍCH GẦN ĐÂY</p>
        <button
          v-for="item in history.slice(0, 3)"
          :key="item.id"
          @click="openHistory(item)"
          :title="item.filename"
        >
          <Icon
            :name="
              item.status === 'completed'
                ? 'CheckCircle2'
                : ['running', 'queued'].includes(item.status)
                  ? 'Clock3'
                  : 'XCircle'
            "
            :size="15"
          /><span>{{ item.filename }}</span>
        </button>
      </div>
      <div class="sidebar-bottom">
        <div class="ai-card">
          <span class="ai-chip"
            ><Icon name="Sparkles" :size="15" /> AI POWERED</span
          >
          <h3>Một góc nhìn mới<br />cho sự nghiệp của bạn.</h3>
          <p>Qwen3 đã fine-tune<br />trên dữ liệu việc làm.</p>
          <button @click="navigate('career')">
            Bắt đầu khám phá <Icon name="ArrowUpRight" :size="16" />
          </button>
        </div>
        <div class="sidebar-footer">
          <span class="avatar">CL</span>
          <div>CareerLens Workspace<small>Python + TensorFlow</small></div>
          <Icon name="ShieldCheck" :size="17" />
        </div>
      </div>
    </aside>
    <div class="main-shell">
      <header class="topbar">
        <div class="breadcrumb">
          <button
            class="mobile-menu"
            @click="menuOpen = !menuOpen"
            :aria-expanded="menuOpen"
            aria-label="Mở điều hướng"
          >
            <Icon name="Menu" /></button
          ><span>Workspace</span
          ><Icon name="ChevronRight" :size="14" /><strong>{{ title }}</strong>
        </div>
        <div class="topbar-actions">
          <span
            class="connection"
            :class="{ offline: !health?.model_available }"
            ><span class="dot"></span
            >{{
              health?.model_available ? "Model sẵn sàng" : "Đang kết nối…"
            }}</span
          ><span class="topbar-divider"></span
          ><span class="topbar-avatar">CL</span>
        </div>
      </header>
      <main id="main-content" tabindex="-1">
        <div class="scope-toolbar">
          <div class="scope-label">
            <Icon name="Globe2" :size="16" /> Phạm vi dữ liệu
          </div>
          <div class="segment market-segment">
            <button
              :class="{ selected: market === 'vietnam' }"
              @click="changeMarket('vietnam')"
            >
              <span class="market-dot vn"></span>Việt Nam
              <small>VND/tháng</small></button
            ><button
              :class="{ selected: market === 'international' }"
              @click="changeMarket('international')"
            >
              <Icon name="Globe2" :size="14" />Quốc tế <small>USD/năm</small>
            </button>
          </div>
          <span class="scope-hint"
            ><Icon name="Database" :size="14" /> Dữ liệu đã chuẩn hóa</span
          >
        </div>
        <OverviewView
          v-if="current === 'overview'"
          :market="market"
          @navigate="navigate"
        />
        <DataView v-else-if="current === 'data'" :market="market" />
        <UploadView
          v-else-if="current === 'upload'"
          :market="market"
          :job="job"
          :result="result"
          @job="setJob"
        />
        <CareerView
          v-else-if="current === 'career'"
          :market="market"
          :job="job"
          :result="result"
          @job="setJob"
        />
        <MetricsView v-else-if="current === 'metrics'" :market="market" />
      </main>
      <footer class="main-footer">
        <span>CareerLens <span>© 2026</span></span
        ><span>Dữ liệu rõ nguồn. Kết quả rõ giới hạn.</span
        ><a href="/docs" target="_blank" rel="noopener"
          >API Documentation <Icon name="ArrowUpRight" :size="13"
        /></a>
      </footer>
    </div>
    <div v-if="toast" class="toast" role="alert">
      <Icon name="CircleHelp" :size="18" /><span>{{ toast }}</span
      ><button @click="toast = ''" aria-label="Đóng thông báo">
        <Icon name="X" :size="17" />
      </button>
    </div>
  </div>
</template>
