/*
 * Plain-JS port of frontend/src/api/*.js + frontend/src/api/client.js.
 * Loaded as a classic <script> (no bundler), so everything hangs off `window.Api`.
 * Points straight at the FastAPI backend (not through the Vite dev proxy), since
 * these pages are served from their own static server. See ../README.md for the
 * backend CORS origin that needs to be allowed.
 */
(function () {
  // Locally the backend runs separately on :8000; when deployed (e.g. Vercel) it shares this origin.
  const isLocal = ["localhost", "127.0.0.1"].includes(location.hostname) || location.protocol === "file:";
  const BACKEND_ORIGIN = window.BACKEND_ORIGIN || (isLocal ? "http://localhost:8000" : location.origin);

  const client = axios.create({
    baseURL: `${BACKEND_ORIGIN}/api/v1`,
  });

  client.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem("access_token");
        if (!location.pathname.endsWith("/Login.html")) {
          const redirect = encodeURIComponent(location.pathname.split("/").pop() + location.search);
          location.href = `Login.html?redirect=${redirect}`;
        }
      }
      return Promise.reject(error);
    },
  );

  function apiErrorMessage(error, fallback = "Something went wrong. Please try again.") {
    const detail = error?.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
    }
    return fallback;
  }

  const cleanParams = (params = {}) =>
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""));

  async function downloadReportCsv(path, params = {}) {
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

  window.Api = {
    client,
    apiErrorMessage,

    auth: {
      login(email, password) {
        const form = new URLSearchParams();
        form.append("username", email);
        form.append("password", password);
        return client.post("/auth/login", form, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        });
      },
      fetchMe() {
        return client.get("/auth/me");
      },
    },

    dashboard: {
      getSummary: (params) => client.get("/dashboard/summary", { params }),
      getRiskDistribution: (params) => client.get("/dashboard/risk-distribution", { params }),
      getProgressionTrends: (params) => client.get("/dashboard/progression-trends", { params }),
    },

    students: {
      listStudents: (params) => client.get("/students", { params }),
      createStudent: (data) => client.post("/students", data),
      getStudent: (id) => client.get(`/students/${id}`),
      updateStudent: (id, data) => client.patch(`/students/${id}`, data),
      getAcademicHistory: (id) => client.get(`/students/${id}/academic-history`),
      getRiskAssessments: (id) => client.get(`/students/${id}/risk-assessments`),
      triggerRiskAssessment: (id) => client.post(`/students/${id}/assess-risk`),
      getStudentInterventions: (id) => client.get(`/students/${id}/interventions`),
      getStudentMilestones: (id) => client.get(`/students/${id}/milestones`),
      getStudentProjects: (id) => client.get(`/students/${id}/projects`),
      getCgpaSummary: (id) => client.get(`/students/${id}/cgpa-summary`),
      getStudentNotifications: (id) => client.get(`/students/${id}/notifications`),
    },

    interventions: {
      listInterventions: (params) => client.get("/interventions", { params }),
      createIntervention: (data) => client.post("/interventions", data),
      updateIntervention: (id, data) => client.patch(`/interventions/${id}`, data),
    },

    projects: {
      listProjects: (params) => client.get("/projects", { params }),
      createProject: (data) => client.post("/projects", data),
      updateProject: (id, data) => client.patch(`/projects/${id}`, data),
      listMilestones: () => client.get("/milestones"),
    },

    registrations: {
      validateRegistration: (data) => client.post("/registrations/validate", data),
      submitRegistration: (data) => client.post("/registrations", data),
      listRegistrations: (params) => client.get("/registrations", { params }),
    },

    rules: {
      listRules: () => client.get("/rules"),
      createRule: (data) => client.post("/rules", data),
      updateRule: (id, data) => client.patch(`/rules/${id}`, data),
      listPolicies: () => client.get("/rules/policies"),
      updatePolicy: (key, value) => client.put(`/rules/policies/${key}`, value),
    },

    imports: {
      validateImport(importType, file) {
        const form = new FormData();
        form.append("import_type", importType);
        form.append("file", file);
        return client.post("/imports/validate", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      },
      commitImport: (validationToken) => client.post("/imports/commit", { validation_token: validationToken }),
      listImports: () => client.get("/imports"),
    },

    reports: {
      getRiskTrends: (params) => client.get("/reports/risk-trends", { params }),
      getInterventionOutcomes: (params) => client.get("/reports/intervention-outcomes", { params }),
      getProgression: (params) => client.get("/reports/progression", { params }),
      getOverdueFollowups: (params) => client.get("/reports/overdue-followups", { params }),
      downloadReportCsv,
    },

    audit: {
      listAuditLogs: (params) => client.get("/audit-logs", { params }),
    },

    assignments: {
      assignStudent: (studentId, staffUserId) =>
        client.post(`/students/${studentId}/assignments`, { staff_user_id: staffUserId }),
      getStaffWorkload: () => client.get("/staff/workload"),
    },

    notifications: {
      listNotifications: (params) => client.get("/notifications", { params }),
      markNotificationRead: (id) => client.patch(`/notifications/${id}/read`),
    },

    academic: {
      listTerms: () => client.get("/academic-terms"),
      listCourses: (params) => client.get("/courses", { params }),
    },
  };
})();
