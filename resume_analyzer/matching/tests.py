from django.test import SimpleTestCase

from .utils import (
    combine_scores,
    compute_skill_overlap,
    compute_tfidf_scores,
    extract_numeric_experience,
    safe_load_skills,
)


class ExtractNumericExperienceTests(SimpleTestCase):
    def test_plain_and_plus(self):
        self.assertEqual(extract_numeric_experience("3 years"), 3.0)
        self.assertEqual(extract_numeric_experience("2+ years"), 2.0)

    def test_range_uses_midpoint(self):
        self.assertEqual(extract_numeric_experience("3-5 years"), 4.0)
        self.assertEqual(extract_numeric_experience("2 to 4 yrs"), 3.0)

    def test_unspecified_is_zero(self):
        for text in ("", None, "Fresher", "Not specified"):
            self.assertEqual(extract_numeric_experience(text), 0.0)


class SkillHelpersTests(SimpleTestCase):
    def test_safe_load_skills_accepts_list_dict_and_json(self):
        expected = ["python", "django"]
        self.assertEqual(safe_load_skills([" Python ", "Django"]), expected)
        self.assertEqual(safe_load_skills({"skills": ["Python", "Django"]}), expected)
        self.assertEqual(safe_load_skills('["Python", "Django"]'), expected)
        self.assertEqual(safe_load_skills(None), [])

    def test_overlap_is_share_of_job_skills_covered(self):
        self.assertEqual(compute_skill_overlap(["python", "django"], ["python", "django", "aws", "docker"]), 0.5)
        self.assertEqual(compute_skill_overlap(["python"], []), 0.0)

    def test_combine_scores_weights(self):
        self.assertAlmostEqual(combine_scores(1.0, 0.0), 0.7)
        self.assertAlmostEqual(combine_scores(0.0, 1.0), 0.3)


class TfidfTests(SimpleTestCase):
    def test_relevant_job_scores_higher(self):
        jobs = [
            "python django developer rest api postgresql celery",
            "graphic designer photoshop illustrator branding",
        ]
        sims = compute_tfidf_scores("backend python django postgresql developer", jobs)
        self.assertEqual(len(sims), 2)
        self.assertGreater(sims[0], sims[1])
