<template>
  <div class="login-page">
    <div class="login-card card">
      <div class="login-brand">
        <div class="crest">IM</div>
        <div>
          <div class="brand-title">IIT Madras</div>
          <div class="brand-sub text-muted">BS Degree Program &mdash; Risk &amp; Intervention Platform</div>
        </div>
      </div>

      <h1 class="page-title" style="margin: 22px 0 4px">Sign in</h1>
      <p class="text-muted text-sm" style="margin-bottom: 20px">
        Use your demo account credentials to continue.
      </p>

      <form @submit.prevent="onSubmit">
        <div class="field">
          <label for="email">Email</label>
          <input id="email" v-model="email" type="email" class="input" required autocomplete="username" />
        </div>
        <div class="field">
          <label for="password">Password</label>
          <input id="password" v-model="password" type="password" class="input" required autocomplete="current-password" />
        </div>

        <p v-if="error" class="field-error" style="margin-bottom: 14px">{{ error }}</p>

        <button class="btn btn-primary" type="submit" style="width: 100%" :disabled="loading">
          {{ loading ? "Signing in..." : "Sign in" }}
        </button>
      </form>

      <div class="demo-accounts">
        <p class="text-sm text-muted" style="margin-bottom: 8px">Demo accounts (password: <code>Demo@12345</code>):</p>
        <ul class="text-sm text-muted">
          <li>admin@demo.iitm.ac.in &mdash; Administrator</li>
          <li>faculty1@demo.iitm.ac.in &mdash; Faculty</li>
          <li>ta1@demo.iitm.ac.in &mdash; Teaching Assistant</li>
          <li>23f1000003@demo.iitm.ac.in &mdash; Student (high risk)</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { apiErrorMessage } from "@/api/client";

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

async function onSubmit() {
  error.value = "";
  loading.value = true;
  try {
    await auth.login(email.value, password.value);
    router.push(route.query.redirect || { name: "dashboard" });
  } catch (e) {
    error.value = apiErrorMessage(e, "Could not sign in. Check your credentials.");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-sidebar-bg);
  padding: 24px;
}
.login-card {
  width: 100%;
  max-width: 420px;
  padding: 32px;
}
.login-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.crest {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: var(--color-primary);
  color: #fff;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-title {
  font-weight: 700;
  font-size: 15px;
}
.brand-sub {
  font-size: 12px;
}
.demo-accounts {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--color-border);
}
.demo-accounts ul {
  margin: 0;
  padding-left: 18px;
}
.demo-accounts li {
  margin-bottom: 3px;
}
</style>
