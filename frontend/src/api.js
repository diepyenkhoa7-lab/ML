export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    cache: "no-store",
    ...options,
  });
  const value = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(value.detail)
      ? value.detail.map((x) => x.msg).join("; ")
      : value.detail;
    throw new Error(detail || `Không thể xử lý yêu cầu (${response.status}).`);
  }
  return value;
}

export function post(path, value) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(value),
  });
}

export const label = (market) =>
  market === "vietnam" ? "Việt Nam" : "Quốc tế";
export const unit = (market) =>
  market === "vietnam" ? "VND / tháng" : "USD / năm";
export const number = (value, digits = 0) =>
  value == null
    ? "—"
    : new Intl.NumberFormat("vi-VN", { maximumFractionDigits: digits }).format(
        value,
      );
export const money = (value, market) =>
  value == null
    ? "—"
    : market === "vietnam"
      ? `${number(value)} ₫`
      : `$${new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value)}`;
export const titles = {
  skills: "Công nghệ phổ biến",
  experience: "Kinh nghiệm & thu nhập",
  role: "Thu nhập theo vai trò",
  location: "Thu nhập theo khu vực",
  skill_income: "Thu nhập theo kỹ năng",
};
