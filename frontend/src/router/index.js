import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const routes = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/Login.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    component: () => import("@/layouts/AppLayout.vue"),
    children: [
      { path: "", redirect: "/dashboard" },
      {
        path: "dashboard",
        name: "dashboard",
        component: () => import("@/views/DashboardOverview.vue"),
      },
      {
        path: "students",
        name: "students",
        component: () => import("@/views/StudentDirectory.vue"),
        meta: { roles: ["admin", "faculty", "ta"] },
      },
      {
        path: "students/:id",
        name: "student-profile",
        component: () => import("@/views/StudentProfile.vue"),
        props: true,
      },
      {
        path: "registration-checker",
        name: "registration-checker",
        component: () => import("@/views/RegistrationChecker.vue"),
      },
      {
        path: "projects",
        name: "projects",
        component: () => import("@/views/ProjectCgpaTracker.vue"),
      },
      {
        path: "notifications",
        name: "notifications",
        component: () => import("@/views/Notifications.vue"),
      },
      {
        path: "interventions",
        name: "interventions",
        component: () => import("@/views/Interventions.vue"),
        meta: { roles: ["admin", "faculty", "ta"] },
      },
      {
        path: "assignments",
        name: "assignments",
        component: () => import("@/views/StaffAssignments.vue"),
        meta: { roles: ["admin"] },
      },
      {
        path: "rules",
        name: "rules",
        component: () => import("@/views/RulesManagement.vue"),
        meta: { roles: ["admin"] },
      },
      {
        path: "imports",
        name: "imports",
        component: () => import("@/views/DataImport.vue"),
        meta: { roles: ["admin"] },
      },
      {
        path: "reports",
        name: "reports",
        component: () => import("@/views/Reports.vue"),
        meta: { roles: ["admin", "faculty", "ta"] },
      },
      {
        path: "audit-logs",
        name: "audit-logs",
        component: () => import("@/views/AuditLogs.vue"),
        meta: { roles: ["admin"] },
      },
      {
        path: "unauthorized",
        name: "unauthorized",
        component: () => import("@/views/Unauthorized.vue"),
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("@/views/NotFound.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();

  if (to.meta.public) {
    return true;
  }

  if (!auth.isAuthenticated) {
    return { name: "login", query: { redirect: to.fullPath } };
  }

  if (!auth.user) {
    try {
      await auth.loadMe();
    } catch (e) {
      auth.logout();
      return { name: "login" };
    }
  }

  if (to.meta.roles && !to.meta.roles.includes(auth.role)) {
    return { name: "unauthorized" };
  }

  return true;
});

export default router;
