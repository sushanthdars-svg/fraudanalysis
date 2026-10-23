import { expect, type Page } from "@playwright/test";

export async function login(page: Page, role = "admin") {
  await page.goto("/");
  await page.getByLabel("Email address").fill(`${role}@example.com`);
  await page.getByLabel("Password", { exact: true }).fill("Browser-Test-Only-2026");
  await page.getByRole("button", { name: "Sign in to workspace" }).click();
  await expect(page.getByRole("heading", { name: "Risk operations overview" })).toBeVisible();
}
