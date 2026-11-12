
from drafter import *
from dataclasses import dataclass
import random

set_website_title("Blackjack")
set_site_information(
    author="Augie Reith",
    description="Play blackjack vs. a computer.",
    sources="Myself and ChatGPT.",
    planning=["plan.pdf", "design.pdf"],
    links=["https://github.com/areith54/Blackjack"]
)
hide_debug_information()
set_website_framed(False)


@dataclass
class Card:
    suit: str
    rank: str
    value: int

@dataclass
class State:
    player_hand: list
    dealer_hand: list
    deck: list
    game_status: str
    player_score: int
    balance: float
    player_name: str
    bet: int
    games_played: int
    games_won: int
    split_hand: list
    active_hand: str
    result_message: str

def create_deck():
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = [
        ("2", 2), ("3", 3), ("4", 4), ("5", 5),
        ("6", 6), ("7", 7), ("8", 8), ("9", 9),
        ("10", 10), ("J", 10), ("Q", 10),
        ("K", 10), ("A", 11)]
    deck = []
    for suit in suits:
        for rank, value in ranks:
            deck.append(Card(suit, rank, value))
    random.shuffle(deck)
    return deck


def draw_card(state):
    if len(state.deck) == 0:
        state.deck = create_deck()
    return state.deck.pop()


def hand_total(hand):
    total = 0
    # Loop through every card in the hand.
    for card in hand:
        total += card.value
    # Change aces from 11 to 1 if necessary.
    for card in hand:
        if total > 21 and card.rank == "A" and card.value == 11:
            card.value = 1
            total -= 10
    return total

def display_hand(hand):
    cards = []
    for card in hand:
        cards.append(card.rank + " of " + card.suit)
    return ", ".join(cards)

def get_active_hand(state):
    if state.active_hand == "split":
        return state.split_hand
    return state.player_hand


def check_player_bust(state):
    hand = get_active_hand(state)
    return hand_total(hand) > 21


def game_board(state):
    content = [
        Header("Blackjack"),
        "Player: " + state.player_name,
        "Balance: $" + str(state.balance),
        "Current bet: $" + str(state.bet),
        "",
        Header("Dealer's Hand"),
        # Only show the dealer's first card during the player's turn.
        display_hand(state.dealer_hand[:1]) + ", Hidden Card",
        "",
        Header("Your Hand"),
        display_hand(state.player_hand),
        "Your total: " + str(hand_total(state.player_hand)),
    ]

    if state.split_hand:
        content += [
            "",
            Header("Your Split Hand"),
            display_hand(state.split_hand),
            "Split total: " + str(hand_total(state.split_hand)),
            "Currently playing: " + state.active_hand
        ]

    content += [
        "",
        Button("Hit", "hit"),
        Button("Stand", "stand"),
    ]

    # Only allow splitting if the player has two matching cards.
    if (len(state.player_hand) == 2
            and state.player_hand[0].rank == state.player_hand[1].rank
            and not state.split_hand
            and state.balance >= state.bet):
        content.append(Button("Split", "split"))

    content.append(Button("Statistics", "statistics"))

    return Page(state, content)


# ----------------------------------
# ROUTE 1: HOME PAGE
# ----------------------------------

@route
def index(state: State):
    return Page(state, [
        Header("Welcome to Blackjack!"),
        "Welcome to the blackjack simulator, " +
        state.player_name + "!",
        "",
        "Play blackjack without gambling real money.",
        "Your starting balance is $1000.",
        "",
        "Enter your name:",
        TextBox("player_name", state.player_name),
        "",
        Button("Continue", "home"),
        Button("Statistics", "statistics")
    ])


# ----------------------------------
# ADDITIONAL ROUTE: SAVE PLAYER NAME
# ----------------------------------

@route
def home(state: State, player_name: str):
    if player_name.strip() != "":
        state.player_name = player_name

    return Page(state, [
        Header("Blackjack Simulator"),
        "Welcome, " + state.player_name + "!",
        "Current balance: $" + str(state.balance),
        "",
        "Choose your bet to start playing:",
        SelectBox("bet", ["10", "25", "50", "100"]),
        "",
        Button("Start Game", "start_game"),
        Button("View Statistics", "statistics")
    ])


# ----------------------------------
# ROUTE 2: START GAME
# ----------------------------------

@route
def start_game(state: State, bet: str):
    bet_amount = int(bet)

    # Make sure the player has enough money.
    if bet_amount > state.balance or bet_amount <= 0:
        state.result_message = "You do not have enough money!"
        return Page(state, [
            Header("Invalid Bet"),
            state.result_message,
            Button("Try Again", "home")
        ])

    state.bet = bet_amount
    state.balance -= bet_amount

    # Create a fresh deck.
    state.deck = create_deck()

    # Reset the hands.
    state.player_hand = []
    state.dealer_hand = []
    state.split_hand = []
    state.active_hand = "player"
    state.game_status = "playing"
    state.result_message = ""

    # Deal two cards to each player.
    state.player_hand.append(draw_card(state))
    state.dealer_hand.append(draw_card(state))
    state.player_hand.append(draw_card(state))
    state.dealer_hand.append(draw_card(state))

    state.player_score = hand_total(state.player_hand)

    # Check for an immediate blackjack.
    if state.player_score == 21:
        return dealer_turn(state)

    return game_board(state)


# ----------------------------------
# ROUTE 3: HIT
# ----------------------------------

@route
def hit(state: State):
    if state.game_status != "playing":
        return results(state)

    # Draw a card for whichever hand is active.
    hand = get_active_hand(state)
    hand.append(draw_card(state))

    state.player_score = hand_total(hand)

    # Check whether the player busted.
    if state.player_score > 21:
        if state.active_hand == "player" and state.split_hand:
            # Move to the second hand if the first one busts.
            state.active_hand = "split"
            state.player_score = hand_total(state.split_hand)
            return game_board(state)

        elif state.active_hand == "player" and not state.split_hand:
            state.result_message = "You busted! The dealer wins."
            state.game_status = "finished"
            return results(state)

        elif state.active_hand == "split":
            state.result_message = "Your split hand busted!"
            return dealer_turn(state)

    return game_board(state)


# ----------------------------------
# ROUTE 4: STAND
# ----------------------------------

@route
def stand(state: State):
    if state.game_status != "playing":
        return results(state)

    # If there is a split hand, play both hands.
    if state.active_hand == "player" and state.split_hand:
        state.active_hand = "split"
        state.player_score = hand_total(state.split_hand)

        return Page(state, [
            Header("First Hand Finished"),
            "Now play your second hand!",
            "",
            "Your split hand: " + display_hand(state.split_hand),
            "Total: " + str(state.player_score),
            Button("Hit", "hit"),
            Button("Stand", "stand")
        ])

    # Otherwise, the player is finished.
    return dealer_turn(state)


# ----------------------------------
# ADDITIONAL ROUTE: SPLIT
# ----------------------------------

@route
def split(state: State):
    # Check that the player has two matching cards.
    if (len(state.player_hand) != 2
            or state.player_hand[0].rank != state.player_hand[1].rank
            or state.split_hand
            or state.balance < state.bet):
        return game_board(state)

    # Pay for the second hand.
    state.balance -= state.bet

    # Move one card to the second hand.
    second_card = state.player_hand.pop()
    state.split_hand = [second_card]

    # Give each hand another card.
    state.player_hand.append(draw_card(state))
    state.split_hand.append(draw_card(state))

    state.active_hand = "player"
    state.player_score = hand_total(state.player_hand)

    return game_board(state)


# ----------------------------------
# ROUTE 5: DEALER TURN
# ----------------------------------

@route
def dealer_turn(state: State):
    # The dealer draws until reaching at least 17.
    while hand_total(state.dealer_hand) < 17:
        state.dealer_hand.append(draw_card(state))

    state.game_status = "finished"

    return results(state)


# ----------------------------------
# ROUTE 6: RESULTS
# ----------------------------------

@route
def results(state: State):
    dealer_total = hand_total(state.dealer_hand)

    # Store all hands so split games can be evaluated.
    hands = [state.player_hand]

    if state.split_hand:
        hands.append(state.split_hand)

    messages = []
    round_won = False

    # Evaluate each hand separately.
    for hand in hands:
        player_total = hand_total(hand)
        payout = 0

        if player_total > 21:
            message = "You busted. Dealer wins!"

        elif dealer_total > 21:
            message = "Dealer busted. You win!"
            payout = state.bet * 2
            round_won = True

        elif player_total > dealer_total:
            if player_total == 21 and len(hand) == 2:
                message = "BLACKJACK! You win!"
                payout = state.bet * 2.5
            else:
                message = "You win!"
                payout = state.bet * 2

            round_won = True

        elif player_total == dealer_total:
            message = "It's a tie!"
            payout = state.bet

        else:
            message = "Dealer wins!"

        state.balance += payout

        messages.append(
            message + " Your total: " + str(player_total)
        )

    state.games_played += 1

    if round_won:
        state.games_won += 1

    state.result_message = " ".join(messages)
    state.player_score = hand_total(state.player_hand)

    return Page(state, [
        Header("Round Results"),
        "Player: " + state.player_name,
        "",
        Header("Your Hand"),
        display_hand(state.player_hand),
        "Total: " + str(hand_total(state.player_hand)),
        "",
        # Show the split hand if one exists.
        *(
            [
                Header("Your Split Hand"),
                display_hand(state.split_hand),
                "Total: " + str(hand_total(state.split_hand)),
                ""
            ] if state.split_hand else []
        ),
        Header("Dealer's Hand"),
        display_hand(state.dealer_hand),
        "Dealer total: " + str(dealer_total),
        "",
        Header("Result"),
        state.result_message,
        "",
        "Updated balance: $" + str(state.balance),
        "",
        Button("Play Again", "home"),
        Button("Statistics", "statistics"),
        Button("Reset Game", "reset_game")
    ])


# ----------------------------------
# ROUTE 7: RESET GAME
# ----------------------------------

@route
def reset_game(state: State):
    state.player_hand = []
    state.dealer_hand = []
    state.deck = create_deck()
    state.split_hand = []

    state.game_status = "not started"
    state.player_score = 0
    state.bet = 0
    state.active_hand = "player"
    state.result_message = ""

    state.balance = 1000
    state.games_played = 0
    state.games_won = 0

    return Page(state, [
        Header("Game Reset!"),
        "Your balance has been restored to $1000.",
        "Your statistics have been reset.",
        "",
        Button("Return Home", "index")
    ])


# ----------------------------------
# ROUTE 8: STATISTICS
# ----------------------------------

@route
def statistics(state: State):
    return Page(state, [
        Header("Player Statistics"),
        "Player: " + state.player_name,
        "",
        "Current Balance: $" + str(state.balance),
        "Games Played: " + str(state.games_played),
        "Games Won: " + str(state.games_won),
        "Games Lost: " + str(state.games_played - state.games_won),
        "",
        "Win Rate: " + str(
            round(state.games_won / state.games_played * 100, 1)
            if state.games_played > 0 else 0
        ) + "%",
        "",
        Button("Return Home", "index"),
        Button("Play Blackjack", "home"),
        Button("Reset Game", "reset_game")
    ])
start_server(State(
    player_hand=[],
    dealer_hand=[],
    deck=create_deck(),
    game_status="not started",
    player_score=0,
    balance=1000,
    player_name="Player",
    bet=0,
    games_played=0,
    games_won=0,
    split_hand=[],
    active_hand="player",
    result_message=""
))


