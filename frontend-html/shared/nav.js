/*
 * Plain-JS port of the nav item list in frontend/src/components/layout/Sidebar.vue.
 * Route names become page filenames since there is no SPA router here.
 */
(function () {
  const ALL_ITEMS = [
    { key: "dashboard", label: "Dashboard", page: "DashboardOverview.html", roles: ["admin", "faculty", "ta", "student"] },
    { key: "students", label: "Students", page: "StudentDirectory.html", roles: ["admin", "faculty", "ta"] },
    { key: "student-profile", label: "My Profile", page: "StudentProfile.html", roles: ["student"], needsOwnId: true },
    { key: "registration-checker", label: "Registration Checker", page: "RegistrationChecker.html", roles: ["admin", "faculty", "ta", "student"] },
    { key: "projects", label: "Projects & CGPA", page: "ProjectCgpaTracker.html", roles: ["admin", "faculty", "ta", "student"] },
    { key: "interventions", label: "Interventions", page: "Interventions.html", roles: ["admin", "faculty", "ta"] },
    { key: "assignments", label: "Staff Assignments", page: "StaffAssignments.html", roles: ["admin"] },
    { key: "notifications", label: "Notifications", page: "Notifications.html", roles: ["admin", "faculty", "ta", "student"] },
    { key: "reports", label: "Reports", page: "Reports.html", roles: ["admin", "faculty", "ta"] },
    { key: "rules", label: "Rules & Policies", page: "RulesManagement.html", roles: ["admin"] },
    { key: "imports", label: "Data Import", page: "DataImport.html", roles: ["admin"] },
    { key: "audit-logs", label: "Audit Logs", page: "AuditLogs.html", roles: ["admin"] },
  ];

  function visibleNavItems(user) {
    return ALL_ITEMS.filter((item) => item.roles.includes(user?.role))
      .filter((item) => !item.needsOwnId || user?.student_id)
      .map((item) => ({
        ...item,
        href: item.needsOwnId ? `${item.page}?id=${user.student_id}` : item.page,
      }));
  }

  window.Nav = { ALL_ITEMS, visibleNavItems };
})();
