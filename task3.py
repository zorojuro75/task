import sys
import secrets
import hmac
import hashlib
from typing import List, Tuple, Dict
from itertools import product
from wcwidth import wcswidth


class Dice:
    def __init__(self, sides: List[int]):
        self.sides = sides

    @property
    def num_sides(self) -> int:
        return len(self.sides)

    def get_value(self, index: int) -> int:
        return self.sides[index]

class ProbabilityCalculator:
    @staticmethod
    def calculate_probability(dice_a: Dice, dice_b: Dice) -> float:
        a_wins = 0
        total = 0

        for side_a, side_b in product(dice_a.sides, dice_b.sides):
            if side_a > side_b:
                a_wins += 1
            total += 1

        return a_wins / total if total > 0 else 0.0

class ProbabilityTableGenerator:
    @staticmethod
    def pad_center(text: str, width: int) -> str:
        visible_width = wcswidth(text)
        pad = max(width - visible_width, 0)
        left = pad // 2
        right = pad - left
        return " " * left + text + " " * right

    @staticmethod
    def generate_table(dices: List['Dice']) -> str:
        dice_labels = [",".join(str(s) for s in dice.sides) for dice in dices]

        col_width = max(max(wcswidth(label) for label in dice_labels), 13) + 2

        header = "| " + ProbabilityTableGenerator.pad_center("User dice v", col_width) + " |"
        header += "".join(
            ProbabilityTableGenerator.pad_center(label, col_width) + "  |" for label in dice_labels
        )
        border = "+" + "+".join(["-" * (col_width + 2) for _ in range(len(dice_labels) + 1)]) + "+"

        table_lines = [border, header, border]

        for i, dice_i in enumerate(dices):
            row = "| " + ProbabilityTableGenerator.pad_center(dice_labels[i], col_width) + " |"
            for j, dice_j in enumerate(dices):
                if i == j:
                    cell = ProbabilityTableGenerator.pad_center("------", col_width)
                else:
                    prob = ProbabilityCalculator.calculate_probability(dice_i, dice_j)
                    cell = ProbabilityTableGenerator.pad_center(f"{prob:.4f}", col_width)
                row += cell + "  |"
            table_lines.append(row)
            table_lines.append(border)

        return "\n".join(table_lines)
    
class DiceParser:
    def __init__(self, args: List[str]):
        self.args = args
        self.dices: List[Dice] = []

    def parse(self) -> List[Dice]:
        self._validate_minimum_args()

        for i, arg in enumerate(self.args, 1):
            dice_values = self._parse_dice_values(arg, i)
            self.dices.append(Dice(dice_values))

        self._validate_dice_sizes()
        self._validate_unique_dice()
        return self.dices

    def _validate_minimum_args(self) -> None:
        if len(self.args) < 3:
            raise ValueError(
                "At least 3 dice are required. Example usage:\n"
                "  python task.py 2,2,4,4,9,9 6,8,1,1,8,6 7,5,3,7,5,3"
            )

    def _parse_dice_values(self, arg: str, dice_number: int) -> List[int]:
        values = [x.strip() for x in arg.split(',') if x.strip()]
        try:
            dice_values = [int(x) for x in values]
        except ValueError:
            raise ValueError(f"Dice {dice_number} contains non-integer values.")

        if len(dice_values) < 6:
            raise ValueError(f"Dice {dice_number} must have at least 6 sides, but has {len(dice_values)} sides.")

        return dice_values

    def _validate_dice_sizes(self) -> None:
        if not self.dices:
            return

        expected_size = self.dices[0].num_sides
        for i, dice in enumerate(self.dices[1:], 2):
            if dice.num_sides != expected_size:
                raise ValueError(
                    f"Dice 1 has {expected_size} sides, but Dice {i} has {dice.num_sides} sides."
                )

    def _validate_unique_dice(self) -> None:
        for i in range(len(self.dices)):
            for j in range(i + 1, len(self.dices)):
                if self.dices[i].sides == self.dices[j].sides:
                    raise ValueError(
                        f"Dice {i + 1} and Dice {j + 1} have identical sides: {self.dices[i].sides}."
                    )

        for i in range(len(self.dices)):
            for j in range(i + 1, len(self.dices)):
                common_values = set(self.dices[i].sides) & set(self.dices[j].sides)
                if common_values:
                    raise ValueError(
                        f"Dice {i + 1} and Dice {j + 1} share common values: {sorted(common_values)}."
                    )

class SecureRandomizer:
 
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end
        self.range_size = end - start + 1
        self.secret_key = secrets.token_bytes(32)
        self.computer_number = self._generate_secure_random()

    def _generate_secure_random(self) -> int:
        bits_needed = self.range_size.bit_length()
        while True:
            random_bytes = secrets.token_bytes((bits_needed + 7) // 8)
            rand_num = int.from_bytes(random_bytes, "big")
            if rand_num < self.range_size:
                return rand_num + self.start

    def get_hmac(self) -> str:
        num_bytes = (self.computer_number.bit_length() + 7) // 8 or 1
        message = self.computer_number.to_bytes(num_bytes, "big")
        return hmac.new(self.secret_key, message, hashlib.sha3_256).hexdigest()

    def reveal(self) -> Tuple[int, str]:
        return self.computer_number, self.secret_key.hex()

class GameManager:

    def __init__(self, dices: List[Dice], user_first: bool):
        self.dices = dices
        self.user_first = user_first
        self.user_dice: Dice = None
        self.comp_dice: Dice = None

    def select_dices(self) -> None:
        if self.user_first:
            self._handle_user_first_selection()
        else:
            self._handle_computer_first_selection()

    def _handle_user_first_selection(self) -> None:
        while True:
            print("Choose your dice:")
            for i, dice in enumerate(self.dices):
                print(f"{i} - {dice.sides}")
            print("X - exit")
            print("? - help")

            selection = input("Your selection: ").strip()
            if selection == "?":
                print(ProbabilityTableGenerator.generate_table(self.dices))
                continue
            if selection.upper() == "X":
                sys.exit(0)

            try:
                user_dice_index = int(selection)
                if not (0 <= user_dice_index < len(self.dices)):
                    raise ValueError
            except ValueError:
                print("Invalid input. Try again.")
                continue

            self.user_dice = self.dices[user_dice_index]
            print(f"You chose: {self.user_dice.sides}")

            remaining_indices = self._get_remaining_indices(user_dice_index)
            comp_dice_index = secrets.choice(remaining_indices)
            self.comp_dice = self.dices[comp_dice_index]
            print(f"I chose: {self.comp_dice.sides}")
            break

    def _handle_computer_first_selection(self) -> None:
        comp_dice_index = secrets.randbelow(len(self.dices))
        self.comp_dice = self.dices[comp_dice_index]
        print(f"I choose first: {self.comp_dice.sides}")

        while True:
            remaining_indices = self._get_remaining_indices(comp_dice_index)
            print("Choose your dice:")
            for i in remaining_indices:
                print(f"{i} - {self.dices[i].sides}")
            print("X - exit")
            print("? - help")

            selection = input("Your selection: ").strip()
            if selection == "?":
                print(ProbabilityTableGenerator.generate_table(self.dices))
                continue
            if selection.upper() == "X":
                sys.exit(0)

            try:
                user_dice_index = int(selection)
                if user_dice_index not in remaining_indices:
                    raise ValueError
            except ValueError:
                print("Invalid input. Try again.")
                continue

            self.user_dice = self.dices[user_dice_index]
            print(f"You chose: {self.user_dice.sides}")
            break

    def _get_remaining_indices(self, excluded_index: int) -> List[int]:
        return [i for i in range(len(self.dices)) if i != excluded_index]
    def play_game(self) -> Dict[str, int]:
        user_round = GameRound("User", self.user_dice)
        comp_round = GameRound("Computer", self.comp_dice)

        user_result = user_round.play()
        comp_result = comp_round.play()

        return {"User": user_result, "Computer": comp_result}

class GameRound:
    def __init__(self, player_name: str, dice: Dice):
        self.player_name = player_name
        self.dice = dice
        self.result: int = None

    def play(self) -> int:
        self._display_round_header()
        
        randomizer = self._setup_randomizer()
        user_input = self._get_user_input()
        result_value = self._calculate_and_display_result(randomizer, user_input)
        
        self.result = result_value
        return result_value

    def _display_round_header(self) -> None:
        if self.player_name == "Computer":
            print("It's time for my roll.")
        else:
            print("It's time for your roll.")

    def _setup_randomizer(self) -> SecureRandomizer:
        randomizer = SecureRandomizer(0, self.dice.num_sides - 1)
        print(f"I selected a random value in the range 0..{self.dice.num_sides - 1} (HMAC={randomizer.get_hmac()}).")
        return randomizer

    def _get_user_input(self) -> int:
        while True:
            print(f"Add your number modulo {self.dice.num_sides}.")
            for i in range(self.dice.num_sides):
                print(f"{i} - {i}")
            print("X - exit")
            print("? - help")

            selection = input("Your selection: ").strip()
            if selection == "?":
                print(ProbabilityTableGenerator.generate_table([self.dice]))
                continue
            if selection.upper() == "X":
                sys.exit(0)

            try:
                user_input = int(selection)
                if not (0 <= user_input < self.dice.num_sides):
                    raise ValueError
                return user_input
            except ValueError:
                print("Invalid input. Try again.")


    def _calculate_and_display_result(self, randomizer: SecureRandomizer, user_input: int) -> int:
        comp_number, key = randomizer.reveal()
        
        print(f"My number is {comp_number} (KEY={key}).")

        combined_index = (comp_number + user_input) % self.dice.num_sides
        result_value = self.dice.get_value(combined_index)

        print(f"The fair number generation result is {comp_number} + {user_input} = {combined_index} (mod {self.dice.num_sides}).")
        
        if self.player_name == "Computer":
            print(f"My roll result is {result_value}.")
        else:
            print(f"Your roll result is {result_value}.")
        
        return result_value

class GameOrchestrator: 
    @staticmethod
    def run_game() -> None:
        try:
            args = sys.argv[1:]
            dices = GameOrchestrator._parse_dice(args)
            user_first = GameOrchestrator._determine_first_player(dices)

            results = GameOrchestrator._play_main_game(dices, user_first)
            GameOrchestrator._display_final_results(results)
            
        except Exception as e:
            print("Error:", e)
            sys.exit(1)

    @staticmethod
    def _parse_dice(args: List[str]) -> List[Dice]:
        parser = DiceParser(args)
        return parser.parse()

    @staticmethod
    def _determine_first_player(dices: List[Dice]) -> bool:
        print("Let's determine who makes the first move.")

        toss = SecureRandomizer(0, 1)
        print(f"I selected a random value in the range 0..1 \n(HMAC={toss.get_hmac()}).")

        while True:
            print("Try to guess my selection.")
            print("0 - 0")
            print("1 - 1")
            print("X - exit")
            print("? - help (show dice probability table)")

            selection = input("Your selection: ").strip()
            if selection == "?":
                print(ProbabilityTableGenerator.generate_table(dices))
                continue
            if selection.upper() == "X":
                sys.exit(0)

            try:
                user_input = int(selection)
                if user_input not in [0,1]:
                    raise ValueError
            except ValueError:
                print("Invalid input. Try again.")
                continue
            break

        comp_num, secret_key = toss.reveal()

        print(f"My selection: {comp_num} (KEY={secret_key}).")

        user_first = comp_num == user_input
        return user_first

    @staticmethod
    def _play_main_game(dices: List[Dice], user_first: bool) -> Dict[str, int]:
        game_manager = GameManager(dices, user_first)
        game_manager.select_dices()
        return game_manager.play_game()

    @staticmethod
    def _display_final_results(results: Dict[str, int]) -> None:
        user_result = results["User"]
        computer_result = results["Computer"]
        
        if user_result > computer_result:
            print(f"You win ({user_result} > {computer_result})!")
        elif computer_result > user_result:
            print(f"I win ({computer_result} > {user_result})!")
        else:
            print(f"It's a tie ({user_result} = {computer_result})!")

GameOrchestrator.run_game()