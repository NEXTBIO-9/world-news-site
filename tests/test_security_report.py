import importlib.util
import pathlib
import unittest

PATH=pathlib.Path(__file__).resolve().parents[1]/"scripts/generate_security_report.py"
spec=importlib.util.spec_from_file_location("security",PATH)
security=importlib.util.module_from_spec(spec)
spec.loader.exec_module(security)

def sample():
    return [{"source":name,"title":"Security event","url":"https://example.com/"+str(i)} for i,name in enumerate(("Source A","Source B","Source C"))]

def assessment():
    return {"publish":True,"headline":"동아시아 안보정세 종합 분석",
            "source_indices":[0,1,2],"confidence":"보통","risk":"평가 불가",
            **{k:["실제 확인된 자료에 기반한 제한적인 평가입니다."] for k in ("key_judgments","situation","implications","outlook_7d","outlook_30d","indicators")}}

class ValidationTests(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(security.valid(assessment(),sample()))
    def test_reject_two_sources(self):
        a=assessment();a["source_indices"]=[0,1]
        self.assertFalse(security.valid(a,sample()))
    def test_reject_duplicate_publishers(self):
        articles=sample();articles[2]["source"]="Source A"
        self.assertFalse(security.valid(assessment(),articles))
    def test_reject_invalid_source_index(self):
        a=assessment();a["source_indices"]=[0,1,999]
        self.assertFalse(security.valid(a,sample()))
    def test_reject_no_publish(self):
        a=assessment();a["publish"]=False
        self.assertFalse(security.valid(a,sample()))
    def test_reject_missing_section(self):
        a=assessment();a["situation"]=[]
        self.assertFalse(security.valid(a,sample()))

if __name__=="__main__":unittest.main()
