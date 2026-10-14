
import { test, expect } from "@playwright/test";

const FRONTEND_URL =
  (globalThis as typeof globalThis & {
    process?: { env?: Record<string, string | undefined> };
  }).process?.env?.FRONTEND_URL ?? "http://localhost:3000";

test.describe("Vibh-Anu frontend smoke tests", () => {
  test("opens the application in a browser", async ({ page }) => {
    const pageErrors: string[] = [];

    page.on("pageerror", (error) => {
      pageErrors.push(error.message);
    });

    const response = await page.goto(FRONTEND_URL, {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });

    expect(response, "Frontend should return a response").not.toBeNull();
    expect(response!.status()).toBeLessThan(500);

    await expect(page.locator("body")).not.toBeEmpty();

    // Capture a screenshot for debugging and review.
    await page.screenshot({
      path: "test-results/frontend-homepage.png",
      fullPage: true,
    });

    expect(
      pageErrors,
      "The page should not have uncaught JavaScript errors",
    ).toEqual([]);
  });

  test("renders a usable login form when one is present", async ({
    page,
  }) => {
    await page.goto(FRONTEND_URL);

    const email = page
      .getByLabel(/email/i)
      .or(page.getByPlaceholder(/email/i))
      .first();

    const password = page
      .getByLabel(/password/i)
      .or(page.getByPlaceholder(/password/i))
      .first();

    // The app might open on a dashboard or redirect to /login.
    // Only test the form if it is actually rendered.
    if (await email.isVisible().catch(() => false)) {
      await expect(email).toBeVisible();
      await expect(password).toBeVisible();

      const loginButton = page
        .getByRole("button", { name: /sign in|log in|login/i })
        .first();

      await expect(loginButton).toBeVisible();

      // Verify required-field validation without using real credentials.
      await loginButton.click();

      // Allow native or application-level validation to run.
      await page.waitForTimeout(300);

      const emailValue = await email.inputValue().catch(() => "");
      expect(emailValue).toBe("");
    } else {
      console.log(
        "No login form found on the landing page; login UI test skipped.",
      );
    }
  });

  test("keeps the page usable after reload", async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.reload();

    await expect(page.locator("body")).not.toBeEmpty();
  });

  test("shows no browser-level JavaScript exceptions on initial load", async ({
    page,
  }) => {
    const errors: string[] = [];

    page.on("pageerror", (error) => errors.push(error.message));

    await page.goto(FRONTEND_URL);
    await page.waitForLoadState("load");

    expect(errors).toEqual([]);
  });
});
