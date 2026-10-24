import client from "./client";

export const validateRegistration = (data) => client.post("/registrations/validate", data);
export const submitRegistration = (data) => client.post("/registrations", data);
export const listRegistrations = (params) => client.get("/registrations", { params });
