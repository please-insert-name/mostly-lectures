using System;
using System.Runtime.InteropServices;
using GameObjects.Interfaces;

namespace GameObjects.Weapons
{
    public class BareHands : IWeapon
    {
        private readonly Random _rnd = new Random();
        
        public BareHands()
        {
            this.WeaponName = "Bare Hands";
            this.WeaponType = Enums.Weapons.BareHands;
            this.ObjectCondition = Enums.ObjectCondition.Good;
            this.IsTwoHanded = true;
        }
        
        public string WeaponName { get; }
        public Enums.Weapons WeaponType { get; }
        public int MaxDamage { get; set; }
        public int MinDamage { get; set; }
        public int StaminaCost { get; set; }
        public Enums.ObjectCondition ObjectCondition { get; set; }
        public bool IsTwoHanded { get; }

        public int Attack(int skill)
        {
            var success = skill - _rnd.Next(1, Globals.MaxRandom);
            return success > 0 ? success : 0;
        }

        public bool Defend(int skill, int malus)
        {
            var defended = (skill - malus) > _rnd.Next(1, Globals.MaxRandom);
            return defended;
        }

        public int DealDamage()
        {
            return _rnd.Next(MinDamage, MaxDamage);
        }

        public int Exhaust()
        {
            return StaminaCost;
        }
    }
}