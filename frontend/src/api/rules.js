import client from "./client";

export const listRules = () => client.get("/rules");
export const createRule = (data) => client.post("/rules", data);
export const updateRule = (id, data) => client.patch(`/rules/${id}`, data);
export const listPolicies = () => client.get("/rules/policies");
export const updatePolicy = (key, value) => client.put(`/rules/policies/${key}`, value);
