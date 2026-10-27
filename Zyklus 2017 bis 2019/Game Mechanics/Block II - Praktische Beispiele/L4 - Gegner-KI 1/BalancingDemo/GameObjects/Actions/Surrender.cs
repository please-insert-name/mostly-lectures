using GameObjects.Interfaces;

namespace GameObjects.Actions
{
    public class Surrender : IAction
    {
        public string Description { get; }
        public int UpperLimit { get; }
        public int LowerLimit { get; }
        
        public Surrender(int upper, int lower)
        {
            this.Description = "surrendering";
            this.UpperLimit = upper;
            this.LowerLimit = lower;
        }
        
        public bool CheckCondition(ICharacter player)
        {
            return player.Stats[(int)Enums.CharacterStats.LifePoints] < LowerLimit;
        }

        public bool DoAction(ICharacter player, ICharacter otherPlayer = null)
        {
            player.IsActiv = false;
            return true;
        }
    }
}