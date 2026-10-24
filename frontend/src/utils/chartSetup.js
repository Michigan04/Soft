import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Legend,
  Tooltip,
} from "chart.js";

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, LineElement, PointElement, Legend, Tooltip);

export const RISK_COLORS = {
  low: "#2f9e44",
  moderate: "#e8a400",
  high: "#e8590c",
  critical: "#c92a2a",
  unassessed: "#9499ab",
};
