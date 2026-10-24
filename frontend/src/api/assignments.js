import client from "./client";

export const assignStudent = (studentId, staffUserId) =>
  client.post(`/students/${studentId}/assignments`, { staff_user_id: staffUserId });
export const getStaffWorkload = () => client.get("/staff/workload");
