<script setup>
import { ref, watch } from "vue";
import { api, post } from "../api";
import Icon from "../components/Icon.vue";
import ResultPanel from "../components/ResultPanel.vue";
const props = defineProps({ market: String, job: Object, result: Object });
const emit = defineEmits(["job"]);
const mode = ref("profile"),
  role = ref("Backend Developer"),
  location = ref("Hà Nội"),
  years = ref(3),
  skills = ref("Python; SQL; Docker"),
  description = ref(""),
  advice = ref(true);
const roles = ref([]),
  countries = ref([]),
  busy = ref(false),
  error = ref("");
watch(
  () => props.market,
  async (market) => {
    try {
      const data = await api(`/overview?market=${market}`);
      roles.value = data.roles;
      countries.value = data.countries;
      location.value = market === "vietnam" ? "Hà Nội" : "Germany";
      role.value =
        market === "vietnam" ? "Backend Developer" : "Developer, back-end";
    } catch (e) {
      error.value = e.message;
    }
  },
  { immediate: true },
);
async function submit() {
  error.value = "";
  busy.value = true;
  try {
    const job = await post("/profiles", {
      market: props.market,
      location: location.value,
      role: mode.value === "text" ? null : role.value,
      experience_years:
        mode.value === "text" || years.value === ""
          ? null
          : Number(years.value),
      skills: mode.value === "text" ? null : skills.value,
      description: mode.value === "text" ? description.value : "",
      include_advice: advice.value,
    });
    emit("job", job);
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
</script>
<template>
  <div class="view">
    <div class="page-intro compact">
      <div>
        <span class="eyebrow">YOUR NEXT CHAPTER</span>
        <h1>Bước tiếp theo trong sự nghiệp<span class="accent-dot">.</span></h1>
        <p>
          Một góc nhìn từ dữ liệu cho vai trò, mức lương và kỹ năng của bạn.
        </p>
      </div>
      <span class="model-badge"
        ><Icon name="Sparkles" :size="16" /> Qwen đã fine-tune</span
      >
    </div>
    <div class="career-grid">
      <section class="panel career-form">
        <div class="panel-head">
          <h3>Hồ sơ của bạn</h3>
          <Icon name="Users" :size="20" />
        </div>
        <div class="segment">
          <button
            :class="{ selected: mode === 'profile' }"
            @click="mode = 'profile'"
          >
            Nhập thông tin</button
          ><button
            :class="{ selected: mode === 'text' }"
            @click="mode = 'text'"
          >
            Dán tin tuyển dụng
          </button>
        </div>
        <form @submit.prevent="submit">
          <div class="form-grid">
            <label class="full"
              ><span>{{
                market === "vietnam"
                  ? "Khu vực"
                  : "Quốc gia (tên trong khảo sát)"
              }}</span
              ><input
                v-model="location"
                list="career-countries"
                required
                maxlength="200" /><datalist id="career-countries">
                <option
                  v-for="country in countries"
                  :key="country"
                  :value="country"
                /></datalist></label
            ><template v-if="mode === 'profile'"
              ><label
                ><span>Vai trò công việc</span
                ><input
                  v-model="role"
                  list="career-roles"
                  required
                  maxlength="200" /><datalist id="career-roles">
                  <option
                    v-for="r in roles"
                    :key="r"
                    :value="r"
                  /></datalist></label
              ><label
                ><span>Kinh nghiệm (năm)</span
                ><input
                  v-model="years"
                  type="number"
                  min="0"
                  max="80"
                  step="0.5"
                  required /></label
              ><label class="full"
                ><span>Kỹ năng hiện có</span
                ><textarea
                  v-model="skills"
                  rows="3"
                  maxlength="6000"
                  placeholder="Python; SQL; Docker"
                  required
                ></textarea
                ><small
                  >Phân tách bằng dấu chấm phẩy hoặc dấu phẩy.</small
                ></label
              ></template
            ><label v-else class="full"
              ><span>Mô tả tuyển dụng</span
              ><textarea
                v-model="description"
                rows="7"
                maxlength="12000"
                minlength="15"
                required
                placeholder="Ví dụ: Tuyển Backend Developer tại Hà Nội, 3 năm kinh nghiệm Python, SQL và Docker…"
              ></textarea
              ><small
                >AI sẽ trích xuất vai trò, kinh nghiệm, kỹ năng. Giữ mô tả ngắn
                để phù hợp ngữ cảnh model.</small
              ></label
            >
          </div>
          <label class="checkbox"
            ><input v-model="advice" type="checkbox" /><span
              >Gợi ý kỹ năng nên học thêm từ bằng chứng dữ liệu</span
            ></label
          >
          <p v-if="error" class="alert error" role="alert">{{ error }}</p>
          <button class="button primary full-width" :disabled="busy">
            <Icon
              :name="busy ? 'LoaderCircle' : 'Sparkles'"
              :class="{ spin: busy }"
              :size="18"
            />{{ busy ? "Đang gửi…" : "Dự đoán & tư vấn nghề nghiệp"
            }}<Icon name="ArrowRight" :size="17" />
          </button>
        </form>
      </section>
      <aside class="career-aside">
        <section class="career-quote">
          <span class="eyebrow">DỮ LIỆU LÀ ĐIỂM BẮT ĐẦU</span>
          <h2>
            Một quyết định tốt<br />bắt đầu từ<br /><span
              >hiểu chính mình.</span
            >
          </h2>
          <div class="quote-line"></div>
          <p>
            Model kết hợp vai trò, khu vực, kinh nghiệm và kỹ năng để ước tính
            thu nhập. Kết quả là một tham khảo, không phải lời hứa tuyển dụng.
          </p>
        </section>
        <section class="panel note-panel">
          <span class="icon-tile mint"><Icon name="ShieldCheck" /></span>
          <h3>Gợi ý có căn cứ</h3>
          <p>
            Mỗi kỹ năng cần ít nhất 10 mẫu hỗ trợ cùng vai trò. Khi thiếu dữ
            liệu, ứng dụng sẽ nói rõ thay vì tự tạo gợi ý.
          </p>
        </section>
      </aside>
    </div>
    <ResultPanel :key="job?.id" :job="job" :result="result" />
  </div>
</template>
