import client from "./client";

export const listProjects = (params) => client.get("/projects", { params });
export const createProject = (data) => client.post("/projects", data);
export const updateProject = (id, data) => client.patch(`/projects/${id}`, data);
export const listMilestones = () => client.get("/milestones");
