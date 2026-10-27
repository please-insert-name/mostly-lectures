using System;
using GameObjects.Interfaces;

namespace GameObjects.Actions
{
    public class Heal : IAction
    {
        public string Description { get; }
        public int UpperLimit { get; }
        public int LowerLimit { get; }

        public Heal(int upper, int lower)
        {
            this.Description = "healing";
            this.UpperLimit = upper;
            this.LowerLimit = lower;
        }
        
        private readonly Random _rnd = new Random();

        public bool CheckCondition(ICharacter player)
        {
            var condition = player.Stats[(int)Enums.CharacterStats.LifePoints] < LowerLimit;
            return condition ? true : false;
        }

        public bool DoAction(ICharacter player, ICharacter otherPlayer = null)
        {
            var healing = _rnd.Next(0, 4);

            if (healing == 0)
            {
                return false;
            }
            
            player.Stats[(int)Enums.CharacterStats.LifePoints] += healing;

            return true;
        }
    }
}