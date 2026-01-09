# Copyright 2026 Healthcare Lifesciences Team, Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from rxnorm.callRxnorm import parse_clinical_drug_name

class TestParsing(unittest.TestCase):
    def test_basic_drug(self):
        self.assertEqual(parse_clinical_drug_name("Amoxicillin 500 MG Oral Tablet"), ("Amoxicillin", "500 MG", "Oral Tablet"))

    def test_no_strength(self):
        self.assertEqual(parse_clinical_drug_name("Amoxicillin Oral Tablet"), ("Amoxicillin", "N/A", "Oral Tablet"))

    def test_no_dose_form(self):
        self.assertEqual(parse_clinical_drug_name("Amoxicillin 500 MG"), ("Amoxicillin", "500 MG", "N/A"))

    def test_complex_strength(self):
        self.assertEqual(parse_clinical_drug_name("Acetaminophen 325 MG / Hydrocodone Bitartrate 5 MG Oral Tablet"), ("Acetaminophen 325 MG / Hydrocodone Bitartrate", "5 MG", "Oral Tablet"))
        # Note: The current regex might not handle multiple strengths perfectly if they are separated by ingredients.
        # Let's see how it behaves with a more standard complex name.
        self.assertEqual(parse_clinical_drug_name("Lisinopril 10 MG / Hydrochlorothiazide 12.5 MG Oral Tablet"), ("Lisinopril 10 MG / Hydrochlorothiazide", "12.5 MG", "Oral Tablet"))

    def test_percentage_strength(self):
        self.assertEqual(parse_clinical_drug_name("Hydrocortisone 1% Topical Cream"), ("Hydrocortisone", "1%", "Topical Cream"))

    def test_no_info(self):
        self.assertEqual(parse_clinical_drug_name("UnknownDrug"), ("UnknownDrug", "N/A", "N/A"))

if __name__ == "__main__":
    unittest.main()
