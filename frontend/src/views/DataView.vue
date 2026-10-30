<script setup>
import { computed, ref, watch, onBeforeUnmount } from "vue";
import { api, label, number, unit } from "../api";
import Icon from "../components/Icon.vue";
import ProfileTable from "../components/ProfileTable.vue";
const props = defineProps({ market: String });
const query = ref(""),
  role = ref(""),
  location = ref(""),
  page = ref(1);
const data = ref(null),
  choices = ref(null),
  error = ref(""),
  loading = ref(false);
let timer,
  generation = 0;
const parameters = computed(() =>
  new URLSearchParams({
    market: props.market,
    q: query.value,
    role: role.value,
    location: location.value,
    page: page.value,
    size: 15,
  }).toString(),
);
async function load() {
  const id = ++generation;
  loading.value = true;
  error.value = "";
  try {
    const value = await api(`/records?${parameters.value}`);
    if (id === generation) data.value = value;
  } catch (e) {
    error.value = e.message;
  } finally {
    if (id === generation) loading.value = false;
  }
}
watch(
  () => props.market,
  async (market) => {
    role.value = "";
    location.value = "";
    page.value = 1;
    choices.value = await api(`/overview?market=${market}`).catch(() => null);
    load();
  },
  { immediate: true },
);
watch([query, role, location], () => {
  page.value = 1;
  clearTimeout(timer);
  timer = setTimeout(load, 250);
});
watch(page, load);
onBeforeUnmount(() => clearTimeout(timer));
</script>
<template>
  <div class="view">
    <div class="page-intro compact">
      <div>
        <span class="eyebrow">DATA EXPLORER</span>
        <h1>Đi từ dữ liệu gốc<span class="accent-dot">.</span></h1>
        <p>
          Tra cứu hồ sơ đã làm sạch trong tập train · {{ label(market) }} ·
          {{ unit(market) }}.
        </p>
      </div>
      <a class="button secondary" :href="`/api/data/download?${parameters}`"
        ><Icon name="ArrowDownToLine" :size="17" /> Xuất dữ liệu đã lọc</a
      >
    </div>
    <section class="panel">
      <div class="table-filters">
        <label class="search-field"
          ><Icon name="Search" :size="18" /><input
            v-model="query"
            aria-label="Tìm vai trò, khu vực hoặc kỹ năng"
            placeholder="Tìm vai trò, khu vực, kỹ năng…" /></label
        ><label
          ><span class="sr-only">Lọc vai trò</span
          ><select v-model="role">
            <option value="">Tất cả vai trò</option>
            <option v-for="r in choices?.roles || []" :key="r">{{ r }}</option>
          </select></label
        ><label
          ><span class="sr-only">Lọc khu vực</span
          ><select v-model="location">
            <option value="">Tất cả khu vực</option>
            <option v-for="r in choices?.countries || []" :key="r">
              {{ r }}
            </option>
          </select></label
        ><button
          v-if="query || role || location"
          class="text-button"
          @click="
            query = '';
            role = '';
            location = '';
          "
        >
          Xóa lọc
        </button>
      </div>
      <div class="table-summary">
        <span
          >{{ number(data?.total || 0) }} hồ sơ{{
            query || role || location ? " phù hợp" : ""
          }}</span
        ><span v-if="loading" class="muted"
          ><Icon name="LoaderCircle" :size="14" class="spin" /> Đang đọc…</span
        ><span v-else class="muted"
          >Nguồn có trong từng hồ sơ · không trộn đơn vị</span
        >
      </div>
      <p v-if="error" class="alert error" role="alert">{{ error }}</p>
      <ProfileTable :rows="data?.rows || []" />
      <div class="pagination">
        <span>{{
          data?.total
            ? `${(page - 1) * 15 + 1}–${Math.min(page * 15, data.total)} trên ${number(data.total)}`
            : "Không có kết quả"
        }}</span>
        <div>
          <button
            :disabled="page === 1 || loading"
            @click="page--"
            aria-label="Trang trước"
          >
            <Icon name="ChevronLeft" :size="17" /></button
          ><span
            >Trang {{ page }} /
            {{ Math.max(1, Math.ceil((data?.total || 0) / 15)) }}</span
          ><button
            :disabled="page * 15 >= (data?.total || 0) || loading"
            @click="page++"
            aria-label="Trang sau"
          >
            <Icon name="ChevronRight" :size="17" />
          </button>
        </div>
      </div>
    </section>
    <div class="context-note">
      <Icon name="Database" :size="18" />
      <p>
        Dữ liệu này được giữ nguyên để tái lập. File tải lên và kết quả phân
        tích được lưu riêng, không ghi đè dataset hay tự huấn luyện model.
      </p>
    </div>
  </div>
</template>
