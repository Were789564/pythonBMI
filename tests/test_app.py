import unittest

from app import app, bmi_guidance, military_service_guidance


class BmiAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_initial_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("了解自己的<br><em>健康狀況。</em>", page)
        self.assertIn("計算你的 BMI", page)
        self.assertIn('name="name"', page)

    def test_calculation_and_advice(self):
        response = self.client.post("/", data={"name": "王小明", "height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertIn("王小明 的 BMI 結果", page)
        self.assertIn("22.5", page)
        self.assertIn("健康體位", page)
        self.assertIn("常備役體位", page)
        self.assertIn("維持均衡飲食", page)

    def test_taiwan_adult_thresholds(self):
        for bmi, category in [
            (18.4, "體重過輕"),
            (18.5, "健康體位"),
            (23.9, "健康體位"),
            (24.0, "體重過重"),
            (26.9, "體重過重"),
            (27.0, "肥胖"),
        ]:
            with self.subTest(bmi=bmi):
                self.assertEqual(bmi_guidance(bmi)["label"], category)

    def test_military_service_thresholds(self):
        for bmi, category in [
            (14.9, "免役體位"),
            (15.0, "替代役體位"),
            (16.4, "替代役體位"),
            (16.5, "常備役體位"),
            (30.9, "常備役體位"),
            (31.0, "替代役體位"),
            (34.9, "替代役體位"),
            (35.0, "免役體位"),
        ]:
            with self.subTest(bmi=bmi):
                self.assertEqual(military_service_guidance(bmi), category)

    def test_invalid_fields_do_not_produce_result(self):
        for height, weight in [("", "65"), ("0", "65"), ("abc", "65"), ("170", "-2"), ("inf", "65"), ("170", "nan"), ("1e-300", "65"), ("1e308", "65"), ("1", "1e308")]:
            with self.subTest(height=height, weight=weight):
                response = self.client.post("/", data={"height": height, "weight": weight})
                page = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn('aria-invalid="true"', page)
                self.assertNotIn("YOUR RESULT", page)

    def test_name_is_optional(self):
        response = self.client.post("/", data={"height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("22.5", page)
        self.assertNotIn("的 BMI 結果", page)

    def test_name_is_escaped(self):
        response = self.client.post("/", data={"name": "<script>alert(1)</script>", "height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; 的 BMI 結果", page)

    def test_target_bmi_shows_weight_change(self):
        response = self.client.post("/", data={"height": "170", "weight": "65", "target_bmi": "20"})
        page = response.get_data(as_text=True)
        self.assertIn("目標 BMI 20.0", page)
        self.assertIn("需要減重 7.2 kg", page)

    def test_target_bmi_is_optional_and_validated(self):
        response = self.client.post("/", data={"height": "170", "weight": "65", "target_bmi": "abc"})
        page = response.get_data(as_text=True)
        self.assertIn("請輸入大於 0 的有效目標 BMI", page)
        self.assertNotIn("YOUR RESULT", page)

    def test_input_is_escaped(self):
        response = self.client.post("/", data={"height": '<script>alert(1)</script>', "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertNotIn("<script>", page)
        self.assertIn("請輸入大於 0", page)


if __name__ == "__main__":
    unittest.main()
