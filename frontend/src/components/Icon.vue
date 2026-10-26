<script setup>
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  ChartNoAxesCombined,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Clock3,
  Database,
  FileSpreadsheet,
  FileUp,
  Globe2,
  Layers3,
  LayoutDashboard,
  LoaderCircle,
  MapPin,
  Menu,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  UploadCloud,
  Users,
  X,
  XCircle,
} from "lucide-vue-next";
const props = defineProps({
  name: String,
  size: { type: Number, default: 20 },
});
const icons = {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  ChartNoAxesCombined,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Clock3,
  Database,
  FileSpreadsheet,
  FileUp,
  Globe2,
  Layers3,
  LayoutDashboard,
  LoaderCircle,
  MapPin,
  Menu,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  UploadCloud,
  Users,
  X,
  XCircle,
};
</script>
<template>
  <component
    :is="icons[props.name] || Activity"
    :size="size"
    :stroke-width="1.7"
    aria-hidden="true"
  />
</template>
