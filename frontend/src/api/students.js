import client from "./client";

export const listStudents = (params) => client.get("/students", { params });
export const createStudent = (data) => client.post("/students", data);
export const getStudent = (id) => client.get(`/students/${id}`);
export const updateStudent = (id, data) => client.patch(`/students/${id}`, data);
export const getAcademicHistory = (id) => client.get(`/students/${id}/academic-history`);
export const getRiskAssessments = (id) => client.get(`/students/${id}/risk-assessments`);
export const triggerRiskAssessment = (id) => client.post(`/students/${id}/assess-risk`);
export const getStudentInterventions = (id) => client.get(`/students/${id}/interventions`);
export const getStudentMilestones = (id) => client.get(`/students/${id}/milestones`);
export const getStudentProjects = (id) => client.get(`/students/${id}/projects`);
export const getCgpaSummary = (id) => client.get(`/students/${id}/cgpa-summary`);
export const getStudentNotifications = (id) => client.get(`/students/${id}/notifications`);
