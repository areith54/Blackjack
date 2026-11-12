round_won = True

        elif dealer_total > 21:
            message = "Dealer busted. You win!"
            payout = state.bet * 2
            round_won = True

        elif player_total > dealer_total:
            message = "You win!"
            payout = state.bet * 2
            round_won = True

        elif player_total == dealer_total:
            message = "It's a tie!"
            payout = state.bet

        else:
            message = "Dealer wins!"

        state.balance += payout
        messages.append(message + " Your total: " + str(player_total))

    state.games_played += 1

    # A round counts as won if at least one hand wins.
    if round_won:
        state.games_won += 1

    state.result_message = " ".join(messages)
    state.player_score = hand_total(state.player_hand)

    return results_page(state)


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
    state.results_calculated = False

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
    games_lost = state.games_played - state.games_won

    if state.games_played > 0:
        win_rate = round(state.games_won / state.games_played * 100, 1)
    else:
        win_rate = 0

    return Page(state, [
        Header("Player Statistics"),
        "Player: " + state.player_name,
        "",
        "Current Balance: $" + str(state.balance),
        "Games Played: " + str(state.games_played),
        "Games Won: " + str(state.games_won),
        "Games Lost: " + str(games_lost),
        "Win Rate: " + str(win_rate) + "%",
        "",
        Button("Return Home", "index"),
        Button("Play Blackjack", "home"),
        Button("Reset Game", "reset_game")
    ])


# ----------------------------------
# START SERVER
# ----------------------------------

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
    result_message="",
    results_calculated=False
))
))


