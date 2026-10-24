import client from "./client";

export const getSummary = (params) => client.get("/dashboard/summary", { params });
export const getRiskDistribution = (params) => client.get("/dashboard/risk-distribution", { params });
export const getProgressionTrends = (params) => client.get("/dashboard/progression-trends", { params });
