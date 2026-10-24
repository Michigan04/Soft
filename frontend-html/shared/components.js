/*
 * Plain-JS ports of frontend/src/components/*.vue (and layout/*.vue) as global
 * Vue 3 "options API" component objects -- no <script setup>, no SFC compiler,
 * no scoped CSS (styles live in main.css / layout.css instead). Registered on
 * window.Components so any page can pick the ones it needs:
 *   components: { MetricCard: Components.MetricCard, ... }
 *
 * Needs Vue (global build), axios and shared/api.js loaded first for
 * InterventionForm/Header; Auth from shared/auth.js for Header's sign-out;
 * Nav from shared/nav.js for Sidebar.
 */
(function () {
  const MetricCard = {
    props: {
      label: { type: String, required: true },
      value: { type: [String, Number], required: true },
      hint: { type: String, default: "" },
      accent: { type: String, default: "#1f2333" },
    },
    template: `
      <div class="card card-pad metric-card">
        <div class="metric-label">{{ label }}</div>
        <div class="metric-value" :style="{ color: accent }">{{ value }}</div>
        <div v-if="hint" class="metric-hint text-muted text-sm">{{ hint }}</div>
      </div>
    `,
  };

  const RISK_BADGE_COLORS = { low: "#2f9e44", moderate: "#e8a400", high: "#e8590c", critical: "#c92a2a" };
  const RiskBadge = {
    props: { level: { type: String, default: null } },
    computed: {
      color() {
        return RISK_BADGE_COLORS[this.level] || "#9499ab";
      },
      label() {
        return this.level ? this.level.toUpperCase() : "UNASSESSED";
      },
      style() {
        return { color: this.color, background: `${this.color}18` };
      },
    },
    template: `
      <span class="badge" :style="style">
        <span class="badge-dot" :style="{ background: color }"></span>
        {{ label }}
      </span>
    `,
  };

  const SEVERITY_BADGE_COLORS = { info: "#1c7ed6", warning: "#e8a400", critical: "#c92a2a" };
  const SeverityBadge = {
    props: { severity: { type: String, required: true } },
    computed: {
      color() {
        return SEVERITY_BADGE_COLORS[this.severity] || "#9499ab";
      },
      style() {
        return { color: this.color, background: `${this.color}18` };
      },
    },
    template: `<span class="badge" :style="style">{{ severity }}</span>`,
  };

  const LoadingState = {
    props: { rows: { type: Number, default: 4 } },
    template: `
      <div class="loading-wrap">
        <div class="skeleton" v-for="n in rows" :key="n" :style="{ height: '18px', marginBottom: '10px' }"></div>
      </div>
    `,
  };

  const ErrorState = {
    props: {
      message: { type: String, default: "We could not load this data. Please try again." },
      retry: { type: Boolean, default: true },
    },
    emits: ["retry"],
    template: `
      <div class="state-box">
        <h3>Something went wrong</h3>
        <p>{{ message }}</p>
        <button v-if="retry" class="btn btn-secondary" @click="$emit('retry')">Try again</button>
      </div>
    `,
  };

  const EmptyState = {
    props: {
      title: { type: String, default: "Nothing here yet" },
      message: { type: String, default: "There is no data to show." },
    },
    template: `
      <div class="state-box">
        <h3>{{ title }}</h3>
        <p>{{ message }}</p>
        <slot />
      </div>
    `,
  };

  const Pagination = {
    props: {
      page: { type: Number, required: true },
      pages: { type: Number, required: true },
      total: { type: Number, required: true },
    },
    emits: ["update:page"],
    template: `
      <div class="flex items-center justify-between pagination">
        <span class="text-muted text-sm">Page {{ page }} of {{ pages || 1 }} ({{ total }} total)</span>
        <div class="flex gap-8">
          <button class="btn btn-secondary btn-sm" :disabled="page <= 1" @click="$emit('update:page', page - 1)">
            Previous
          </button>
          <button class="btn btn-secondary btn-sm" :disabled="page >= pages" @click="$emit('update:page', page + 1)">
            Next
          </button>
        </div>
      </div>
    `,
  };

  const ConfirmDialog = {
    props: {
      modelValue: { type: Boolean, default: false },
      title: { type: String, default: "Are you sure?" },
      message: { type: String, default: "This action cannot be undone." },
      confirmLabel: { type: String, default: "Confirm" },
      danger: { type: Boolean, default: false },
    },
    emits: ["confirm", "cancel", "update:modelValue"],
    template: `
      <div v-if="modelValue" class="modal-overlay" @click.self="$emit('cancel')">
        <div class="modal-box">
          <h3 style="margin-bottom: 10px">{{ title }}</h3>
          <p class="text-muted" style="margin-bottom: 20px">{{ message }}</p>
          <div class="flex gap-8" style="justify-content: flex-end">
            <button class="btn btn-secondary" @click="$emit('cancel')">Cancel</button>
            <button class="btn" :class="danger ? 'btn-danger' : 'btn-primary'" @click="$emit('confirm')">
              {{ confirmLabel }}
            </button>
          </div>
        </div>
      </div>
    `,
  };

  const InterventionForm = {
    props: { studentId: { type: String, required: true } },
    emits: ["created", "cancel"],
    data() {
      return {
        form: { intervention_type: "call", description: "", follow_up_date: "" },
        submitting: false,
        error: "",
      };
    },
    methods: {
      async submit() {
        this.submitting = true;
        this.error = "";
        try {
          const { data } = await Api.interventions.createIntervention({
            student_id: this.studentId,
            intervention_type: this.form.intervention_type,
            description: this.form.description,
            follow_up_date: this.form.follow_up_date || null,
          });
          this.$emit("created", data);
        } catch (e) {
          this.error = Api.apiErrorMessage(e);
        } finally {
          this.submitting = false;
        }
      },
    },
    template: `
      <form @submit.prevent="submit">
        <div class="field">
          <label>Type</label>
          <select v-model="form.intervention_type" class="input" required>
            <option value="call">Call</option>
            <option value="email">Email</option>
            <option value="meeting">Meeting</option>
            <option value="academic_counselling">Academic Counselling</option>
            <option value="remedial_recommendation">Remedial Recommendation</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div class="field">
          <label>Description</label>
          <textarea v-model="form.description" class="input" rows="3" required></textarea>
        </div>
        <div class="field">
          <label>Follow-up date (optional)</label>
          <input v-model="form.follow_up_date" type="date" class="input" />
        </div>
        <p v-if="error" class="field-error" style="margin-bottom: 10px">{{ error }}</p>
        <div class="flex gap-8" style="justify-content: flex-end">
          <button type="button" class="btn btn-secondary" @click="$emit('cancel')">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? "Saving..." : "Log Intervention" }}
          </button>
        </div>
      </form>
    `,
  };

  const Sidebar = {
    props: {
      open: { type: Boolean, default: false },
      user: { type: Object, default: null },
    },
    emits: ["close"],
    computed: {
      items() {
        return Nav.visibleNavItems(this.user);
      },
      currentPage() {
        return location.pathname.split("/").pop();
      },
    },
    methods: {
      isActive(item) {
        return item.page === this.currentPage;
      },
    },
    template: `
      <div>
        <div v-if="open" class="sidebar-scrim" @click="$emit('close')"></div>
        <aside class="sidebar" :class="{ open }">
          <div class="brand">
            <div class="crest">IM</div>
            <div class="brand-text">
              <div class="brand-title">IIT Madras</div>
              <div class="brand-sub">Risk &amp; Intervention Platform</div>
            </div>
          </div>

          <nav class="nav">
            <a
              v-for="item in items"
              :key="item.key"
              :href="item.href"
              class="nav-item"
              :class="{ active: isActive(item) }"
              @click="$emit('close')"
            >
              {{ item.label }}
            </a>
          </nav>

          <div class="sidebar-footer text-sm">Dev / Demo Build</div>
        </aside>
      </div>
    `,
  };

  const Header = {
    props: { user: { type: Object, default: null } },
    emits: ["toggle-sidebar"],
    data() {
      return { unread: 0 };
    },
    computed: {
      initials() {
        return (this.user?.full_name || "?")
          .split(" ")
          .map((p) => p[0])
          .slice(0, 2)
          .join("")
          .toUpperCase();
      },
    },
    async mounted() {
      try {
        const { data } = await Api.notifications.listNotifications();
        this.unread = data.filter((n) => !n.is_read).length;
      } catch (e) {
        /* notification count is non-critical */
      }
    },
    methods: {
      signOut() {
        Auth.logout();
        location.href = "Login.html";
      },
    },
    template: `
      <header class="topbar">
        <button class="hamburger" aria-label="Toggle navigation" @click="$emit('toggle-sidebar')">
          <span></span><span></span><span></span>
        </button>

        <div class="spacer"></div>

        <a href="Notifications.html" class="icon-btn" title="Notifications">
          <span>Notifications</span>
          <span v-if="unread > 0" class="unread-dot">{{ unread > 9 ? "9+" : unread }}</span>
        </a>

        <div class="user-menu">
          <div class="avatar">{{ initials }}</div>
          <div class="user-info">
            <div class="user-name">{{ user?.full_name }}</div>
            <div class="user-role text-muted">{{ user?.role }}</div>
          </div>
          <button class="btn btn-secondary btn-sm" @click="signOut">Sign out</button>
        </div>
      </header>
    `,
  };

  const AppShell = {
    components: { Sidebar, Header },
    props: { user: { type: Object, default: null } },
    data() {
      return { sidebarOpen: false };
    },
    template: `
      <div class="app-shell">
        <Sidebar :open="sidebarOpen" :user="user" @close="sidebarOpen = false" />
        <div class="main-col">
          <Header :user="user" @toggle-sidebar="sidebarOpen = !sidebarOpen" />
          <main class="main-content">
            <slot />
          </main>
        </div>
      </div>
    `,
  };

  window.Components = {
    MetricCard,
    RiskBadge,
    SeverityBadge,
    LoadingState,
    ErrorState,
    EmptyState,
    Pagination,
    ConfirmDialog,
    InterventionForm,
    Sidebar,
    Header,
    AppShell,
  };
})();
