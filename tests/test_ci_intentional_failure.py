"""只供獨立驗證分支的故意失敗測試，禁止合入正式 PR。"""
import unittest


class IntentionalCIFailure(unittest.TestCase):
    def test_intentional_failure(self):
        self.fail("事前約定的 CI 紅燈驗證；下一 commit 移除")
