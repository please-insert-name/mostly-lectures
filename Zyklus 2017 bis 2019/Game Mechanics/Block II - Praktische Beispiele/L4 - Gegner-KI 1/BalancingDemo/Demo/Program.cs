using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using GameObjects.Characters;
using GameObjects.Interfaces;
using GameObjects.Enums;

namespace Demo
{
    internal static class Program
    {
        public static void Main(string[] args)
        {
            Console.WriteLine("Starting Demo");

            // Create Players
            List<ICharacter> players = new List<ICharacter>()
            {
                new Human("Player 1"),
                new Orc("Player 2")
            };

            players[0].IsActiv = true;
            players[1].IsActiv = true;
            players[0].Target = players[1];
            players[1].Target = players[0];
            
            // Battle Loop
            var round = 0;
            while (ConditionForBattle(players))
            {
                Console.Clear();
                
                foreach (var player in players)
                {
                    foreach (var action in player.ActionsBattle)
                    {
                        if (!action.CheckCondition(player)) continue;
                        
                        Console.WriteLine(player.Name + " is " + action.Description);
                        var success = action.DoAction(player, player.Target);
                        if (success)
                        {
                            Console.WriteLine(player.Name + " was successful");
                            break;
                        }
                        Console.WriteLine(player.Name + " failed");
                        break;
                    }                   
                }

                Console.WriteLine();
                Console.WriteLine("Round " + round.ToString() + "   " + 
                                  players[0].Name + ": " + players[0].Stats[(int)GameObjects.Enums.CharacterStats.LifePoints] + "   " + 
                                  players[1].Name + ": " + players[1].Stats[(int)GameObjects.Enums.CharacterStats.LifePoints]);
                
                round++;
                Console.ReadLine();
            }

            // Finished
            var winner = players[0].IsAlive() && players[0].IsActiv ? players[0].Name : players[1].Name;
            Console.WriteLine(winner + " won!");

            Console.WriteLine("Demo finished");
            Console.ReadLine();
        }

        private static bool ConditionForBattle(IReadOnlyList<ICharacter> players)
        {
            return players[0].IsAlive() && players[1].IsAlive() && players[0].IsActiv && players[1].IsActiv;
        }
    }
}