import client from "./client";

export const listAuditLogs = (params) => client.get("/audit-logs", { params });
