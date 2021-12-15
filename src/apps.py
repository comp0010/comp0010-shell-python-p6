import re
import sys
import os
from os import listdir
from collections import deque
from abc import ABC, abstractmethod
import fnmatch
import itertools


class Application(ABC):
    @classmethod
    def exec(self, args, stdin):
        raise (Exception(NotImplementedError))


class Pwd(Application):
    def exec(self, args=None, stdin=None):
        stdout = deque()
        stdout.append(os.getcwd())
        return stdout


class Cd(Application):
    def exec(self, args, stdin=None):
        if len(args) == 0 or len(args) > 1:
            raise ValueError("wrong number of command line arguments")
        os.chdir(args[0])
        # print("apps/Cd: " + os.getcwd())


class Echo(Application):
    def exec(self, args, stdin=None):
        stdout = deque()
        # print(args)
        stdout.append(" ".join(args) + "\n")
        return stdout


class Ls:
    def exec(self, args, stdin=None):
        stdout = deque()
        if len(args) == 0:
            ls_dir = os.getcwd()
        elif len(args) > 1:
            raise ValueError("wrong number of command line arguments")
        else:
            ls_dir = args[0]
        for f in listdir(ls_dir):
            if not f.startswith("."):
                stdout.append(f + "\n")
        return stdout


class Cat:
    def exec(self, args, stdin=None):
        stdout = deque()

        if stdin:
            with open(stdin) as f:
                stdout.append(f.read())
        else:
            for a in args:
                with open(a) as f:
                    stdout.append(f.read())

        return stdout


class Head:
    def exec(self, args, stdin=None):
        stdout = deque()
        # print(stdin)
        if stdin:
            if len(args) != 0 and len(args) != 2:
                raise ValueError("wrong number of command line arguments")
            if len(args) == 0:
                num_lines = 10
            if len(args) == 2:
                if args[0] != "-n":
                    raise ValueError("wrong flags")
                else:
                    num_lines = int(args[1])
            with open(stdin) as f:
                lines = f.readlines()
                for i in range(0, min(len(lines), num_lines)):
                    stdout.append(lines[i])
        else:
            if len(args) != 1 and len(args) != 3:
                raise ValueError("wrong number of command line arguments")
            if len(args) == 1:
                num_lines = 10
                file = args[0]
            if len(args) == 3:
                if args[0] != "-n":
                    raise ValueError("wrong flags")
                else:
                    num_lines = int(args[1])
                    file = args[2]
            with open(file) as f:
                lines = f.readlines()
                for i in range(0, min(len(lines), num_lines)):
                    stdout.append(lines[i])
        return stdout


class Tail:
    def exec(self, args, stdin=None):
        stdout = deque()
        # print(stdin)
        if stdin:
            if len(args) != 0 and len(args) != 2:
                raise ValueError("wrong number of command line arguments")
            if len(args) == 0:
                num_lines = 10
            if len(args) == 2:
                if args[0] != "-n":
                    raise ValueError("wrong flags")
                else:
                    num_lines = int(args[1])
            with open(stdin) as f:
                lines = f.readlines()
                display_length = min(len(lines), num_lines)
                for i in range(0, min(len(lines), num_lines)):
                    stdout.append(lines[len(lines) - display_length + i])
        else:
            if len(args) != 1 and len(args) != 3:
                raise ValueError("wrong number of command line arguments")
            if len(args) == 1:
                num_lines = 10
                file = args[0]
            if len(args) == 3:
                if args[0] != "-n":
                    raise ValueError("wrong flags")
                else:
                    num_lines = int(args[1])
                    file = args[2]
            with open(file) as f:
                lines = f.readlines()
                display_length = min(len(lines), num_lines)
                for i in range(0, display_length):
                    stdout.append(lines[len(lines) - display_length + i])
        return stdout


class Grep:
    def exec(self, args, stdin=None):
        # print("args: ", args)
        stdout = deque()
        if len(args) < 2:
            raise ValueError("wrong number of command line arguments")
        pattern = args[0]
        # print(pattern)
        files = args[1:]
        for file in files:
            with open(file) as f:
                lines = f.readlines()

                for line in lines:
                    if re.match(pattern, line):

                        if len(files) > 1:
                            stdout.append(f"{file}:{line}")
                        else:
                            # print(line)
                            stdout.append(line)
        return stdout


class Cut:
    def exec(self, args, stdin=None):
        lines = None
        stdout = deque()
        if len(args) > 3:
            raise ValueError("wrong number of command line arguments")
        elif len(args) == 3:
            if args[0] != "-b":
                raise ValueError("wrong flags")
            pattern = args[1]
            file = args[2]
        else:
            if args[0] != "-b":
                raise ValueError("wrong flags")
            pattern = args[1]
            lines = [stdin.strip()]

        pattern_list = pattern.split(",")
        if not lines:
            with open(file) as f:
                # If the cut command uses the -b option, then when executing this command,
                # cut will sort all the positions after -b from small to large, and then extract them.
                lines = f.readlines()

        for line in lines:
            start_list = []
            end_list = []
            byte_list = []
            cut_line = ""
            for p in pattern_list:
                if "-" in p:
                    start_i, end_i = p.split("-")
                    start_i = 1 if start_i == "" else int(start_i)
                    end_i = len(line) if end_i == "" else int(end_i)
                    start_list.append(int(start_i) - 1)
                    end_list.append(int(end_i) - 1)
                else:
                    byte_list.append(int(p) - 1)
            for i in range(len(line)):
                if i in byte_list:
                    cut_line += line[i]
                else:
                    for j in range(len(start_list)):
                        if i >= start_list[j] and i <= end_list[j]:
                            cut_line += line[i]
                            break
            stdout.append(cut_line + "\n")
        # print(stdout)
        return stdout


class Uniq:
    def exec(self, args, stdin=None):
        stdout = deque()
        ignore = False
        if len(args) > 2:
            raise ValueError("wrong number of command line arguments")
        elif len(args) == 2:
            if args[0] != "-i":
                raise ValueError("wrong flags")
            else:
                ignore = True
            file = args[1]
        elif len(args) == 1:
            file = args[0]

        with open(file) as f:
            lines = f.readlines()
            output = (
                [k for k, g in itertools.groupby(lines)]
                if not ignore
                else [
                    n
                    for i, n in enumerate(lines)
                    if i == 0 or n.casefold() != lines[i - 1].casefold()
                ]
            )
            for i in output:
                stdout.append(i)
        return stdout


class Sort:
    def exec(self, args, stdin=None):
        stdout = deque()
        if len(args) > 2:
            raise ValueError("wrong number of command line arguments")
        elif len(args) == 2:
            if args[0] != "-o":
                raise ValueError("wrong flags")
            else:
                ignore = True
            file = args[1]
        elif len(args) == 1:
            file = args[0]

        with open(file) as f:
            lines = f.readlines()
            lines.sort()
            for i in lines:
                stdout.append(i)
        return stdout


class Find:
    def exec(self, args, stdin=None):
        stdout = deque()
        if len(args) > 3:
            raise ValueError("wrong number of command line arguments")
        elif len(args) == 3:
            if args[1] != "-name":
                raise ValueError("wrong flags")
            pattern = args[2]
            dict = args[0]
        else:
            if args[0] != "-name":
                raise ValueError("wrong flags")
            pattern = args[1]
            dict = "."
        # for path, dirlist, filelist in os.walk(dict):

        #     path1 = path[1:]
        #     index = path1.find("/")
        #     path1 = path[: index + 1]

        #     path2 = path[index + 1 :]

        #     if path1 == os.getcwd():
        #         path = "." + path2

        #     for name in fnmatch.filter(filelist, pattern):
        #         stdout.append(path + "/" + name + "\n")
        # print(stdout)
        res = self.helper(pattern, [dict], [])
        for i in res:
            stdout.append(i + "\n")

        return stdout

    def helper(self, pattern, stack, res):
        while stack:

            current = stack.pop()
            dirs = os.listdir(current)
            # print(current, dirs)

            for d in dirs:
                d1 = os.path.join(current, d)
                if not os.path.isdir(d1):
                    if fnmatch.fnmatch(d, pattern):
                        res.append("/".join([current, d]))
                elif os.path.isdir(d1):
                    stack.append("/".join([current, d]))

        return res


class NotSupported:
    def __init__(self, app_token):
        self.app_token = app_token

    def exec(self, out, args):
        raise ValueError(f"unsupported application {self.app_token}")


class LocalApp:
    def exec(self, out, args):

        return


if __name__ == "__main__":
    print("Cut", Cut().exec)
    # print("Pwd", Pwd().exec())
    # print("Ls", Ls().exec(args=[]))
    # print(
    #     "Ls", Ls().exec(args=["F:\\OneDrive\\OneDrive - University College London\\"])
    # )
    # print("Cat", Cat().exec(args=["test.txt"]))
    # print("Grep", Grep().exec(args=["test file 3*", "test.txt"]))
    # print("Head", Head().exec(args=["-n", 3, "test.txt"]))
    # print("Tail", Tail().exec(args=["-n", 3, "test.txt"]))
    # print("Echo", Echo().exec(args=["test"]))
    # print("Find local", Find().exec(args=["-name", "parsercombinator.*"]))
    # print("Find local", Find().exec(args=["..\doc", "-name", "*.md"]))
    # print("Cut file", Cut().exec(args=["-b", "1-2,-4,8", "test.txt"]))
    # print("Uniq Care case", Uniq().exec(args=["test_abc.txt"]))
    # print("Uniq Ignore case", Uniq().exec(args=["-i", "test_abc.txt"]))
    # print("Sort", Sort().exec(args=["-o", "test_abc.txt"]))
    # args_num = len(sys.argv) - 1
    # if args_num > 0:
    #     if args_num != 2:
    #         raise ValueError("wrong number of command line arguments")
    #     if sys.argv[1] != "-c":
    #         raise ValueError(f"unexpected command line argument {sys.argv[1]}")
    #     out = deque()
    #     print(out)
    #     # eval(sys.argv[2], out)
    #     while len(out) > 0:
    #         print(out.popleft(), end="")
    # else:
    #     while True:
    #         print(os.getcwd() + "> ", end="")
    #         cmdline = input()
    #         out = deque()
    #         print(cmdline,out)
    #         # eval(cmdline, out)
    #         while len(out) > 0:
    #             print(out.popleft(), end="")
