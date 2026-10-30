<script setup>
import { ref, watch } from "vue";
import { api, post } from "../api";
import Icon from "../components/Icon.vue";
import ResultPanel from "../components/ResultPanel.vue";
const props = defineProps({ market: String, job: Object, result: Object });
const emit = defineEmits(["job"]);
const input = ref(null),
  upload = ref(null),
  error = ref(""),
  uploading = ref(false),
  submitting = ref(false),
  dragging = ref(false);
const mapping = ref({}),
  defaultMarket = ref(props.market),
  defaultLocation = ref(""),
  referenceUnit = ref(""),
  includeAdvice = ref(false);
const fields = {
  role: "Vai trò",
  location: "Khu vực / quốc gia",
  experience_years: "Số năm kinh nghiệm",
  skills: "Kỹ năng",
  description: "Mô tả tin tuyển dụng",
  market: "Thị trường",
  salary: "Thu nhập thực tế (tùy chọn)",
  unit: "Đơn vị thu nhập (tùy chọn)",
};
watch(
  () => props.market,
  (m) => {
    defaultMarket.value = m;
    referenceUnit.value = "";
  },
);
async function handleFile(file) {
  if (!file) return;
  error.value = "";
  upload.value = null;
  if (file.size > 10 * 1024 * 1024) {
    error.value = "File vượt giới hạn 10 MB.";
    return;
  }
  if (!/\.(csv|json|xlsx)$/i.test(file.name)) {
    error.value = "Hãy chọn file CSV, JSON hoặc XLSX.";
    return;
  }
  uploading.value = true;
  const body = new FormData();
  body.append("file", file);
  try {
    upload.value = await api("/uploads", { method: "POST", body });
    mapping.value = { ...upload.value.mapping };
    includeAdvice.value = false;
  } catch (e) {
    error.value = e.message;
  } finally {
    uploading.value = false;
    if (input.value) input.value.value = "";
  }
}
async function analyze() {
  submitting.value = true;
  error.value = "";
  try {
    const job = await post("/analyses", {
      upload_id: upload.value.id,
      mapping: mapping.value,
      market: defaultMarket.value,
      location: defaultLocation.value,
      reference_unit: referenceUnit.value,
      include_advice: includeAdvice.value,
    });
    emit("job", job);
  } catch (e) {
    error.value = e.message;
  } finally {
    submitting.value = false;
  }
}
</script>
<template>
  <div class="view">
    <div class="page-intro compact">
      <div>
        <span class="eyebrow">YOUR DATA, YOUR INSIGHTS</span>
        <h1>Mang dữ liệu của bạn đến<span class="accent-dot">.</span></h1>
        <p>
          Qwen đã fine-tune sẽ đọc hồ sơ, ước tính lương và tổng hợp biểu đồ.
        </p>
      </div>
      <span class="model-badge"
        ><Icon name="Sparkles" :size="16" /> Qwen3 đã fine-tune</span
      >
    </div>
    <div class="upload-layout">
      <section class="panel upload-card">
        <div class="panel-head">
          <div>
            <span class="step-badge">01</span>
            <h3>Chọn dữ liệu</h3>
          </div>
          <span class="muted">CSV · JSON · XLSX</span>
        </div>
        <input
          ref="input"
          id="data-file"
          aria-label="Chọn file dữ liệu CSV, JSON hoặc XLSX"
          type="file"
          accept=".csv,.xlsx,.json"
          class="sr-only"
          @change="handleFile($event.target.files[0])"
        /><button
          class="dropzone"
          :class="{ dragging }"
          :disabled="uploading"
          @click="input.click()"
          @dragover.prevent="dragging = true"
          @dragleave.prevent="dragging = false"
          @drop.prevent="
            dragging = false;
            handleFile($event.dataTransfer.files[0]);
          "
        >
          <span class="upload-icon"
            ><Icon
              :name="uploading ? 'LoaderCircle' : 'UploadCloud'"
              :class="{ spin: uploading }"
              :size="32" /></span
          ><strong>{{
            uploading ? "Đang đọc file…" : "Kéo thả file vào đây"
          }}</strong
          ><span>hoặc <u>chọn từ máy tính</u></span
          ><small>Tối đa 500 dòng · 10 MB / file</small>
        </button>
        <div class="example-row">
          <span>Chưa có file? Tải mẫu:</span
          ><a
            v-for="f in ['csv', 'xlsx', 'json']"
            :key="f"
            :href="`/api/examples/${f}`"
            >{{ f.toUpperCase() }} <Icon name="ArrowDownToLine" :size="13"
          /></a>
        </div>
      </section>
      <aside class="panel upload-guide">
        <span class="icon-tile lime"
          ><Icon name="FileSpreadsheet" :size="24"
        /></span>
        <h3>Một file, nhiều góc nhìn.</h3>
        <div>
          <span>1</span>
          <p>
            <strong>Xác nhận các cột</strong>Ghép tên cột trong file với thông
            tin hồ sơ.
          </p>
        </div>
        <div>
          <span>2</span>
          <p>
            <strong>Để AI phân tích</strong>Trích xuất phần thiếu từ mô tả và dự
            đoán lương.
          </p>
        </div>
        <div>
          <span>3</span>
          <p>
            <strong>Đọc & tải kết quả</strong>Xem biểu đồ, lỗi từng dòng, xuất
            bảng để sử dụng.
          </p>
        </div>
      </aside>
    </div>
    <p v-if="error" class="alert error" role="alert">{{ error }}</p>
    <section v-if="upload" class="panel mapping-panel">
      <div class="panel-head">
        <div>
          <span class="step-badge">02</span>
          <h3>Xác nhận dữ liệu</h3>
        </div>
        <span class="soft-badge"
          >{{ upload.filename }} · {{ upload.rows }} dòng</span
        >
      </div>
      <details class="preview-details">
        <summary>Xem trước {{ upload.preview.length }} dòng đầu</summary>
        <div
          class="table-scroll"
          tabindex="0"
          role="region"
          aria-label="Bảng dữ liệu có thể cuộn ngang"
        >
          <table>
            <thead>
              <tr>
                <th v-for="column in upload.columns" :key="column">
                  {{ column }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in upload.preview" :key="i">
                <td
                  v-for="column in upload.columns"
                  :key="column"
                  class="preview-cell"
                  :title="String(row[column] ?? '')"
                >
                  {{ row[column] ?? "—" }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>
      <form @submit.prevent="analyze">
        <div class="mapping-grid">
          <label v-for="(title, field) in fields" :key="field"
            ><span>{{ title }}</span
            ><select v-model="mapping[field]">
              <option value="">
                {{
                  field === "description"
                    ? "Không dùng trích xuất văn bản"
                    : "Chưa ghép cột"
                }}
              </option>
              <option v-for="column in upload.columns" :key="column">
                {{ column }}
              </option>
            </select></label
          >
        </div>
        <div class="form-note">
          <Icon name="CircleHelp" :size="16" />
          <p>
            Nếu có cột mô tả, AI có thể trích vai trò, kinh nghiệm và kỹ năng
            còn thiếu. Thu nhập nguồn chỉ dùng đối chiếu, không đưa vào dự đoán.
          </p>
        </div>
        <div class="mapping-defaults">
          <label
            ><span>Thị trường mặc định</span
            ><select v-model="defaultMarket">
              <option value="vietnam">Việt Nam · VND/tháng</option>
              <option value="international">Quốc tế · USD/năm</option></select
            ><small>Dùng khi file không có thị trường.</small></label
          ><label
            ><span>Khu vực mặc định</span
            ><input
              v-model="defaultLocation"
              :placeholder="
                defaultMarket === 'vietnam' ? 'Ví dụ: Hà Nội' : 'Ví dụ: Germany'
              "
            /><small>Dùng khi dòng thiếu khu vực/quốc gia.</small></label
          ><label
            ><span>Xác nhận đơn vị lương nguồn</span
            ><select v-model="referenceUnit">
              <option value="">Không đối chiếu thu nhập</option>
              <option value="VND/month">Lương chào tuyển · VND/tháng</option>
              <option value="USD/year">Tổng thu nhập · USD/năm</option></select
            ><small>Chỉ chọn khi bạn biết rõ đơn vị.</small></label
          >
        </div>
        <div class="submit-row">
          <label class="checkbox"
            ><input
              v-model="includeAdvice"
              type="checkbox"
              :disabled="upload.rows > 20"
            /><span
              >Thêm tư vấn kỹ năng <small>(tối đa 20 hồ sơ)</small></span
            ></label
          ><button class="button primary" :disabled="submitting">
            <Icon
              :name="submitting ? 'LoaderCircle' : 'Sparkles'"
              :class="{ spin: submitting }"
              :size="18"
            />{{ submitting ? "Đang gửi…" : "Phân tích bằng Qwen"
            }}<Icon name="ArrowRight" :size="17" />
          </button>
        </div>
      </form>
    </section>
    <ResultPanel :key="job?.id" :job="job" :result="result" />
  </div>
</template>
