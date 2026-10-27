using System;
using GameObjects.Enums;

namespace GameObjects.Interfaces
{
    public interface IWeapon
    {
        string WeaponName { get; }
        Enums.Weapons WeaponType { get; }
        int MaxDamage { get; set; }
        int MinDamage { get; set; }
        int StaminaCost { get; set; }
        Enums.ObjectCondition ObjectCondition { get; set; }
        bool IsTwoHanded { get; }

        int Attack(int skill);
        bool Defend(int skill, int malus);
        int DealDamage();
        int Exhaust();
    }
}