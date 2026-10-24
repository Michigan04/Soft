import client from "./client";

export const listTerms = () => client.get("/academic-terms");
export const listCourses = (params) => client.get("/courses", { params });
