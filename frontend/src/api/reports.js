import client from "./client";

export const getRiskTrends = (params) => client.get("/reports/risk-trends", { params });
export const getInterventionOutcomes = (params) => client.get("/reports/intervention-outcomes", { params });
export const getProgression = (params) => client.get("/reports/progression", { params });
export const getOverdueFollowups = (params) => client.get("/reports/overdue-followups", { params });

const cleanParams = (params = {}) =>
  Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""));

export async function downloadReportCsv(path, params = {}) {
  const response = await client.get(`/reports/${path}`, {
    params: { ...cleanParams(params), export: true },
    responseType: "blob",
  });
  const url = URL.createObjectURL(response.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${path}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
