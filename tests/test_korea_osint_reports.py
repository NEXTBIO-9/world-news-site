import datetime as dt
import unittest
from scripts.osint.build_reports import build, group, local_day

class ReportTests(unittest.TestCase):
    def test_no_false_corroboration(self):
        x=[{"title":"North Korea missile","published":"2026-11-17","source":"A"},{"title":"North Korea missile","published":"2026-11-17","source":"B"}]
        self.assertEqual(group(x)[0]["count"],2)
        self.assertNotIn("verified",group(x)[0])
    def test_daily_and_sunday(self):
        x=[{"title":"North Korea missile","published":"2026-11-14"}]
        now=dt.datetime(2026,11,15,8,tzinfo=dt.timezone(dt.timedelta(hours=9)))
        self.assertEqual(len(build(x,now)["reports"]),2)
    def test_kst_boundary(self):
        self.assertEqual(local_day({"published":"2026-11-14T16:30:00+00:00"}),"2026-11-15")
    def test_weekday(self):
        self.assertEqual(len(build([],dt.datetime(2026,11,16,tzinfo=dt.timezone.utc))["reports"]),1)
if __name__=="__main__":unittest.main()
