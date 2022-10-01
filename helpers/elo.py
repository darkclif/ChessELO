from data.chess_structs import GameDetails, GameResult, GameSide


class EloCalculator:
    ELO_START = 1500
    K_VALUE = 20.0
    RANGE_VALUE = 400.0

    @staticmethod
    def ExpectedScore(player_elo: int, opponent_elo: int):
        return (1.0 / (1.0 + pow(10.0, (float(opponent_elo) - float(player_elo))/EloCalculator.RANGE_VALUE)))

    @staticmethod
    def AddedScore(exp: float, side: int, result: int):
        return int(EloCalculator.K_VALUE * (GameResult.getEloResult(result, side) - exp))

    @staticmethod
    def RecalculateEloIterate(api, timestamp: int):
        players_elo = {id: elo for id, elo in api.GetPlayersElo()}
        game_generator = api.GetAllNotArchivedGamesAscending(timestamp)
        
        if timestamp <= api.GetInfo().elo_calc_date:
            return

        # Main calculation
        for g in game_generator:
            elo1 = players_elo[g.player_1_id]
            elo2 = players_elo[g.player_2_id]

            exp1 = EloCalculator.ExpectedScore(elo1, elo2)
            exp2 = EloCalculator.ExpectedScore(elo2, elo1)

            added1 = EloCalculator.AddedScore(exp1, GameSide.WHITE, g.result)
            added2 = EloCalculator.AddedScore(exp2, GameSide.BLACK, g.result)
            
            players_elo[g.player_1_id] = elo1 + added1
            players_elo[g.player_2_id] = elo2 + added2

            # Debug
            print('')
            print('P1: elo={}, exp={}, added={}'.format(elo1, exp1, added1))
            print('P2: elo={}, exp={}, added={}'.format(elo2, exp2, added2))

            api.AddGameDetails(GameDetails(g.id, elo1, elo2, added1, added2))

        # Debug
        for p_id, elo in players_elo.items():
            print("id: {}, elo: {}".format(p_id, elo))

        # Update players elo
        for p_id, elo in players_elo.items():
            api.UpdatePlayerElo(p_id, elo)
        
        api.UpdateEloTimestamp(timestamp)

    @staticmethod
    def RecalculateArchivedElo(api):
        players_elo = {id: EloCalculator.ELO_START for id in api.GetPlayersId()}
        game_generator = api.GetAllArchivedGamesAscending()
        api.DeleteAllGameDetails()

        # Main calculation
        print('===========================')
        print('Calculation of ELO started.')
        for g in game_generator:
            elo1 = players_elo[g.player_1_id]
            elo2 = players_elo[g.player_2_id]

            exp1 = EloCalculator.ExpectedScore(elo1, elo2)
            exp2 = EloCalculator.ExpectedScore(elo2, elo1)

            added1 = EloCalculator.AddedScore(exp1, GameSide.WHITE, g.result)
            added2 = EloCalculator.AddedScore(exp2, GameSide.BLACK, g.result)
            
            players_elo[g.player_1_id] = elo1 + added1
            players_elo[g.player_2_id] = elo2 + added2

            # Debug
            print('')
            print('P1: elo={}, exp={}, added={}'.format(elo1, exp1, added1))
            print('P2: elo={}, exp={}, added={}'.format(elo2, exp2, added2))

            api.AddGameDetails(GameDetails(g.id, elo1, elo2, added1, added2))

        # Debug
        for p_id, elo in players_elo.items():
            print("id: {}, elo: {}".format(p_id, elo))

        # Update players elo
        for p_id, elo in players_elo.items():
            api.UpdatePlayerElo(p_id, elo)