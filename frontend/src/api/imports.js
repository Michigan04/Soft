import client from "./client";

export function validateImport(importType, file) {
  const form = new FormData();
  form.append("import_type", importType);
  form.append("file", file);
  return client.post("/imports/validate", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export const commitImport = (validationToken) => client.post("/imports/commit", { validation_token: validationToken });
export const listImports = () => client.get("/imports");
