import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import Pagination from "./Pagination.vue";

describe("Pagination", () => {
  it("disables Previous on the first page", () => {
    const wrapper = mount(Pagination, { props: { page: 1, pages: 5, total: 100 } });
    const [prev, next] = wrapper.findAll("button");
    expect(prev.attributes("disabled")).toBeDefined();
    expect(next.attributes("disabled")).toBeUndefined();
  });

  it("disables Next on the last page", () => {
    const wrapper = mount(Pagination, { props: { page: 5, pages: 5, total: 100 } });
    const [prev, next] = wrapper.findAll("button");
    expect(prev.attributes("disabled")).toBeUndefined();
    expect(next.attributes("disabled")).toBeDefined();
  });

  it("emits update:page with the next page number", async () => {
    const wrapper = mount(Pagination, { props: { page: 2, pages: 5, total: 100 } });
    const [, next] = wrapper.findAll("button");
    await next.trigger("click");
    expect(wrapper.emitted("update:page")[0]).toEqual([3]);
  });
});
