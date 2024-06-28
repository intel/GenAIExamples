// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { test, expect, type Page } from "@playwright/test";
import { fileURLToPath } from "url";
import path from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FILE_PATH = path.resolve(__dirname, "test_file.txt");

let consoleMessages: string[] = []; // 声明一个数组来存储控制台消息

// Initialization before each test
test.beforeEach(async ({ page }) => {
	await page.goto("/");

	// 设置控制台消息捕获函数
	page.on("console", (msg) => {
		consoleMessages.push(`${msg.type().substr(0, 3).toUpperCase()} ${msg.text()}`);
	});
});

// Helper function: Check notification text
async function checkNotificationText(page: Page, expectedText: string) {
	const notification = await page.waitForSelector(".notification");
	const notificationText = await notification.textContent();
	expect(notificationText).toContain(expectedText);
}

// Helper function: Enter message to chat
async function enterMessageToChat(page: Page, message: string) {
	await page.getByTestId("chat-input").click();
	await page.getByTestId("chat-input").fill(message);
	await page.getByTestId("chat-input").press("Enter");
	await page.waitForTimeout(10000);
	await expect(page.getByTestId("display-answer")).toBeVisible();
}

// Helper function: Upload file
async function uploadFile(page: Page, filePath: string) {
	const fileUpload = page.getByTestId("file-upload");
	await fileUpload.setInputFiles(filePath);
	await checkNotificationText(page, "Uploaded successfully");
}

// Helper function: Paste link
async function pasteLink(page: Page, link: string) {
	await page.getByTestId("paste-link").fill(link);
	const pasteClick = page.getByTestId("paste-click");
	await pasteClick.click();
	await page.waitForTimeout(10000);
	await checkNotificationText(page, "Uploaded successfully");
}

// Test description: New Chat
test.describe("New Chat", () => {
	// Test: Enter message to chat
	test("should enter message to chat", async ({ page }) => {
		await enterMessageToChat(page, "What is the total revenue of Nike in 2023?");
	});
});

// Test description: Upload file
test.describe("Upload file", () => {
	// Test: Upload file
	test("should upload a file", async ({ page }) => {
		await page.waitForTimeout(10000);
		await page.getByTestId("open-upload").click();
		await page.waitForTimeout(10000);
		await uploadFile(page, FILE_PATH);
	});

	// Test: Paste link
	test("should paste link", async ({ page }) => {
		await page.waitForTimeout(10000);
		await page.getByTestId("open-upload").click();
		await page.waitForTimeout(10000);
		await page.getByTestId("exchange-paste").click();
		await pasteLink(page, "https://www.ces.tech/");
	});
});

// After each test, check if there were any console messages and print them if there were
test.afterEach(async ({ page }) => {
	if (consoleMessages.length > 0) {
		console.log("Console messages:");
		consoleMessages.forEach((msg) => console.log(msg));
	}
	consoleMessages = [];
});
