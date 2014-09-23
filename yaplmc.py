#!/usr/bin/env python3
"""
Yet Another Python Little Man Computer written in Python 3
Copyright (C) 2013  Matthew Joyce matsjoyce@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

instructions = {"ADD": "1xx",
                "SUB": "2xx",
                "STA": "3xx",
                "LDA": "5xx",
                "BRA": "6xx",
                "BRZ": "7xx",
                "BRP": "8xx",
                "INP": "901",
                "OUT": "902",
                "HLT": "000",
                "DAT": None
                }


def add_arg(memo, arg, lineno, line):
    instr = instructions[memo]
    if arg and len(arg) > 2:
        raise SyntaxError("Bad argument on line {}: '{}'".format(lineno + 1,
                                                                 memo))
    if arg:
        arg = arg.zfill(2)
    if "xx" in instr:
        if not arg:
            raise SyntaxError("Instruction on line {} "
                              "takes an argument: '{}'".format(lineno + 1,
                                                               memo))
        return instr.replace("xx", arg)
    if arg:
        raise SyntaxError("Instruction on line {} "
                          "has no argument: '{}'".format(lineno + 1, memo))
    return instr


def assemble(lines):
    labels = {}
    instrs = []
    # Turn list of lines into list of (instruction, argument)
    i = 0
    for lineno, origline in enumerate(lines):
        line = origline
        if "#" in line:
            line = line[:line.find("#")]
        line = line.strip()
        if not line:
            continue
        line = line.split()
        if len(line) == 3:
            label, instr, arg = line
        elif len(line) == 2:
            if line[0] in instructions:
                instr, arg = line
                label = None
            else:
                label, instr = line
                arg = None
        elif len(line) == 1:
            instr = line[0]
            label = arg = None
        else:
            raise SyntaxError("Invalid line {}: '{}'".format(lineno + 1,
                                                             origline))
        instr = instr.upper()
        if instr not in instructions:
            raise SyntaxError("Invalid mnemonic at line {}:"
                              " '{}'".format(lineno + 1, instr))
        if label:
            if label in labels:
                orig_line = instrs[labels[label]][3] + 1
                raise SyntaxError("Duplicate label '{}' "
                                  "on lines {} and {}".format(label,
                                                              lineno + 1,
                                                              orig_line))
            labels[label] = i
        instrs.append((instr, arg, origline, lineno))
        i += 1
    # resolve arguments and assemble
    assembled = []
    for instr, arg, line, lineno in instrs:
        if instr == "DAT":
            if arg:
                i = int(arg)
                arg = 1000 + i if i < 0 else i
            else:
                arg = 0
            assembled.append(arg)
        else:
            if arg in labels:
                arg = str(labels[arg])
            assembled.append(int(add_arg(instr, arg, lineno, line)))
    l = len(assembled)
    while len(assembled) != 100:
        assembled.append(0)
    return assembled, l

DEBUG_LEVEL_NONE = 0
DEBUG_LEVEL_LOW = 1
DEBUG_LEVEL_MEDIUM = 2
DEBUG_LEVEL_HIGH = 3


class Runner:
    def __init__(self, program, get_input=None, use_input_callback=False,
                 give_output=None, debug_output=None, debug_level=0):
        self.counter = 0
        self.accumulator = 0
        self.code = program
        self.memory = self.code.copy()
        self.get_input = get_input if get_input else self._get_input
        self.give_output = give_output if give_output else self._give_output
        self.use_input_callback = use_input_callback
        self.debug_level = debug_level
        self.unfiltered_debug_output = debug_output or self._debug_output

    def debug_output(self, msg, level):
        if level <= self.debug_level:
            self.unfiltered_debug_output(msg)

    def cap(self, i):
        return (i + 1000) % 1000

    def int_to_complement(self, i):
        return 1000 + i if i < 0 else i

    def int_from_complement(self, i):
        return i - 1000 if i >= 500 else i

    def _get_input(self):
        return int(input("<<< "))

    def _give_output(self, i):
        print(">>>", i)

    def _debug_output(self, i):
        print(i)

    def input_callback(self, i):
        self.accumulator = self.cap(i)
        return self.rth

    def next_step(self, rth=False):
        self.debug_output("Executing next instruction"
                          " at {:03}".format(self.counter), DEBUG_LEVEL_HIGH)
        instruction = self.memory[self.counter]
        self.debug_output("Next instruction is {:03}".format(instruction),
                          DEBUG_LEVEL_MEDIUM)
        memory_str = ", ".join("{}: {:03}".format(i, self.memory[i])
                               for i in range(100))
        self.debug_output("Memory: {}".format(memory_str), DEBUG_LEVEL_MEDIUM)
        self.counter += 1
        self.debug_output("Incrementing counter to {}".format(self.counter),
                          DEBUG_LEVEL_HIGH)
        addr = instruction % 100
        if addr > 99:
            raise RuntimeError("Invalid memory address")
        if instruction == 0:  # HLT
            self.debug_output("HLT", DEBUG_LEVEL_LOW)
            self.give_output("Done! Coffee break!")
            return True
        elif instruction < 100:
            raise RuntimeError("Invalid instruction {:03}".format(instruction))
        elif instruction < 200:  # ADD
            value = self.cap(self.accumulator + self.memory[addr])
            self.debug_output("ADD {:03}: accumulator = {} + {} = {}"
                              .format(addr, self.accumulator,
                                      self.memory[addr], value),
                              DEBUG_LEVEL_LOW)
            self.accumulator = value
        elif instruction < 300:  # SUB
            value = self.cap(self.accumulator - self.memory[addr])
            self.debug_output("SUB {:03}: accumulator = {} - {} = {}"
                              .format(addr, self.accumulator,
                                      self.memory[addr], value),
                              DEBUG_LEVEL_LOW)
            self.accumulator = value
        elif instruction < 400:  # STA
            self.debug_output("STA {:03}: accumulator = {}"
                              .format(addr, self.accumulator), DEBUG_LEVEL_LOW)
            self.memory[addr] = self.accumulator
        elif instruction < 600:  # LDA
            self.debug_output("LDA {:03}: value = {}"
                              .format(addr, self.memory[addr]),
                              DEBUG_LEVEL_LOW)
            self.accumulator = self.memory[addr]
        elif instruction < 700:  # BRA
            self.debug_output("BRA {:03}".format(addr), DEBUG_LEVEL_LOW)
            self.counter = addr
        elif instruction < 800:  # BRZ
            word = "" if self.accumulator == 0 else " no"
            self.debug_output("BRZ {:03}: accumulator = {}, so{} branch"
                              .format(addr, self.accumulator, word),
                              DEBUG_LEVEL_LOW)
            if self.accumulator == 0:
                self.counter = addr
        elif instruction < 900:  # BRP
            word = "" if self.accumulator < 500 else " no"
            self.debug_output("BRP {:03}: accumulator = {}, so{} branch"
                              .format(addr, self.accumulator, word),
                              DEBUG_LEVEL_LOW)
            if self.accumulator < 500:
                self.counter = addr
        elif instruction == 901:  # INP
            self.debug_output("INP", DEBUG_LEVEL_LOW)
            if self.use_input_callback:
                self.rth = rth
                return self.input_callback
            else:
                i = self.int_to_complement(self.get_input())
                self.accumulator = self.cap(i)
        elif instruction == 902:  # OUT
            self.debug_output("OUT", DEBUG_LEVEL_LOW)
            self.give_output(self.int_from_complement(self.accumulator))
        else:
            raise RuntimeError("Invalid instruction {:03}".format(instruction))
        return False

    def run_to_hlt(self):
        r = None
        while not r:
            r = self.next_step(rth=True)
        return r

    def reset(self):
        self.counter = 0
        self.accumulator = 0
        self.memory = self.code.copy()

if __name__ == "__main__":
    import argparse

    arg_parser = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                         epilog="""
yaplmc Copyright (C) 2014  Matthew Joyce
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions. Type `yaplmc --licence` for details.
                                         """.strip())
    arg_parser.add_argument("-d", "--debug", help="debug level",
                            type=int, default=0)
    arg_parser.add_argument("-f", "--file", help="lmc file",
                            default=None)
    arg_parser.add_argument("-l", "--licence", help="display licence",
                            action="store_true")

    args_from_parser = arg_parser.parse_args()

    if args_from_parser.licence:
        print(__doc__.strip())
        exit()

    if args_from_parser.file:
        code = open(args_from_parser.file).read().split("\n")
    else:
        code = open(input("Filename: ")).read().split("\n")
    print("Assembling...")
    try:
        machine_code, code_length = assemble(code)
    except SyntaxError as e:
        print("Assembly failed")
        print("Error:", e.args[0])
        exit(1)
    print("Assembly successful")
    print("Running...")
    runner = Runner(machine_code, debug_level=args_from_parser.debug)
    try:
        runner.run_to_hlt()
    except RuntimeError as e:
        print("Error:", e.args[0])
