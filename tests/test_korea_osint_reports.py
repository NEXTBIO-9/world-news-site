import datetime as dt
import unittest
from scripts.osint.build_reports import build, group, local_day, preserve_published

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
    def test_date_only_kept(self):
        self.assertEqual(local_day({"published":"2026-11-14"}),"2026-11-14")
    def test_daily_includes_date_only(self):
        x=[{"title":"North Korea missile","published":"2026-11-14"}]
        now=dt.datetime(2026,11,15,8,tzinfo=dt.timezone(dt.timedelta(hours=9)))
        self.assertEqual(len(build(x,now)["reports"][0]["items"]),1)
    def test_sunday_before_7am_no_weekly(self):
        now=dt.datetime(2026,11,15,6,59,tzinfo=dt.timezone(dt.timedelta(hours=9)))
        self.assertEqual(len(build([],now)["reports"]),1)
    def test_sunday_at_7am_weekly(self):
        now=dt.datetime(2026,11,15,7,0,tzinfo=dt.timezone(dt.timedelta(hours=9)))
        self.assertEqual(len(build([],now)["reports"]),2)
    def test_preserve_old_daily_before_7am(self):
        new={"updated":"2026-11-16T06:59:00+09:00","reports":[{"type":"daily","date":"2026-11-15","items":[]}]}
        old={"reports":[{"type":"daily","date":"2026-11-14","items":[{"title":"old"}]},{"type":"weekly","date":"2026-11-15"}]}
        out=preserve_published(new,old)
        self.assertEqual(out["reports"][0]["date"],"2026-11-14")
        self.assertEqual(out["reports"][1]["type"],"weekly")
    def test_replace_daily_after_7am(self):
        new={"updated":"2026-11-16T07:00:00+09:00","reports":[{"type":"daily","date":"2026-11-15"}]}
        old={"reports":[{"type":"daily","date":"2026-11-14"}]}
        self.assertEqual(preserve_published(new,old)["reports"][0]["date"],"2026-11-15")
    def test_same_sunday_weekly_not_overwritten(self):
        new={"updated":"2026-11-15T09:00:00+09:00","reports":[{"type":"daily","date":"2026-11-14"},{"type":"weekly","date":"2026-11-15","items":[]}]}
        old={"reports":[{"type":"weekly","date":"2026-11-15","items":[{"title":"published"}]}]}
        self.assertEqual(preserve_published(new,old)["reports"][1]["items"][0]["title"],"published")
    def test_new_sunday_replaces_previous_weekly(self):
        new={"updated":"2026-11-22T07:00:00+09:00","reports":[{"type":"daily","date":"2026-11-21"},{"type":"weekly","date":"2026-11-22"}]}
        old={"reports":[{"type":"weekly","date":"2026-11-15"}]}
        self.assertEqual(preserve_published(new,old)["reports"][1]["date"],"2026-11-22")
    def test_corrupt_previous_reports_list(self):
        new={"updated":"2026-11-16T08:00:00+09:00","reports":[{"type":"daily","date":"2026-11-15"}]}
        self.assertEqual(preserve_published(new,{"reports":None})["reports"][0]["date"],"2026-11-15")
        self.assertEqual(preserve_published(new,{"reports":[None,42,{"type":"weekly","date":"2026-11-15"}]})["reports"][1]["type"],"weekly")
    def test_weekday(self):
        self.assertEqual(len(build([],dt.datetime(2026,11,16,tzinfo=dt.timezone.utc))["reports"]),1)
if __name__=="__main__":unittest.main()
