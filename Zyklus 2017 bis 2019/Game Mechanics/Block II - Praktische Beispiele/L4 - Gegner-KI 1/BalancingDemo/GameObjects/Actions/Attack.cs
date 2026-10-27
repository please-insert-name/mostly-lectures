using GameObjects.Enums;
using GameObjects.Interfaces;

namespace GameObjects.Actions
{
    public class Attack : IAction
    {
        public string Description { get; }
        public int UpperLimit { get; }
        public int LowerLimit { get; }

        public Attack(int upper, int lower)
        {
            this.Description = "attacking";
            this.UpperLimit = upper;
            this.LowerLimit = lower;
        }

        public bool CheckCondition(ICharacter player)
        {
            return true;
        }

        public bool DoAction(ICharacter player, ICharacter otherPlayer = null)
        {
            if (otherPlayer == null)
            {
                return false;
            }

            var equipedPlayer = player.WeaponEquiped[(int) CharacterHands.RightHand];
            var skillPlayer = player.WeaponSkills[(int) equipedPlayer.WeaponType];

            var attack = equipedPlayer.Attack(skillPlayer);
            if (!(attack > 0))
            {
                return false;
            }

            var equipedOtherPlayer = otherPlayer.WeaponEquiped[(int) CharacterHands.RightHand];
            var skillOtherPlayer = otherPlayer.WeaponSkills[(int) equipedPlayer.WeaponType];

            var defend = equipedOtherPlayer.Defend(skillOtherPlayer, attack);
            if (defend)
            {
                return false;
            }

            var damage = equipedPlayer.DealDamage();
            otherPlayer.Stats[(int) CharacterStats.LifePoints] -= damage;

            return true;
        }
    }
}