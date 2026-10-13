#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { chromium } from "playwright";

const samplePath = process.argv[2] || "stage5-aggregate/STAGE5_SAMPLE_PACK_V1.json";
const outputPath = process.argv[3] || "stage5-aggregate/STAGE5_RENDER_QA_V1.json";
const qaPath = process.argv[4] || "stage5-aggregate/STAGE5_66937_QA_V1.json";
const baseUrl = process.env.STAGE5_BASE_URL || "http://127.0.0.1:8000";
const sample = JSON.parse(fs.readFileSync(samplePath, "utf8"));
const targets = sample.render_targets || [];

if (!targets.length) throw new Error("No Stage 5 render targets");

const viewports = [
  { name: "desktop", width: 1365, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];

const browser = await chromium.launch({ headless: true });
const cases = [];
let failures = 0;
let overflowFailures = 0;
let consoleOrPageErrorCases = 0;

for (const target of targets) {
  for (const viewport of viewports) {
    const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height } });
    const errors = [];
    page.on("pageerror", (err) => errors.push(`pageerror:${String(err.message || err)}`));
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(`console:${msg.text()}`);
    });

    const urlPath = "/stage5-work/" + target.source_path.split(path.sep).map(encodeURIComponent).join("/");
    let response = null;
    let navError = null;
    try {
      response = await page.goto(baseUrl + urlPath, { waitUntil: "domcontentloaded", timeout: 30000 });
      await page.waitForTimeout(50);
    } catch (err) {
      navError = String(err);
    }

    const result = {
      file: target.file,
      intent: target.intent,
      locality: target.locality,
      viewport: viewport.name,
      status_code: response ? response.status() : null,
      navigation_error: navError,
      h1: null,
      expected_h1: target.h1,
      horizontal_overflow: null,
      production_flag: null,
      required_blocks: null,
      related_links: null,
      errors,
      status: "PASS",
      failures: [],
    };

    if (!response || !response.ok()) result.failures.push("http");
    if (navError) result.failures.push("navigation");

    if (!navError) {
      const data = await page.evaluate(() => {
        const h1 = document.querySelector("h1")?.textContent?.replace(/\s+/g, " ").trim() || "";
        const root = document.documentElement;
        const required = [
          ".decision-strip",
          ".decision-guide",
          ".mid-cta",
          ".variation-story",
          ".locality-longform",
          ".row-signature",
        ];
        return {
          h1,
          horizontalOverflow: root.scrollWidth > root.clientWidth + 2,
          productionFlag: document.body?.dataset?.productionDeploy || null,
          requiredBlocks: required.reduce((acc, selector) => {
            acc[selector] = Boolean(document.querySelector(selector));
            return acc;
          }, {}),
          relatedLinks: document.querySelectorAll(".related .links a[href$='.html']").length,
        };
      });
      result.h1 = data.h1;
      result.horizontal_overflow = data.horizontalOverflow;
      result.production_flag = data.productionFlag;
      result.required_blocks = data.requiredBlocks;
      result.related_links = data.relatedLinks;

      if (data.h1 !== target.h1) result.failures.push("h1");
      if (data.horizontalOverflow) {
        result.failures.push("horizontal_overflow");
        overflowFailures += 1;
      }
      if (data.productionFlag !== "false") result.failures.push("production_flag");
      if (Object.values(data.requiredBlocks).some((x) => !x)) result.failures.push("required_blocks");
      if (data.relatedLinks < 12) result.failures.push("related_links");
    }

    if (errors.length) {
      result.failures.push("console_or_page_error");
      consoleOrPageErrorCases += 1;
    }
    if (result.failures.length) {
      result.status = "FAIL";
      failures += 1;
    }
    cases.push(result);
    await page.close();
  }
}
await browser.close();

const report = {
  version: "1.0",
  status: failures === 0 ? "PASS" : "FAIL",
  stage: "STAGE5_SAMPLE_RENDER_QA",
  sample_pages: targets.length,
  render_cases: cases.length,
  desktop_cases: cases.filter((x) => x.viewport === "desktop").length,
  mobile_cases: cases.filter((x) => x.viewport === "mobile").length,
  failures,
  horizontal_overflow_failures: overflowFailures,
  console_or_page_error_cases: consoleOrPageErrorCases,
  cases,
  safety: { production_deploy: false, main_merge: false, sitemap_live: false },
};
fs.writeFileSync(outputPath, JSON.stringify(report, null, 2) + "\n", "utf8");

if (fs.existsSync(qaPath)) {
  const qa = JSON.parse(fs.readFileSync(qaPath, "utf8"));
  qa.render_qa = {
    status: report.status,
    file: path.basename(outputPath),
    sample_pages: report.sample_pages,
    render_cases: report.render_cases,
    desktop_cases: report.desktop_cases,
    mobile_cases: report.mobile_cases,
    failures: report.failures,
    horizontal_overflow_failures: report.horizontal_overflow_failures,
    console_or_page_error_cases: report.console_or_page_error_cases,
    production_deploy: false,
  };
  if (report.status === "PASS" && String(qa.status).startsWith("PASS_FULL_GENERATION")) {
    qa.status = "PASS_FULL_GENERATION_AND_SAMPLE_RENDER_READY_STAGE6_REQUIRED_NOT_PRODUCTION";
  } else if (report.status !== "PASS") {
    qa.status = "FAIL";
  }
  fs.writeFileSync(qaPath, JSON.stringify(qa, null, 2) + "\n", "utf8");
}

console.log(JSON.stringify({
  status: report.status,
  sample_pages: report.sample_pages,
  render_cases: report.render_cases,
  failures: report.failures,
  overflow_failures: report.horizontal_overflow_failures,
  console_or_page_error_cases: report.console_or_page_error_cases,
}));

if (failures) process.exit(1);
