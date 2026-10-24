import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useAuthStore } from "./auth";

describe("auth store role getters", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("identifies an admin user", () => {
    const store = useAuthStore();
    store.user = { role: "admin" };
    expect(store.isAdmin).toBe(true);
    expect(store.isStaff).toBe(false);
    expect(store.isStudent).toBe(false);
  });

  it("identifies faculty and ta as staff", () => {
    const store = useAuthStore();
    store.user = { role: "faculty" };
    expect(store.isStaff).toBe(true);
    store.user = { role: "ta" };
    expect(store.isStaff).toBe(true);
  });

  it("identifies a student user", () => {
    const store = useAuthStore();
    store.user = { role: "student" };
    expect(store.isStudent).toBe(true);
    expect(store.isAdmin).toBe(false);
  });

  it("reports not authenticated when there is no token", () => {
    const store = useAuthStore();
    store.token = null;
    expect(store.isAuthenticated).toBe(false);
  });

  it("clears user and token on logout", () => {
    const store = useAuthStore();
    store.token = "abc";
    store.user = { role: "admin" };
    store.logout();
    expect(store.token).toBeNull();
    expect(store.user).toBeNull();
    expect(store.isAuthenticated).toBe(false);
  });
});
