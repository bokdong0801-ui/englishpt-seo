#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast, safe smoke QA for Stage 9 audience Hero V2 (no deploy, no forms POST)."""
from __future__ import annotations

import importlib.util
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("stage9_hero_copy", ROOT / "scripts/stage9_hero_copy.py")
assert SPEC and SPEC.loader
HERO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HERO)
INTENTS = {
    "elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv",
    "biz-business-conv","housewife-conv","toeic","toeic-speaking","opic",
    "ielts","duolingo","toefl","toeic-academy",
    "toeic-speaking-academy","opic-academy","ielts-academy",
    "duolingo-academy","toefl-academy","english-conv-academy",
    "adult-english-conv-academy","worker-english-conv-academy",
    "beginner-english-conv",
}


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ignore = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.ignore += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.ignore = max(0, self.ignore - 1)
    def handle_data(self, data):
        if not self.ignore:
            self.parts.append(data)


class TestAudienceHero(unittest.TestCase):
    def loc(self, i: int):
        return {"slug": f"sample-locality-{i}", "dong": f"샘플{i}동", "service": "왕초보영어회화"}

    def test_all_23_intents_have_valid_markup_and_ctas(self):
        self.assertEqual(len(INTENTS), 23)
        for intent in INTENTS:
            loc = self.loc(11)
            loc["service"] = "토익학원" if intent.endswith("academy") else "영어회화"
            heading = f'{loc["dong"]} {loc["service"]}'
            page = HERO.render_hero(loc, intent, heading)
            with self.subTest(intent=intent):
                self.assertEqual(HERO.audit_copy(loc, intent, heading), [])
                self.assertIn(heading, page)
                self.assertIn('href="#consultation-preview"', page)
                self.assertIn('href="#detail"', page)
                self.assertEqual(page.count("<article>"), 3)
                self.assertNotIn('type="submit"', page)
                self.assertNotIn("<img", page)

    def test_beginner_avoids_pressuring_vocabulary(self):
        text = HERO.render_hero(self.loc(3), "beginner-english-conv", "샘플3동 왕초보영어회화")
        for word in ("훈련", "진단", "실전", "교정", "병목", "재점검", "재검증"):
            self.assertNotIn(word, text)

    def test_stable_and_different_for_neighboring_localities(self):
        for intent in INTENTS:
            seen = set()
            for n in range(80):
                loc = self.loc(n)
                h1 = f'{loc["dong"]} {loc["service"]}'
                a = HERO.render_hero(loc, intent, h1)
                self.assertEqual(a, HERO.render_hero(loc, intent, h1))
                self.assertNotIn(a, seen)
                seen.add(a)

    def test_source_renderer_references_new_copy_module(self):
        source = (ROOT / "scripts/stage9-clean-mass-renderer.py").read_text(encoding="utf-8")
        self.assertIn('HERO_COPY.render_hero(loc, intent, h1)', source)
        self.assertIn('HERO_COPY.audit_copy(loc, intent, h1)', source)
        self.assertIn('beginner_exam_guide(intent, loc)', source)

    def test_hubs_have_ctas_and_immediate_guide(self):
        filenames = ("englishpt.html", "courses.html", "student-english.html",
                     "english-conversation.html", "exam-english.html")
        for path in filenames:
            raw = (ROOT / path).read_text(encoding="utf-8")
            hero_match = re.search(r'<section class="hero[^"]*">.*?</section>', raw, re.S)
            with self.subTest(file=path):
                self.assertIsNotNone(hero_match)
                self.assertEqual(raw.count("<h1>"), 1)
                self.assertIn('hero-choice-actions', hero_match.group())
                self.assertIn('hero-entry-panel', raw[hero_match.end():hero_match.end()+200])
                self.assertIn("data-open-form", hero_match.group())
                self.assertIn('id="applyModal"', raw)
                self.assertIn('name="englishpt-consultation"', raw)
                self.assertIn('name="consent"', raw)
                self.assertIn("assets/site.js", raw)
                for target in re.findall(r'href="#([^"]+)"', hero_match.group()):
                    self.assertIn(f'id="{target}"', raw)

    def test_homepage_has_no_pressure_terms_in_visible_body(self):
        raw = (ROOT / "englishpt.html").read_text(encoding="utf-8")
        parser = VisibleText()
        parser.feed(raw)
        visible = " ".join(parser.parts)
        for word in ("훈련", "진단", "실전", "교정", "병목", "재점검", "재검증"):
            self.assertNotIn(word, visible)

    def test_mobile_styles_exist(self):
        hub = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        mass = (ROOT / "assets/stage9-mass-production.css").read_text(encoding="utf-8")
        for marker in (".hero-choice-actions", ".hero-entry-grid", ".hero-entry-panel"):
            self.assertIn(marker, hub)
        for marker in (".hero-next-grid", ".hero-next-step"):
            self.assertIn(marker, mass)


if __name__ == "__main__":
    unittest.main()
