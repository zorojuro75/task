#!/usr/bin/env python3
import sys
import secrets
import hmac
import hashlib
from itertools import product
from typing import List
from wcwidth import wcswidth

class RandomGen:
    def __init__(self):
        self.key = None
        self.num = None

    def get_num(self, min_val: int, max_val: int) -> int:
        self.key = secrets.token_bytes(32)
        self.num = secrets.randbelow(max_val - min_val + 1) + min_val
        return self.num

    def get_hmac(self) -> str:
        return hmac.new(self.key, str(self.num).encode(), hashlib.sha3_256).hexdigest().upper()

    def show_key(self) -> str:
        return self.key.hex().upper()

    def get_number(self) -> int:
        return self.num

class Dice:
    def __init__(self, sides: List[int]):
        self.sides = sides

    @property
    def num_sides(self) -> int:
        return len(self.sides)

    def get_value(self, index: int) -> int:
        return self.sides[index]

    def __str__(self):
        return "[" + ",".join(str(s) for s in self.sides) + "]"

class ProbabilityCalculator:
    @staticmethod
    def win_chance(dice1: Dice, dice2: Dice) -> float:
        wins = 0
        total = 0
        for a, b in product(dice1.sides, dice2.sides):
            if a > b:
                wins += 1
            total += 1
        return wins / total if total else 0.0

    @staticmethod
    def show_table(dices: List[Dice]) -> None:
        labels = [str(d) for d in dices]
        col_width = max(max(wcswidth(lbl) for lbl in labels), 13) + 2
        def pad(s):
            pad = max(col_width - wcswidth(s), 0)
            return " "*(pad//2) + s + " "*(pad - pad//2)
        header = "| " + pad("User dice v") + " |" + "".join(pad(lbl) + " |" for lbl in labels)
        border = "+" + "+".join("-"*(col_width+2) for _ in range(len(labels)+1)) + "+"
        print(border)
        print(header)
        print(border)
        for i, di in enumerate(dices):
            row = "| " + pad(str(di)) + " |"
            for j, dj in enumerate(dices):
                if i == j:
                    cell = pad("------")
                else:
                    p = ProbabilityCalculator.win_chance(di, dj)
                    cell = pad(f"{p:.4f}")
                row += cell + " |"
            print(row)
            print(border)

class Game:
    def __init__(self, dices: List[Dice]):
        self.dices = dices
        self.rng = RandomGen()
        self.user_dice = None
        self.comp_dice = None

    def choose_first(self):
        toss = RandomGen()
        comp_num = toss.get_num(0, 1)
        print(f"I selected a random value in the range 0..1\n(HMAC={toss.get_hmac()}).")
        while True:
            inp = input("Try to guess my selection.\n0 - 0\n1 - 1\nX - exit\n? - help\nYour Selection: ").strip()
            if inp == "?":
                ProbabilityCalculator.show_table(self.dices)
                continue
            if inp.upper() == "X":
                sys.exit(0)
            if inp in ("0","1"):
                guess = int(inp)
                break
            print("Invalid; enter 0 or 1.")
        print(f"My selection: {comp_num} \n(KEY={toss.show_key()}).")
        return guess == comp_num

    def select_dices(self, user_first: bool):
        idx = None
        if user_first:
            while True:
                print("Choose your dice:")
                for i, d in enumerate(self.dices):
                    print(f"{i} - {d}")
                sel = input("X - exit\n? - help\nYour selection: ").strip()
                if sel == "?":
                    ProbabilityCalculator.show_table(self.dices)
                    continue
                if sel.upper() == "X":
                    sys.exit(0)
                if sel.isdigit() and 0 <= int(sel) < len(self.dices):
                    idx = int(sel)
                    self.user_dice = self.dices[idx]
                    print(f"You chose: {self.user_dice}")
                    break
                print("Invalid.")
            rem = [i for i in range(len(self.dices)) if i != idx]
            comp_idx = secrets.choice(rem)
            self.comp_dice = self.dices[comp_idx]
            print(f"I chose: {self.comp_dice}")
        else:
            comp_idx = secrets.randbelow(len(self.dices))
            self.comp_dice = self.dices[comp_idx]
            print(f"I choose first: {self.comp_dice}")
            while True:
                rem = [i for i in range(len(self.dices)) if i != comp_idx]
                print("Choose your dice:")
                for i in rem:
                    print(f"{i} - {self.dices[i]}")
                sel = input("? - help\nX - exit\nYour selection: ").strip()
                if sel == "?":
                    ProbabilityCalculator.show_table(self.dices)
                    continue
                if sel.upper() == "X":
                    sys.exit(0)
                if sel.isdigit() and int(sel) in rem:
                    self.user_dice = self.dices[int(sel)]
                    print(f"You chose: {self.user_dice}")
                    break
                print("Invalid.")

    def play_rounds(self):
        print("It's time for my roll.")
        comp_result = self.play_single(self.comp_dice, "My")
        print("It's time for your roll.")
        user_result = self.play_single(self.user_dice, "Your")
        return user_result, comp_result

    def play_single(self, dice: Dice, name: str):
        faces = dice.num_sides
        rand = RandomGen()
        comp_num = rand.get_num(0, faces - 1)
        print(f"I selected a random value in the range 0..{faces - 1} \n(HMAC={rand.get_hmac()}).")
        print(f"Add your number modulo {faces}.")

        for i in range(faces):
            print(f"{i} - {i}")
        print("X - exit")
        print("? - help")

        while True:
            inp = input("Your selection: ").strip()
            if inp == "?":
                ProbabilityCalculator.show_table(self.dices)
                continue
            if inp.upper() == "X":
                sys.exit(0)
            if inp.isdigit() and 0 <= int(inp) < faces:
                user_num = int(inp)
                break
            print("Invalid.")

        print(f"My number is {comp_num} (KEY={rand.show_key()}).")
        idx = (comp_num + user_num) % faces
        result = dice.get_value(idx)
        print(f"The fair number generation result is {comp_num} + {user_num} = {idx} (mod {faces}).")
        print(f"{name} roll result is {result}.")
        return result

    def run(self):
        user_first = self.choose_first()
        self.select_dices(user_first)
        user_res, comp_res = self.play_rounds()
        if user_res > comp_res:
            print(f"You win ({user_res} > {comp_res})!")
        elif comp_res > user_res:
            print(f"I win ({comp_res} > {user_res})!")
        else:
            print(f"It's a tie ({user_res} = {comp_res})!")

def parse_dices(args: List[str]) -> List[Dice]:
    if len(args) < 3:
        raise ValueError("Require at least 3 dice.")
    dices = []
    for i, arg in enumerate(args, start=1):
        parts = [p.strip() for p in arg.split(",") if p.strip()]
        if len(parts) != 6:
            raise ValueError(f"Dice {i} must have exactly 6 faces.")
        nums = []
        for p in parts:
            try:
                nums.append(int(p))
            except:
                raise ValueError(f"Dice {i} face invalid number: {p}")
        dices.append(Dice(nums))
                      
    size = dices[0].num_sides
    for i, d in enumerate(dices[1:], start=2):
        if d.num_sides != size:
            raise ValueError(f"Dice 1 size {size}, but dice {i} size {d.num_sides}")
    
    for i in range(len(dices)):
        for j in range(i+1, len(dices)):
            if dices[i].sides == dices[j].sides:
                raise ValueError(f"Dice {i+1} and {j+1} have identical sides.")
            if set(dices[i].sides) & set(dices[j].sides):
                common = sorted(set(dices[i].sides) & set(dices[j].sides))
                raise ValueError(f"Dice {i+1} and {j+1} share values {common}.")
    return dices

def main():
    try:
        args = sys.argv[1:]
        dices = parse_dices(args)
    except Exception as e:
        print("Error:", e)
        print("Usage: python task3.py 2,2,4,4,9,9 6,8,1,1,8,6 7,5,3,7,5,3")
        sys.exit(1)
    game = Game(dices)
    game.run()

if __name__ == "__main__":
    main()
