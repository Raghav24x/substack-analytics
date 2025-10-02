import os
import sqlite3
import tempfile
import unittest
from datetime import datetime

import pandas as pd

from enhanced_collector import PostData, PublicationData, SubstackDataCollector


class ExportToCsvTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.db")
        self.collector_one = SubstackDataCollector("publication-one", self.db_path)
        self.collector_two = SubstackDataCollector("publication-two", self.db_path)

        self.post_one = self._create_post("post-one", self.collector_one.base_url)
        self.post_two = self._create_post("post-two", self.collector_two.base_url)

        self.pub_one = self._create_publication("Publication One", self.collector_one.base_url)
        self.pub_two = self._create_publication("Publication Two", self.collector_two.base_url)

        self.collector_one.save_to_database([self.post_one], self.pub_one)
        self.collector_two.save_to_database([self.post_two], self.pub_two)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_post(self, slug: str, base_url: str) -> PostData:
        now = datetime.utcnow()
        return PostData(
            title=f"Title {slug}",
            slug=slug,
            url=f"{base_url}/p/{slug}",
            content="content",
            excerpt="excerpt",
            author="Author",
            published_at=now,
            updated_at=now,
            word_count=100,
            read_time=5,
            likes=0,
            comments=0,
            shares=0,
            tags=["tag1", "tag2"],
            is_premium=False,
            subscriber_only=False,
        )

    def _create_publication(self, name: str, base_url: str) -> PublicationData:
        return PublicationData(
            name=name,
            description="desc",
            url=base_url,
            subscriber_count=100,
            posts_count=0,
            founded_date=datetime.utcnow(),
            author="Author",
            social_links={},
            revenue_estimate=None,
        )

    def test_export_filters_to_single_publication(self):
        export_prefix = os.path.join(self.temp_dir.name, "publication_one_export")
        self.collector_one.export_to_csv(export_prefix)

        posts_df = pd.read_csv(f"{export_prefix}_posts.csv")
        self.assertFalse(posts_df.empty)
        self.assertTrue(posts_df["url"].str.startswith(self.collector_one.base_url).all())
        self.assertEqual(
            int((posts_df["url"].str.contains("publication-two")).sum()),
            0,
        )

        publication_df = pd.read_csv(f"{export_prefix}_publication.csv")
        self.assertEqual(len(publication_df), 1)
        self.assertEqual(publication_df.loc[0, "name"], "Publication One")

        conn = sqlite3.connect(self.db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
