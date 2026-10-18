<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import ResearchDashboard from "./ResearchDashboard.vue";
import ModelComparison from "./ModelComparison.vue";
const page = ref("research"),
  meta = ref(null),
  dataset = ref(null),
  mapping = ref({});
const research = ref(null),
  researchError = ref(""),
  benchmarkId = ref("global_survey"),
  internationalMeta = ref(null);
const uploadMarket = ref("international_survey"),
  profileMarket = ref("international_survey"),
  researchMarket = ref("international_survey");
const error = ref(""),
  busy = ref(false),
  job = ref(null),
  rows = ref([]),
  offset = ref(0);
const resultTab = ref("overview"),
  salarySource = ref("observed"),
  profileBusy = ref(false),
  advice = ref(null);
const useGemma = ref(false),
  currency = ref(""),
  period = ref(""),
  scale = ref(1);
const profile = ref({
  role: "Backend Developer",
  level: "Junior",
  experience_years: 3,
  location: "Hà Nội",
  skills: "Python, SQL",
  country: "United States of America",
});
let timer = null;
let pollRevision = 0;
let rowsRevision = 0;
let profileRevision = 0;
watch(
  profile,
  () => {
    // Every displayed prediction belongs to the submitted profile, never a newer edit.
    profileRevision++;
    advice.value = null;
    profileBusy.value = false;
  },
  { deep: true, flush: "sync" },
);
const labels = {
  country: "Quốc gia",
  title: "Chức danh",
  role: "Vai trò",
  level: "Cấp bậc",
  experience_years: "Kinh nghiệm",
  location: "Khu vực",
  skills: "Kỹ năng",
  salary: "Lương cung cấp",
  posted_date: "Ngày đăng",
  description: "Mô tả tuyển dụng",
};
const icons = {
  research: "M3 20V9h4v11m3 0V3h4v17m3 0v-8h4v8",
  models: "M4 4h16v16H4zM8 16v-4m4 4V8m4 8v-6",
  upload: "M12 16V4m-4 4 4-4 4 4M4 16v4h16v-4",
  results: "M4 20V10h4v10m4 0V4h4v16m4 0v-7h3",
  advice: "M9 18h6m-5 3h4M8 14a6 6 0 1 1 8 0l-1 2H9z",
};
const result = computed(() =>
  job.value?.status === "completed" ? job.value.result : null,
);
const running = computed(() =>
  ["queued", "running"].includes(job.value?.status),
);
const canAnalyze = computed(
  () =>
    dataset.value &&
    !busy.value &&
    !running.value &&
    (uploadMarket.value !== "international_survey" || mapping.value.country) &&
    (mapping.value.role ||
      mapping.value.title ||
      (mapping.value.description && useGemma.value)),
);
const charts = computed(() =>
  (result.value?.charts || []).filter(
    (c) =>
      c.id === "actual_predicted" ||
      (!c.id.endsWith("_observed") && !c.id.endsWith("_predicted")) ||
      c.id.endsWith("_" + salarySource.value),
  ),
);
const modelLabel = (name) =>
  name === "ridge"
    ? "Ridge"
    : name === "random_forest"
      ? "Random Forest"
      : "Đang tải";
const comparisonFamily = (name) =>
  name === "ridge" ? "random_forest" : "ridge";
const benchmarks = computed(() =>
  research.value
    ? [
        research.value.benchmark,
        ...(research.value.additional_benchmarks || []),
      ]
    : [],
);
const selectedBenchmark = computed(
  () =>
    benchmarks.value.find((b) => b.id === benchmarkId.value) ||
    benchmarks.value[0],
);
const selectedResearch = computed(() =>
  researchMarket.value === "international_survey" &&
  research.value?.international
    ? research.value.international
    : research.value,
);
const visibleModel = computed(() =>
  page.value === "results" && result.value
    ? result.value.model.selected_model
    : page.value === "advice"
      ? advice.value?.selected_model ||
        (profileMarket.value === "international_survey"
          ? internationalMeta.value?.selected_model
          : meta.value?.salary_model.selected_model)
      : (page.value === "upload" || page.value === "results") &&
          uploadMarket.value === "international_survey"
        ? internationalMeta.value?.selected_model
        : meta.value?.salary_model.selected_model,
);
const currentUnit = computed(() =>
  page.value === "results" && result.value
    ? result.value.unit || "VND/month"
    : (page.value === "advice" &&
          profileMarket.value === "international_survey") ||
        (page.value === "results" &&
          uploadMarket.value === "international_survey")
      ? "USD/year"
      : "VND/month",
);
const unitLabel = computed(() =>
  currentUnit.value === "USD/year" ? "nghìn USD/năm" : "triệu VND/tháng",
);
const shortUnit = computed(() =>
  currentUnit.value === "USD/year" ? "nghìn USD" : "triệu VND",
);
const money = (n) =>
  n == null
    ? "—"
    : new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 1 }).format(
        n / (currentUnit.value === "USD/year" ? 1000 : 1e6),
      );
const prediction = (row, kind = "selected") => {
  const suffix = result.value?.unit === "USD/year" ? "usd_year" : "vnd";
  return row[
    (kind === "selected"
      ? "predicted"
      : kind === "comparison"
        ? "comparison"
        : kind) +
      "_salary_" +
      suffix
  ];
};
const observedSalary = (row) =>
  result.value?.unit === "USD/year"
    ? row.salary_annual_usd
    : row.salary_monthly_vnd;
const profileRoles = computed(() =>
  profileMarket.value === "international_survey"
    ? internationalMeta.value?.roles || []
    : meta.value?.salary_model.roles || [],
);
const pageInfo = computed(
  () =>
    ({
      research: [
        "Xu hướng & kỹ năng",
        "Phân tích thị trường việc làm CNTT",
        "Nhu cầu công nghệ, mức lương, kinh nghiệm, vai trò và khu vực từ dữ liệu có nguồn.",
      ],
      models: [
        "So sánh mô hình",
        "Đánh giá Ridge và Random Forest",
        "So sánh MAE, RMSE và R² trên cùng tập test; chọn đúng nhánh dữ liệu và đơn vị.",
      ],
      upload: [
        "Phân tích file",
        "Nhập và chuẩn hóa dữ liệu",
        "CSV, Excel hoặc JSON → ghép cột → dự đoán từng dòng → biểu đồ và xuất kết quả.",
      ],
      results: [
        "Kết quả của file",
        "Kết quả phân tích dữ liệu đã nhập",
        "Phân biệt lương cung cấp, dự đoán và sai số trên bảng nhập với test đã lưu.",
      ],
      advice: [
        "Dự đoán & tư vấn",
        "Dự đoán lương và gợi ý kỹ năng",
        "Chọn thị trường, nhập hồ sơ và xem gợi ý có số mẫu hỗ trợ từ train.",
      ],
    })[page.value],
);
async function loadResearch() {
  researchError.value = "";
  try {
    research.value = await api("/api/research");
  } catch (e) {
    researchError.value = e.message;
  }
}
function changeProfileMarket() {
  profileRevision++;
  advice.value = null;
  profileBusy.value = false;
  const roles = profileRoles.value;
  profile.value.role =
    roles.find((r) => r.toLowerCase().includes("back-end")) ||
    roles.find((r) => r === "Backend Developer") ||
    roles[0] ||
    "";
}
watch(uploadMarket, () => {
  useGemma.value = false;
  currency.value = uploadMarket.value === "international_survey" ? "USD" : "";
  period.value = uploadMarket.value === "international_survey" ? "year" : "";
  scale.value = 1;
});
watch(profileMarket, changeProfileMarket);
const integer = (n) => new Intl.NumberFormat("vi-VN").format(n ?? 0);
const artifact = (name) =>
  `/api/analyses/${job.value.id}/artifacts/${encodeURIComponent(name)}`;
async function api(url, options = {}) {
  const response = await fetch(url, options);
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(
      "Không đọc được phản hồi máy chủ. Kiểm tra kết nối rồi thử lại.",
    );
  }
  if (!response.ok)
    throw new Error(
      Array.isArray(data.detail)
        ? data.detail.map((x) => x.msg).join("; ")
        : data.detail || "Yêu cầu chưa thực hiện được",
    );
  return data;
}
function acceptDataset(data) {
  dataset.value = data;
  mapping.value = {
    ...Object.fromEntries(Object.keys(labels).map((k) => [k, ""])),
    ...data.suggested_mapping,
  };
  page.value = "upload";
  uploadMarket.value = data.suggested_mapping.country
    ? "international_survey"
    : "vietnam_offers";
  currency.value = uploadMarket.value === "international_survey" ? "USD" : "";
  period.value = uploadMarket.value === "international_survey" ? "year" : "";
  scale.value = 1;
  useGemma.value = false;
}
async function upload(file) {
  if (!file || busy.value) return;
  error.value = "";
  busy.value = true;
  try {
    if (file.size > 10 * 1024 * 1024)
      throw new Error("File vượt 10 MiB. Hãy giảm kích thước bảng.");
    const form = new FormData();
    form.append("file", file);
    acceptDataset(await api("/api/datasets", { method: "POST", body: form }));
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
async function demo() {
  error.value = "";
  busy.value = true;
  try {
    acceptDataset(
      await api(`/api/datasets/demo?market=${uploadMarket.value}`, {
        method: "POST",
      }),
    );
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
async function refreshGpuStatus() {
  try {
    meta.value = await api("/api/meta");
  } catch (e) {
    error.value = e.message;
  }
}
async function analyze() {
  clearTimeout(timer);
  pollRevision++;
  rowsRevision++;
  rows.value = [];
  error.value = "";
  busy.value = true;
  try {
    if (useGemma.value) {
      meta.value = await api("/api/meta");
      if (meta.value.gemma.training_check_error)
        throw new Error(
          "Chưa kiểm tra được GPU. Hãy thử lại hoặc bỏ chọn Gemma nếu bảng đã có cột chuẩn.",
        );
      if (!meta.value.gemma.available)
        throw new Error("Chưa có trọng số Gemma trên máy này.");
      if (meta.value.gemma.training_active || meta.value.gemma.gpu_busy)
        throw new Error(
          "GPU đang train, đánh giá hoặc suy luận Gemma. Chờ hoàn tất hoặc bỏ chọn Gemma nếu bảng đã có cột chuẩn.",
        );
    }
    job.value = await api("/api/analyses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset_id: dataset.value.dataset_id,
        mapping: mapping.value,
        currency: currency.value || null,
        period: period.value || null,
        salary_scale: Number(scale.value),
        use_gemma: useGemma.value,
        market: uploadMarket.value,
      }),
    });
    localStorage.setItem("career-last-job", job.value.id);
    page.value = "results";
    resultTab.value = "overview";
    offset.value = 0;
    await poll();
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
async function poll() {
  clearTimeout(timer);
  const revision = ++pollRevision;
  const identifier = job.value.id;
  try {
    const state = await api(`/api/analyses/${identifier}`);
    if (revision !== pollRevision || identifier !== job.value?.id) return;
    job.value = state;
    if (running.value) timer = setTimeout(() => poll(), 1100);
    else if (job.value.status === "completed") {
      salarySource.value = result.value.summary.labeled
        ? "observed"
        : "predicted";
      await loadRows(0);
    } else error.value = job.value.error;
  } catch (e) {
    if (revision !== pollRevision || identifier !== job.value?.id) return;
    error.value = e.message;
    job.value = {
      ...job.value,
      status: "failed",
      error:
        "Chưa đọc được trạng thái máy chủ. Kết quả có thể vẫn đang xử lý; chọn kiểm tra lại.",
    };
  }
}
async function loadRows(value) {
  const revision = ++rowsRevision;
  const identifier = job.value.id;
  error.value = "";
  try {
    const data = await api(
      `/api/analyses/${identifier}/rows?offset=${value}&limit=25`,
    );
    if (revision !== rowsRevision || identifier !== job.value?.id) return;
    rows.value = data.rows;
    offset.value = value;
  } catch (e) {
    if (revision === rowsRevision && identifier === job.value?.id)
      error.value = e.message;
  }
}
async function getAdvice() {
  const revision = ++profileRevision;
  advice.value = null;
  error.value = "";
  profileBusy.value = true;
  try {
    const data = await api("/api/career/advice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...profile.value,
        market: profileMarket.value,
        experience_years:
          profile.value.experience_years === ""
            ? null
            : Number(profile.value.experience_years),
        skills: profile.value.skills
          .split(/[,;\n]/)
          .map((x) => x.trim())
          .filter(Boolean),
      }),
    });
    if (revision === profileRevision) advice.value = data;
  } catch (e) {
    if (revision === profileRevision) error.value = e.message;
  } finally {
    if (revision === profileRevision) profileBusy.value = false;
  }
}
onMounted(async () => {
  loadResearch();
  try {
    internationalMeta.value = await api("/api/international/meta");
    changeProfileMarket();
  } catch (e) {
    researchError.value = e.message;
  }
  try {
    meta.value = await api("/api/meta");
    const previous = localStorage.getItem("career-last-job");
    if (previous) {
      job.value = { id: previous };
      try {
        await poll();
      } catch {
        localStorage.removeItem("career-last-job");
      }
    }
  } catch (e) {
    error.value = e.message;
  }
});
onBeforeUnmount(() => {
  clearTimeout(timer);
  pollRevision++;
  rowsRevision++;
  profileRevision++;
});
</script>

<template>
  <div class="workspace">
    <aside class="sidebar">
      <a
        class="brand"
        href="#"
        @click.prevent="page = 'research'"
        aria-label="IT Career Insight, trang phân tích thị trường"
      >
        <span class="brand-mark"><i></i><i></i><i></i></span
        ><span
          >career<span class="brand-light">insight</span
          ><small>THỊ TRƯỜNG VIỆC LÀM CNTT</small></span
        >
      </a>
      <span class="nav-caption">KHÔNG GIAN LÀM VIỆC</span>
      <nav aria-label="Điều hướng chính">
        <button
          v-for="[id, title] in [
            ['research', 'Xu hướng & kỹ năng'],
            ['models', 'So sánh mô hình'],
            ['advice', 'Dự đoán & tư vấn'],
            ['upload', 'Phân tích file'],
            ['results', 'Kết quả của file'],
          ]"
          :key="id"
          :class="{ selected: page === id }"
          @click="page = id"
          :aria-current="page === id ? 'page' : undefined"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.6"
            aria-hidden="true"
          >
            <path :d="icons[id]" /></svg
          >{{ title
          }}<span v-if="id === 'results' && result" class="nav-dot"></span>
        </button>
      </nav>
      <div class="sidebar-note">
        <span class="small-dot"></span>Phân tích trên máy của bạn
        <p>
          Dữ liệu nhập được lưu local.<br />Model chạy suy luận khi bạn yêu cầu.
        </p>
      </div>
      <div class="sidebar-bottom">
        <span class="project-number">04</span>
        <div>
          Đề tài phân tích dữ liệu<small>Python · AI / Machine Learning</small>
        </div>
      </div>
    </aside>
    <main>
      <header class="topbar">
        <div class="breadcrumb">
          IT Career Insight <span>/</span>
          {{ pageInfo[0] }}
        </div>
        <span class="local-badge"><i></i>Local workspace</span>
      </header>
      <div class="content">
        <div class="page-heading">
          <div>
            <div class="eyebrow">
              ĐỀ TÀI 04 · PHÂN TÍCH DỮ LIỆU & MACHINE LEARNING
            </div>
            <h1>{{ pageInfo[1] }}</h1>
            <p>{{ pageInfo[2] }}</p>
          </div>
          <div
            v-if="!['research', 'models'].includes(page)"
            class="model-badge"
          >
            <span>MÔ HÌNH DỰ ĐOÁN</span
            ><strong>{{ modelLabel(visibleModel) }}</strong
            ><small>{{
              page === "upload"
                ? uploadMarket === "international_survey"
                  ? "USD / năm"
                  : "VND / tháng"
                : unitLabel
            }}</small>
          </div>
        </div>
        <div v-if="error" class="alert error" role="alert">
          <strong>Chưa thực hiện được.</strong> {{ error }}
          <button
            class="dismiss"
            @click="error = ''"
            aria-label="Đóng thông báo"
          >
            ×
          </button>
        </div>
        <template v-if="page === 'research' || page === 'models'">
          <div v-if="researchError" class="info-note" role="alert">
            {{ researchError }}
            <button class="text-button" @click="loadResearch">
              Tải lại dữ liệu
            </button>
          </div>
          <template v-if="research">
            <template v-if="page === 'research'">
              <label class="context-picker"
                >Tập dữ liệu phân tích<select v-model="researchMarket">
                  <option
                    value="international_survey"
                    :disabled="!research.international"
                  >
                    Khảo sát lập trình viên quốc tế · USD/năm
                  </option>
                  <option value="vietnam_offers">
                    Tin tuyển dụng Việt Nam · VND/tháng
                  </option>
                </select></label
              >
              <ResearchDashboard
                :data="selectedResearch"
                @upload="page = 'upload'"
                @advice="page = 'advice'"
                @models="page = 'models'"
              />
            </template>
            <template v-else>
              <label class="context-picker"
                >Bài toán / tập đánh giá<select v-model="benchmarkId">
                  <option v-for="b in benchmarks" :key="b.id" :value="b.id">
                    {{ b.title }}
                  </option>
                </select></label
              >
              <ModelComparison
                v-if="selectedBenchmark"
                :metrics="selectedBenchmark.metrics"
                :selected="selectedBenchmark.selected_model"
                :unit="selectedBenchmark.unit"
                :scope="selectedBenchmark.scope"
              />
              <div class="research-notice" v-if="selectedBenchmark">
                <strong>Chọn bằng validation.</strong>
                {{ selectedBenchmark.selection_note }}
                {{ selectedBenchmark.limits }}
              </div>
              <div class="analysis-next">
                <p>
                  <strong>Áp dụng vào hồ sơ</strong><br />Sai số test là kết quả
                  của tập đánh giá, không phải cam kết sai số cho mọi người
                  dùng.
                </p>
                <button class="primary" @click="page = 'advice'">
                  Dự đoán & tư vấn →
                </button>
              </div>
            </template>
          </template>
          <section
            v-else-if="!researchError"
            class="panel loading-research"
            role="status"
          >
            Đang đọc dữ liệu phân tích và kết quả đánh giá đã lưu…
          </section>
        </template>
        <template v-else-if="page === 'upload'">
          <label class="context-picker"
            >Nhánh mô hình cho file<select v-model="uploadMarket">
              <option value="international_survey">
                Khảo sát quốc tế · tổng thu nhập USD/năm
              </option>
              <option value="vietnam_offers">
                Tin tuyển dụng Việt Nam · lương chào tuyển VND/tháng
              </option>
            </select></label
          >
          <p
            v-if="uploadMarket === 'international_survey'"
            class="context-help"
          >
            Cần vai trò và quốc gia; nhận số năm kinh nghiệm và kỹ năng. Nhánh
            này dùng các cột có sẵn, không dùng adapter Gemma tin Việt Nam.
          </p>
          <div class="steps">
            <span class="active"><b>01</b> Nhập bảng</span><i></i
            ><span :class="{ active: dataset }"
              ><b>02</b> Kiểm tra & ghép cột</span
            ><i></i
            ><span :class="{ active: result }"
              ><b>03</b> Phân tích & xuất kết quả</span
            >
          </div>
          <section class="panel import-panel">
            <div class="panel-heading">
              <div>
                <h2>Đưa dữ liệu của bạn vào</h2>
                <p>
                  Mỗi dòng là một tin tuyển dụng hoặc một hồ sơ cần ước tính
                  lương.
                </p>
              </div>
              <span class="pill neutral">CSV · XLSX · JSON</span>
            </div>
            <div class="import-layout">
              <label
                class="dropzone"
                @dragover.prevent
                @drop.prevent="upload($event.dataTransfer.files[0])"
              >
                <input
                  type="file"
                  accept=".csv,.xlsx,.json"
                  aria-label="Chọn bảng dữ liệu CSV, XLSX hoặc JSON"
                  @change="upload($event.target.files[0])"
                  :disabled="busy || running"
                />
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.4"
                  aria-hidden="true"
                >
                  <path
                    d="M8 3H5v18h14V7l-4-4H8m6 0v5h5M12 17v-6m-3 3 3-3 3 3"
                  />
                </svg>
                <strong>{{
                  busy
                    ? "Đang đọc bảng dữ liệu…"
                    : dataset
                      ? dataset.filename
                      : "Kéo thả file vào đây"
                }}</strong
                ><span>hoặc chọn file từ máy tính</span
                ><small
                  >Tối đa 10 MiB · 2.000 dòng · Sheet đầu tiên của XLSX</small
                >
              </label>
              <div class="import-help">
                <span class="eyebrow">BẠN SẼ NHẬN ĐƯỢC</span>
                <ul>
                  <li>
                    <b>01</b>
                    <div>
                      Dự đoán mức lương<small
                        >Theo vai trò, kinh nghiệm, kỹ năng và khu vực</small
                      >
                    </div>
                  </li>
                  <li>
                    <b>02</b>
                    <div>
                      {{
                        uploadMarket === "international_survey"
                          ? "Kỹ năng và thu nhập khảo sát"
                          : "Bức tranh nhu cầu tuyển dụng"
                      }}<small
                        >Biểu đồ kỹ năng, thu nhập và phân bố công việc</small
                      >
                    </div>
                  </li>
                  <li>
                    <b>03</b>
                    <div>
                      Kết quả để mang đi<small
                        >Bảng CSV / Excel và bộ biểu đồ PNG</small
                      >
                    </div>
                  </li>
                </ul>
                <button
                  class="text-button"
                  @click="demo"
                  :disabled="busy || running"
                >
                  Thử với 48 mẫu có sẵn <span>↗</span>
                </button>
              </div>
            </div>
          </section>
          <template v-if="dataset">
            <section class="panel">
              <div class="panel-heading">
                <div>
                  <h2>
                    Kiểm tra dữ liệu
                    <span class="pill"
                      >{{ integer(dataset.row_count) }} dòng</span
                    >
                  </h2>
                  <p>
                    {{ dataset.filename }} · {{ dataset.columns.length }} cột
                  </p>
                </div>
                <span class="pill neutral"
                  >Xem trước {{ dataset.preview.length }} dòng</span
                >
              </div>
              <div class="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th v-for="column in dataset.columns" :key="column">
                        {{ column }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, i) in dataset.preview" :key="i">
                      <td
                        v-for="column in dataset.columns"
                        :key="column"
                        class="preview-cell"
                        :title="String(row[column] ?? '')"
                      >
                        {{
                          Array.isArray(row[column])
                            ? row[column].join(", ")
                            : (row[column] ?? "—")
                        }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="source-note">{{ dataset.provenance }}</div>
            </section>
            <section class="panel">
              <div class="panel-heading">
                <div>
                  <h2>Ghép cột với thông tin cần phân tích</h2>
                  <p>
                    Gợi ý đã được điền sẵn. Bạn có thể chọn lại theo cấu trúc
                    bảng của mình.
                  </p>
                </div>
              </div>
              <div class="mapping-grid">
                <label v-for="(label, key) in labels" :key="key"
                  >{{ label
                  }}<select v-model="mapping[key]">
                    <option value="">Không có cột này</option>
                    <option
                      v-for="column in dataset.columns"
                      :key="column"
                      :value="column"
                    >
                      {{ column }}
                    </option>
                  </select></label
                >
              </div>
              <div
                v-if="mapping.salary && mapping.salary !== 'salary_monthly_vnd'"
                class="unit-controls"
              >
                <div>
                  <strong>Đơn vị của cột lương</strong
                  ><small
                    >Chọn cho giá trị số chưa ghi rõ đơn vị. Thông tin ghi trong
                    chuỗi được ưu tiên.</small
                  >
                </div>
                <label
                  >Tiền tệ<select v-model="currency">
                    <option value="">Chưa xác định</option>
                    <option>VND</option>
                    <option>USD</option>
                    <option>EUR</option>
                  </select></label
                ><label
                  >Kỳ lương<select v-model="period">
                    <option value="">Chưa xác định</option>
                    <option value="month">Tháng</option>
                    <option value="year">Năm</option>
                  </select></label
                ><label
                  >Đơn vị số<select v-model="scale">
                    <option :value="1">Nguyên đơn vị tiền</option>
                    <option :value="1000000">Triệu đơn vị tiền</option>
                  </select></label
                >
              </div>
              <div class="run-controls">
                <div v-if="uploadMarket === 'vietnam_offers'">
                  <label class="checkbox"
                    ><input
                      type="checkbox"
                      v-model="useGemma"
                      :disabled="
                        !mapping.description ||
                        uploadMarket === 'international_survey' ||
                        !meta?.gemma.available ||
                        meta?.gemma.training_active ||
                        meta?.gemma.gpu_busy
                      "
                    />Dùng Gemma đọc cột mô tả</label
                  ><small>{{
                    meta?.gemma.training_check_error
                      ? "Không kiểm tra được GPU; chạy app từ Terminal rồi thử lại."
                      : meta?.gemma.training_active || meta?.gemma.gpu_busy
                        ? "GPU đang train/đánh giá/suy luận; chờ hoàn tất để dùng Gemma."
                        : !meta?.gemma.available
                          ? "Chưa có trọng số Gemma trên máy."
                          : "Tối đa 20 mô tả/lượt. Bảng đã có cột chuẩn có thể phân tích trực tiếp."
                  }}</small>
                  <button class="text-button" @click="refreshGpuStatus">
                    Kiểm tra lại GPU
                  </button>
                </div>
                <button
                  class="primary"
                  :disabled="!canAnalyze"
                  @click="analyze"
                >
                  {{ running ? "Đang phân tích…" : "Phân tích bảng dữ liệu" }}
                  <span>→</span>
                </button>
              </div>
            </section>
          </template>
          <div class="template-downloads">
            Tải bảng mẫu:
            <a
              :href="`/api/templates/${uploadMarket === 'international_survey' ? 'international_demo' : 'application_demo'}.csv`"
              download
              >CSV ↓</a
            ><a
              :href="`/api/templates/${uploadMarket === 'international_survey' ? 'international_demo' : 'application_demo'}.xlsx`"
              download
              >Excel ↓</a
            ><a
              :href="`/api/templates/${uploadMarket === 'international_survey' ? 'international_demo' : 'application_demo'}.json`"
              download
              >JSON ↓</a
            ><small
              >48 mẫu từ train; dùng minh họa chức năng, không phải test độc
              lập.</small
            >
          </div>
          <div class="bottom-note">
            <span>Không có cột lương?</span> Bạn vẫn có thể dự đoán. Chỉ tính
            sai số khi bảng có nhãn đúng đơn vị của nhánh đã chọn.
          </div>
        </template>
        <template v-else-if="page === 'results'">
          <section
            v-if="running"
            class="panel job-progress"
            role="status"
            aria-live="polite"
          >
            <div class="spinner"></div>
            <h2>{{ job.stage }}</h2>
            <p>Đang xử lý dữ liệu và tạo kết quả của bạn.</p>
            <progress :value="job.progress" max="100"></progress
            ><small>{{ job.progress }}%</small>
          </section>
          <section v-else-if="!result" class="panel empty-state">
            <div class="empty-icon">↗</div>
            <h2>
              {{
                job?.status === "failed"
                  ? "Lượt phân tích chưa hoàn tất"
                  : "Bảng dữ liệu đầu tiên đang chờ bạn"
              }}
            </h2>
            <p>
              {{
                job?.error ||
                "Nhập một bảng hoặc thử dữ liệu có sẵn để khám phá kết quả."
              }}
            </p>
            <button class="primary" @click="page = 'upload'">
              Đến phần nhập dữ liệu →</button
            ><button
              v-if="job?.id"
              class="text-button retry-button"
              @click="poll"
            >
              Kiểm tra lại kết quả
            </button>
          </section>
          <template v-else>
            <div class="result-toolbar">
              <div>
                <span class="file-label">▤ {{ result.filename }}</span
                ><small>{{ result.provenance }}</small>
              </div>
              <a class="primary" :href="artifact('analysis.zip')" download
                >Tải toàn bộ kết quả <span>↓</span></a
              >
            </div>
            <div class="stat-grid">
              <div>
                <span>DÒNG ĐÃ PHÂN TÍCH</span
                ><strong
                  >{{ integer(result.summary.predicted)
                  }}<small> / {{ integer(result.summary.rows) }}</small></strong
                >
                <p>
                  {{ result.summary.invalid }} dòng lỗi ·
                  {{ result.summary.duplicates }} dòng trùng
                </p>
              </div>
              <div>
                <span>TRUNG VỊ LƯƠNG DỰ ĐOÁN</span
                ><strong
                  >{{
                    money(
                      result.summary.median_prediction_usd_year ??
                        result.summary.median_prediction_vnd,
                    )
                  }}
                  <small>{{ shortUnit }}</small></strong
                >
                <p>
                  {{ modelLabel(result.model.selected_model) }} ·
                  {{ unitLabel }}
                </p>
              </div>
              <div>
                <span>KỸ NĂNG ĐƯỢC GHI NHẬN</span
                ><strong>{{ integer(result.summary.skill_count) }}</strong>
                <p>
                  Từ {{ integer(result.summary.unique_jobs) }}
                  {{ result.unit === "USD/year" ? "hồ sơ" : "tin" }} không trùng
                </p>
              </div>
              <div>
                <span>DÒNG CÓ LƯƠNG ĐỐI CHIẾU</span
                ><strong>{{ integer(result.summary.labeled) }}</strong>
                <p>Đúng đơn vị của nhánh đã chọn</p>
              </div>
            </div>
            <div class="result-tabs" role="tablist" aria-label="Phần kết quả">
              <button
                v-for="[id, title] in [
                  ['overview', 'Tổng quan dữ liệu'],
                  ['rows', 'Dự đoán từng dòng'],
                  ['quality', 'Chất lượng & sai số'],
                ]"
                :key="id"
                role="tab"
                :aria-selected="resultTab === id"
                :class="{ active: resultTab === id }"
                @click="resultTab = id"
              >
                {{ title }}
              </button>
            </div>
            <template v-if="resultTab === 'overview'"
              ><div class="section-heading">
                <div>
                  <h2>
                    {{
                      result.unit === "USD/year"
                        ? "Kỹ năng & thu nhập khảo sát"
                        : "Nhu cầu kỹ năng & thu nhập"
                    }}
                  </h2>
                  <p>
                    Các biểu đồ được tính từ bảng nhập, đã loại bản trùng hoàn
                    toàn.
                  </p>
                </div>
                <label class="chart-source"
                  >Nguồn lương<select v-model="salarySource">
                    <option
                      value="observed"
                      :disabled="!result.summary.labeled"
                    >
                      Lương cung cấp
                    </option>
                    <option value="predicted">
                      Lương dự đoán
                      {{ modelLabel(result.model.selected_model) }}
                    </option>
                  </select></label
                >
              </div>
              <div class="chart-grid">
                <article
                  v-for="chart in charts"
                  :key="chart.id"
                  class="panel chart-panel"
                >
                  <div>
                    <h3>{{ chart.title }}</h3>
                    <a
                      :href="artifact(chart.file)"
                      :download="chart.file"
                      aria-label="Tải ảnh biểu đồ"
                      title="Tải PNG"
                      >↓</a
                    >
                  </div>
                  <img
                    :src="artifact(chart.file)"
                    :alt="chart.title"
                    loading="lazy"
                  />
                  <p>{{ chart.caption }}</p>
                </article>
              </div></template
            >
            <section v-else-if="resultTab === 'rows'" class="panel">
              <div class="panel-heading">
                <div>
                  <h2>Dự đoán cho từng dòng</h2>
                  <p>
                    Chênh lệch = dự đoán
                    {{ modelLabel(result.model.selected_model) }} − lương cung
                    cấp. Chọn trạng thái để đọc lỗi hoặc cảnh báo.
                  </p>
                </div>
                <div class="download-links">
                  <a :href="artifact('results.csv')" download>CSV ↓</a
                  ><a :href="artifact('results.xlsx')" download>Excel ↓</a>
                </div>
              </div>
              <div class="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Dòng</th>
                      <th>Vai trò</th>
                      <th>Kinh nghiệm</th>
                      <th>Quốc gia / khu vực</th>
                      <th>Kỹ năng</th>
                      <th>
                        {{ modelLabel(result.model.selected_model) }} ·
                        {{ unitLabel }}
                      </th>
                      <th>
                        {{
                          modelLabel(
                            comparisonFamily(result.model.selected_model),
                          )
                        }}
                        · {{ unitLabel }}
                      </th>
                      <th>Cung cấp</th>
                      <th>Chênh lệch</th>
                      <th v-if="result.gemma_execution?.used">Gemma đọc tin</th>
                      <th>Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in rows" :key="row.source_row">
                      <td>{{ row.source_row }}</td>
                      <td>
                        {{ row.role || "—" }}<small>{{ row.level }}</small>
                      </td>
                      <td>{{ row.experience_years ?? "—" }}</td>
                      <td>{{ row.country || row.location || "—" }}</td>
                      <td class="skills-cell">
                        {{ row.skills.join(", ") || "—" }}
                      </td>
                      <td class="number">
                        {{ money(prediction(row)) }}
                      </td>
                      <td>
                        {{ money(prediction(row, "comparison")) }}
                      </td>
                      <td>{{ money(observedSalary(row)) }}</td>
                      <td>{{ money(row.error_usd_year ?? row.error_vnd) }}</td>
                      <td v-if="result.gemma_execution?.used">
                        <span
                          class="pill"
                          :class="row.gemma_status === 'failed' ? 'bad' : ''"
                        >
                          {{
                            row.gemma_status === "succeeded"
                              ? "Đã trích xuất"
                              : row.gemma_status === "failed"
                                ? "Trích xuất lỗi"
                                : "Không dùng"
                          }}
                        </span>
                      </td>
                      <td>
                        <details
                          v-if="row.errors.length || row.warnings.length"
                          class="row-details"
                        >
                          <summary>
                            <span
                              class="pill"
                              :class="
                                row.status === 'invalid' ? 'bad' : 'warning'
                              "
                              >{{
                                row.status === "invalid" ? "Lỗi" : "Cần xem"
                              }}</span
                            >
                          </summary>
                          <ul>
                            <li
                              v-for="note in [...row.errors, ...row.warnings]"
                              :key="note"
                            >
                              {{ note }}
                            </li>
                          </ul>
                        </details>
                        <span v-else class="pill">Hoàn tất</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="pagination">
                <span
                  >{{ offset + 1 }}–{{
                    Math.min(offset + 25, result.summary.rows)
                  }}
                  / {{ result.summary.rows }} dòng</span
                ><button
                  class="secondary"
                  @click="loadRows(offset - 25)"
                  :disabled="offset === 0"
                >
                  ← Trước</button
                ><button
                  class="secondary"
                  @click="loadRows(offset + 25)"
                  :disabled="offset + 25 >= result.summary.rows"
                >
                  Sau →
                </button>
              </div>
            </section>
            <template v-else
              ><section
                v-if="result.gemma_execution && result.unit !== 'USD/year'"
                class="panel quality-panel"
              >
                <h2>Gemma đọc tin tuyển dụng</h2>
                <template v-if="result.gemma_execution.used">
                  <p>
                    {{ result.gemma_execution.succeeded }} /
                    {{ result.gemma_execution.rows }} mô tả trích xuất thành
                    công; {{ result.gemma_execution.failed }} dòng lỗi.
                  </p>
                  <p class="muted">
                    Adapter:
                    {{
                      result.gemma_execution.provenance.adapter.split("/").pop()
                    }}
                    · chỉ suy luận.
                  </p>
                  <a :href="artifact('gemma_outputs.json')" download
                    >Tải JSON gốc và lỗi từng dòng ↓</a
                  >
                  <p class="muted">
                    Gemma trích thông tin; Random Forest / Ridge dự đoán lương.
                    Lương do Gemma đọc không được dùng làm nhãn đánh giá.
                  </p>
                </template>
                <p v-else class="muted">
                  {{
                    result.gemma_execution.requested
                      ? "Đã chọn Gemma nhưng không có mô tả khác rỗng để xử lý."
                      : "Lượt này dùng các cột có sẵn; chưa gọi Gemma."
                  }}
                </p>
              </section>
              <section class="quality-panel metrics-section">
                <h2>Độ khớp trên bảng đang nhập</h2>
                <p class="muted">
                  Số đo dưới đây có thể bao gồm dữ liệu model từng thấy. Không
                  thay thế đánh giá trên tập test độc lập.
                </p>
                <ModelComparison
                  v-if="Object.keys(result.metrics).length"
                  :metrics="result.metrics"
                  :selected="result.model.selected_model"
                  :unit="result.unit || 'VND/month'"
                  scope="Bảng vừa nhập · không phải test độc lập"
                />
                <div v-else class="info-note">
                  Không có nhãn đúng đơn vị để tính MAE/RMSE/R²; vẫn có dự đoán
                  trong bảng kết quả.
                </div>
                <ul class="quality-notes">
                  <li v-for="note in result.warnings" :key="note">
                    {{ note }}
                  </li>
                </ul>
                <details>
                  <summary>Thông tin model & khả năng tái hiện</summary>
                  <p>
                    Model {{ result.model.experiment_id }},
                    {{ result.model.train_jobs }} mẫu train. MAE test lịch sử:
                    {{
                      money(
                        result.model.historical_test.mae_usd_year ??
                          result.model.historical_test.mae_vnd,
                      )
                    }}
                    {{ unitLabel }} trên
                    {{ result.model.historical_test.samples }} mẫu.
                  </p>
                  <p
                    v-if="
                      result.model.train_label_counts?.assumed_month_train_only
                    "
                    class="muted"
                  >
                    Trong train có
                    {{
                      result.model.train_label_counts.assumed_month_train_only
                    }}
                    tin cần giả định kỳ lương tháng (trọng số 0,3);
                    validation/test chỉ dùng tin có bằng chứng lương tháng. Kết
                    quả không phải nhãn gold.
                  </p>
                  <p>
                    File manifest trong gói ZIP ghi checksum, ánh xạ cột và cấu
                    hình phân tích.
                  </p>
                </details>
              </section></template
            >
          </template>
        </template>
        <template v-else>
          <div class="advice-layout">
            <section class="panel profile-panel">
              <h2>Thông tin hồ sơ</h2>
              <label class="profile-market"
                >Dữ liệu / đơn vị<select v-model="profileMarket">
                  <option
                    value="international_survey"
                    :disabled="!internationalMeta"
                  >
                    Khảo sát quốc tế · USD/năm
                  </option>
                  <option value="vietnam_offers">
                    Tin Việt Nam · VND/tháng
                  </option>
                </select></label
              >
              <p class="muted">
                Dùng cùng các thông tin đầu vào của mô hình lương.
              </p>
              <form @submit.prevent="getAdvice">
                <label
                  >Vai trò<select v-model="profile.role">
                    <option v-for="role in profileRoles" :key="role">
                      {{ role }}
                    </option>
                  </select></label
                >
                <div class="form-two">
                  <label v-if="profileMarket === 'vietnam_offers'"
                    >Cấp bậc<select v-model="profile.level">
                      <option
                        v-for="level in [
                          ...new Set([
                            ...(meta?.salary_model.levels || []),
                            'Unknown',
                          ]),
                        ]"
                        :key="level"
                      >
                        {{ level }}
                      </option>
                    </select></label
                  ><label
                    >Kinh nghiệm (năm)<input
                      v-model="profile.experience_years"
                      type="number"
                      min="0"
                      max="80"
                      step="0.5"
                      placeholder="Chưa có thông tin"
                  /></label>
                </div>
                <label v-if="profileMarket === 'international_survey'"
                  >Quốc gia<select v-model="profile.country">
                    <option
                      v-for="country in internationalMeta?.countries"
                      :key="country"
                    >
                      {{ country }}
                    </option>
                  </select></label
                >
                <label v-else
                  >Khu vực<input
                    v-model="profile.location"
                    placeholder="Ví dụ: Hà Nội" /></label
                ><label
                  >Kỹ năng<input
                    v-model="profile.skills"
                    placeholder="Python, SQL, FastAPI"
                  /><small>Phân cách bằng dấu phẩy.</small></label
                ><button
                  type="submit"
                  class="primary"
                  :disabled="profileBusy || !meta"
                >
                  {{ profileBusy ? "Đang ước tính…" : "Dự đoán & xem gợi ý" }} →
                </button>
              </form>
            </section>
            <div v-if="advice" class="advice-result">
              <section class="salary-spotlight">
                <span>{{ advice.target_label }}</span>
                <div class="prediction-pair">
                  <div>
                    <span
                      >{{ modelLabel(advice.selected_model) }} · được chọn</span
                    ><strong
                      >{{ money(advice.predictions[advice.selected_model])
                      }}<small>{{ unitLabel }}</small></strong
                    >
                  </div>
                  <div>
                    <span
                      >{{
                        modelLabel(comparisonFamily(advice.selected_model))
                      }}
                      · đối chiếu</span
                    ><strong
                      >{{
                        money(
                          advice.predictions[
                            comparisonFamily(advice.selected_model)
                          ],
                        )
                      }}<small>{{ unitLabel }}</small></strong
                    >
                  </div>
                </div>
                <small
                  >MAE test đã lưu:
                  {{
                    money(
                      advice.evidence.historical_test_mae_usd_year ??
                        advice.evidence.historical_test_mae_vnd,
                    )
                  }}
                  {{ unitLabel }} trên
                  {{ advice.evidence.historical_test_samples }} mẫu. Đây không
                  phải khoảng chắc chắn cho hồ sơ này.</small
                >
              </section>
              <h2>Kỹ năng để cân nhắc tiếp theo</h2>
              <p class="muted">{{ advice.explanation }}</p>
              <section
                v-if="advice.recommendations.length"
                class="panel recommendation-table"
              >
                <div class="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Kỹ năng nên cân nhắc</th>
                        <th>Mẫu train cùng vai trò</th>
                        <th>Thay đổi dự đoán khi thêm kỹ năng</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="item in advice.recommendations"
                        :key="item.skill"
                      >
                        <td>
                          <strong>{{ item.skill }}</strong>
                        </td>
                        <td>{{ item.role_support ?? item.train_support }}</td>
                        <td class="number">
                          +{{
                            money(
                              item.predicted_delta_usd_year ??
                                item.predicted_delta_vnd,
                            )
                          }}
                          {{ unitLabel }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
              <div v-if="!advice.recommendations.length" class="info-note">
                Chưa đủ bằng chứng trong train để gợi ý thêm kỹ năng.
              </div>
              <div v-if="advice.warnings.length" class="info-note">
                <strong>Lưu ý về hồ sơ</strong>
                <ul>
                  <li v-for="warning in advice.warnings" :key="warning">
                    {{ warning }}
                  </li>
                </ul>
              </div>
            </div>
            <section v-else class="panel empty-state advice-empty">
              <div class="empty-icon">↗</div>
              <h2>Kết quả dự đoán và kỹ năng đề xuất</h2>
              <p>
                Nhập vai trò, kinh nghiệm, quốc gia hoặc khu vực và kỹ năng. Kết
                quả sẽ đặt hai mô hình cạnh nhau, kèm số mẫu hỗ trợ cho từng gợi
                ý.
              </p>
              <span class="pill neutral"
                >Gợi ý dựa trên dữ liệu · Không cam kết tăng lương</span
              >
            </section>
          </div>
        </template>
        <footer class="footer">
          <span
            >Đề tài 04 <b>·</b> Phân tích thị trường việc làm CNTT & dự đoán
            lương</span
          ><span
            >Gemma đọc tin <b>·</b> Ridge / RF dự đoán <b>·</b> Python vẽ biểu
            đồ</span
          >
        </footer>
      </div>
    </main>
  </div>
</template>
