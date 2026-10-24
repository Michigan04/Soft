import client from "./client";

export const listInterventions = (params) => client.get("/interventions", { params });
export const createIntervention = (data) => client.post("/interventions", data);
export const updateIntervention = (id, data) => client.patch(`/interventions/${id}`, data);
