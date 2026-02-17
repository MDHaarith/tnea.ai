
import unittest
import sys
import os
import logging

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.embedding_search import CollegeEmbeddingSearch

# Mock data
SAMPLE_COLLEGES = [
    {"name": "College of Engineering Guindy", "district": "Chennai", "code": 1},
    {"name": "Madras Institute of Technology", "district": "Chennai", "code": 4},
    {"name": "SSN College of Engineering", "district": "Chengalpattu", "code": 1315},
    {"name": "PSG College of Technology", "district": "Coimbatore", "code": 2006},
    {"name": "Coimbatore Institute of Technology", "district": "Coimbatore", "code": 2007},
]

class TestEmbeddingSearch(unittest.TestCase):
    TEST_ALIASES = {
        "CEG": "COLLEGE OF ENGINEERING GUINDY",
        "MIT": "MADRAS INSTITUTE OF TECHNOLOGY",
        "MIT CHROMEPET": "MADRAS INSTITUTE OF TECHNOLOGY",
        "ANNA UNIVERSITY MAIN CAMPUS": "COLLEGE OF ENGINEERING GUINDY",
    }

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO)
        cls.searcher = CollegeEmbeddingSearch()
        cls.searcher.index_colleges(SAMPLE_COLLEGES, cls.TEST_ALIASES)

    def test_exact_match(self):
        results = self.searcher.search("College of Engineering Guindy", top_k=1)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0][0]['code'], 1)
        self.assertTrue(results[0][1] > 0.6) # High score for exact match

    def test_fuzzy_semantic_match(self):
        # "Anna University Main Campus" -> CEG (conceptually linked in training data usually)
        # OR "CEG" abbreviation
        results = self.searcher.search("CEG Chennai", top_k=1)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0][0]['code'], 1)

    def test_abbreviation_usage(self):
        results = self.searcher.search("MIT Chromepet", top_k=1)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0][0]['code'], 4)

    def test_typo_handling(self):
        results = self.searcher.search("Coimbatore Institue of Techology", top_k=1) # Typos
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0][0]['code'], 2007)

    def test_location_context(self):
         results = self.searcher.search("PSG Coimbatore", top_k=1)
         self.assertTrue(len(results) > 0)
         self.assertEqual(results[0][0]['code'], 2006)

if __name__ == '__main__':
    unittest.main()
