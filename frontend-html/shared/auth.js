/*
 * Plain-JS port of frontend/src/stores/auth.js + the router guard in
 * frontend/src/router/index.js. There is no SPA router here -- every page is
 * its own full reload, so "navigation guard" becomes "run this at the top of
 * each page's mounted() hook, before showing any real content."
 */
(function () {
  function getToken() {
    return localStorage.getItem("access_token");
  }

  function setToken(token) {
    localStorage.setItem("access_token", token);
  }

  function clearToken() {
    localStorage.removeItem("access_token");
  }

  function isAuthenticated() {
    return !!getToken();
  }

  async function login(email, password) {
    const response = await Api.auth.login(email, password);
    setToken(response.data.access_token);
  }

  function logout() {
    clearToken();
  }

  async function fetchMe() {
    const response = await Api.auth.fetchMe();
    return response.data;
  }

  const roleHelpers = {
    isAdmin: (user) => user?.role === "admin",
    isStaff: (user) => user?.role === "faculty" || user?.role === "ta",
    isStudent: (user) => user?.role === "student",
  };

  function currentPage() {
    return location.pathname.split("/").pop() || "DashboardOverview.html";
  }

  /**
   * Call at the start of mounted() on every protected page.
   * Redirects to Login.html (no user) or Unauthorized.html (wrong role) and
   * returns null when the page should not render; otherwise returns the user.
   */
  async function requireUser(allowedRoles) {
    if (!isAuthenticated()) {
      const redirect = encodeURIComponent(currentPage() + location.search);
      location.href = `Login.html?redirect=${redirect}`;
      return null;
    }
    let user;
    try {
      user = await fetchMe();
    } catch (e) {
      clearToken();
      location.href = "Login.html";
      return null;
    }
    if (allowedRoles && !allowedRoles.includes(user.role)) {
      location.href = "Unauthorized.html";
      return null;
    }
    return user;
  }

  window.Auth = {
    getToken,
    setToken,
    clearToken,
    isAuthenticated,
    login,
    logout,
    fetchMe,
    requireUser,
    ...roleHelpers,
  };
})();
