from collections import deque
import unittest

from visitor import ASTVisitor
from abstract_syntax_tree import (
    DoubleQuote,
    Substitution,
    SingleQuote,
    RedirectIn,
    RedirectOut,
    Call,
    Seq,
    Pipe,
)
import os


class TestASTVisitor(unittest.TestCase):
    def setUp(self) -> None:
        os.chdir("./test")
        self.visitor = ASTVisitor()
        with open("file1.txt", "w") as f1:
            f1.write("abc\nadc\nabc\ndef")
        with open("file2.txt", "w") as f2:
            f2.write("file2\ncontent")

    def test_visit_singlequote_empty(self):
        i = SingleQuote("")
        out = self.visitor.visit_single_quote(i)
        self.assertEqual("".join(out["stdout"]), "")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_singlequote_space(self):
        i = SingleQuote("  ")
        out = self.visitor.visit_single_quote(i)
        self.assertEqual("".join(out["stdout"]), "  ")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_singlequote_disable_doublequote(self):
        i = SingleQuote('""')
        out = self.visitor.visit_single_quote(i)
        self.assertEqual("".join(out["stdout"]), '""')
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_singlequote_backquote(self):
        i = SingleQuote("`echo hello`")
        out = self.visitor.visit_single_quote(i)
        self.assertEqual("".join(out["stdout"]), "`echo hello`")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_doublequote_no_substitution(self):
        i = DoubleQuote(["a", "b"], False)
        out = self.visitor.visit_double_quote(i)
        self.assertEqual("".join(out["stdout"]), "ab")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_doublequote_has_substitution(self):
        i = DoubleQuote(["a", "b", Substitution("echo c")], True)
        out = self.visitor.visit_double_quote(i)
        self.assertEqual("".join(out["stdout"]), "abc")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_doublequote_error_unsafe(self):
        i = DoubleQuote(["a", Substitution("_ls a b"), "b"], True)
        out = self.visitor.visit_double_quote(i)
        self.assertEqual("".join(out["stdout"]), "ab")
        assert len(out["stderr"]) > 0
        self.assertNotEquals(out["exit_code"], 0)

    def test_visit_substitution(self):
        i = Substitution("echo foo")
        out = self.visitor.visit_sub(i)
        self.assertEqual("".join(out["stdout"]), "foo")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_substitution_error(self):
        i = Substitution("_ls a b")
        out = self.visitor.visit_sub(i)
        self.assertEqual("".join(out["stdout"]), "")
        assert len(out["stderr"]) > 0
        self.assertNotEquals(out["exit_code"], 0)

    def test_visit_redirectin(self):
        i = RedirectIn("file1.txt")
        out = self.visitor.visit_redirect_in(i)
        self.assertEqual("".join(out["stdout"]), "abc\nadc\nabc\ndef")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_redirectin_glob(self):
        i = RedirectIn("*2.txt")
        out = self.visitor.visit_redirect_in(i)
        self.assertEqual("".join(out["stdout"]), "file2\ncontent")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_redirectin_error(self):
        with self.assertRaises(OSError):
            self.visitor.visit_redirect_in(RedirectIn("notExist.txt"))

    def test_visit_redirectout(self):
        i = RedirectOut("testRedirectout.txt")
        stdin = deque()
        stdin.append("aaa\nbbb\nccc")
        self.visitor.visit_redirect_out(i, stdin=stdin)
        with open("testRedirectout.txt") as f:
            lines = f.readlines()
        self.assertEqual("".join(lines).strip("\n"), "aaa\nbbb\nccc")
        os.remove("testRedirectout.txt")

    def test_visit_redirectout_error(self):
        with self.assertRaises(Exception) as context:
            self.visitor.visit_redirect_out(RedirectOut("*.txt"))
        self.assertEqual("invalid redirection out", str(context.exception))

    def test_visit_call_appname_substitution(self):
        i = Call(
            redirects=[],
            appName=Substitution("echo echo"),
            args=[["hello world"]],
        )
        out = self.visitor.visit_call(i)
        self.assertEqual("".join(out["stdout"]).strip("\n"), "hello world")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_call_appname_substitution_error(self):
        i = Call(
            redirects=[],
            appName=Substitution("_cat notExist.txt"),
            args=[["hello world"]],
        )
        with self.assertRaises(Exception):
            self.visitor.visit_call(i)

    def test_visit_call_redirectin(self):
        i = Call(
            redirects=[RedirectIn("file1.txt")],
            appName="cat",
            args=[],
        )
        out = self.visitor.visit_call(i)
        self.assertEqual("".join(out["stdout"]).strip("\n"), "abc\nadc\nabc\ndef")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_call_redirectout_return(self):
        i = Call(
            redirects=[RedirectOut("testRedirectoutReturn.txt")],
            appName="echo",
            args=[["call\nredirectout"]],
        )
        out = self.visitor.visit_call(i)
        self.assertEqual("".join(out["stdout"]).strip("\n"), "")
        self.assertEqual("".join(out["stderr"]), "")
        os.remove("testRedirectoutReturn.txt")

    def test_visit_call_redirection_invalid(self):
        i = Call(
            redirects=["not redirection type"],
            appName="echo",
            args=[["call\nredirectout"]],
        )
        with self.assertRaises(Exception) as context:
            self.visitor.visit_call(i)
        self.assertEqual("invalid redirections", str(context.exception))

    def test_visit_call_no_redirectin_but_input(self):
        i = Call(
            redirects=[],
            appName="cat",
            args=[],
        )
        out = self.visitor.visit_call(i, in_put="input\ncontent")
        self.assertEqual("".join(out["stdout"]).strip("\n"), "input\ncontent")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_call_redirectin_overwrite_input(self):
        with open("testRedirectinOverwriteInput.txt", "w") as f:
            f.write("redirectin\ncontent")
        i = Call(
            redirects=[RedirectIn("testRedirectinOverwriteInput.txt")],
            appName="cat",
            args=[],
        )
        out = self.visitor.visit_call(i, in_put="input\ncontent")
        self.assertEqual("".join(out["stdout"]).strip("\n"), "redirectin\ncontent")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)
        os.remove("testRedirectinOverwriteInput.txt")

    def test_visit_call_args_doublequote(self):
        i = Call(
            redirects=[],
            appName="echo",
            args=[["aa", DoubleQuote(["bb"], False)]],
        )
        out = self.visitor.visit_call(i)
        self.assertEqual("".join(out["stdout"]).strip("\n"), "aabb")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_call_args_singlequote(self):
        i = Call(
            redirects=[],
            appName="echo",
            args=[["aa"], [SingleQuote("bb")]],
        )
        out = self.visitor.visit_call(i)
        self.assertEqual("".join(out["stdout"]).strip("\n"), "aa bb")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_call_args_substitution(self):
        i = Call(
            redirects=[],
            appName="echo",
            args=[[Substitution("echo arg_sub_content")]],
        )
        out = self.visitor.visit_call(i)
        self.assertEqual("".join(out["stdout"]).strip("\n"), "arg_sub_content")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_call_args_exec_error(self):
        i = Call(
            redirects=[],
            appName="_echo",
            args=[[Substitution("cat notExist.txt")]],
        )
        with self.assertRaises(Exception) as context:
            self.visitor.visit_call(i)
        self.assertEqual(
            "Cat: notExist.txt: No such file or directory", str(context.exception)
        )

    def test_visit_call_args_glob(self):
        with open("file3.txt", "w") as f:
            f.write("file3\ncontent")
        i = Call(
            redirects=[],
            appName="cat",
            args=[["*3.txt"]],
        )
        out = self.visitor.visit_call(i)
        self.assertEqual("".join(out["stdout"]), "file3\ncontent")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)
        os.remove("file3.txt")

    def test_visit_call_args_multiple_glob(self):
        i = Call(
            redirects=[],
            appName="cat",
            args=[["file1.txt"], ["*1.txt"], ["*2.txt"]],
        )
        out = self.visitor.visit_call(i)
        self.assertEqual(
            "".join(out["stdout"]), "abc\nadc\nabc\ndefabc\nadc\nabc\ndeffile2\ncontent"
        )
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_seq_left_error_unsafe(self):
        i = Seq(
            Call(
                redirects=[],
                appName="_ls",
                args=[["notExist"]],
            ),
            Call(
                redirects=[],
                appName="echo",
                args=[["right\noutput"]],
            ),
        )
        out = self.visitor.visit_seq(i)
        self.assertEqual("".join(out["stdout"]).strip("\n"), "right\noutput")
        assert len(out["stderr"]) > 0
        self.assertNotEquals(out["exit_code"], 1)

    def test_visit_seq_right_error_unsafe(self):
        i = Seq(
            Call(
                redirects=[],
                appName="echo",
                args=[["left\noutput"]],
            ),
            Call(
                redirects=[],
                appName="_ls",
                args=[["notExist"]],
            ),
        )
        out = self.visitor.visit_seq(i)
        self.assertEqual("".join(out["stdout"]).strip("\n"), "left\noutput")
        assert len(out["stderr"]) > 0
        self.assertNotEquals(out["exit_code"], 1)

    def test_visit_seq_left_error_right_error_unsafe(self):
        i = Seq(
            Call(
                redirects=[],
                appName="_ls",
                args=[["notExist1"]],
            ),
            Call(
                redirects=[],
                appName="_ls",
                args=[["notExist2"]],
            ),
        )
        out = self.visitor.visit_seq(i)
        self.assertEqual("".join(out["stdout"]), "")
        assert len(out["stderr"]) > 0
        self.assertNotEquals(out["exit_code"], 1)

    def test_visit_seq_no_error(self):
        i = Seq(
            Call(
                redirects=[],
                appName="echo",
                args=[["left\noutput"]],
            ),
            Call(
                redirects=[],
                appName="echo",
                args=[["right\noutput"]],
            ),
        )
        out = self.visitor.visit_seq(i)
        self.assertEqual(
            "".join(out["stdout"]).strip("\n"), "left\noutput\nright\noutput"
        )
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_pipe_with_outleft(self):
        i = Pipe(
            Call(
                redirects=[],
                appName="echo",
                args=[["left output"]],
            ),
            Call(
                redirects=[],
                appName="cut",
                args=[["-b"], ["1,2"]],
            ),
        )
        out = self.visitor.visit_pipe(i)
        self.assertEqual("".join(out["stdout"]).strip("\n"), "le")
        self.assertEqual("".join(out["stderr"]), "")
        self.assertEqual(out["exit_code"], 0)

    def test_visit_pipe_outright_error_unsafe(self):
        i = Pipe(
            Call(
                redirects=[],
                appName="echo",
                args=[["notExist"]],
            ),
            Call(
                redirects=[],
                appName="_cd",
                args=[],
            ),
        )
        out = self.visitor.visit_pipe(i)
        self.assertEqual("".join(out["stdout"]).strip("\n"), "")
        assert len(out["stderr"]) > 0
        self.assertNotEquals(out["exit_code"], 1)

    def tearDown(self) -> None:
        os.remove("file1.txt")
        os.remove("file2.txt")
        os.chdir("./..")


if __name__ == "__main__":
    unittest.main()
