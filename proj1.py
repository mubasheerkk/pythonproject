# Tic Tac Toe Game

board = [" "] * 9


def display():
    print()
    print(board[0], "|", board[1], "|", board[2])
    print("--+---+--")
    print(board[3], "|", board[4], "|", board[5])
    print("--+---+--")
    print(board[6], "|", board[7], "|", board[8])


def check_winner():

    wins = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [2, 4, 6]
    ]

    for w in wins:
        if board[w[0]] == board[w[1]] == board[w[2]] != " ":
            return True

    return False


while True:

    board = [" "] * 9
    player = "X"

    for i in range(9):

        display()

        print("Player", player, "turn")

        while True:
            try:
                pos = int(input("Enter position (1-9): ")) - 1

                if pos < 0 or pos > 8:
                    print("Enter a number from 1 to 9")
                elif board[pos] != " ":
                    print("Position already taken")
                else:
                    break

            except ValueError:
                print("Please enter a valid number")

        board[pos] = player

        if check_winner():
            display()
            print("Player", player, "wins!")
            break

        if player == "X":
            player = "O"
        else:
            player = "X"

    else:
        display()
        print("Game Draw!")

    again = input("Play again? (y/n): ").lower()

    if again != "y":
        print("Thank you for playing!")
        break
