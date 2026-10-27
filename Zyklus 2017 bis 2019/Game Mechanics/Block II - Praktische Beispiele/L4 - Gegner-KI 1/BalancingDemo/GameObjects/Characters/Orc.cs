using System;
using System.Collections.Generic;
using GameObjects.Actions;
using GameObjects.Interfaces;
using GameObjects.Weapons;

namespace GameObjects.Characters
{
    public sealed class Orc : BaseClass
    {
        public Orc(string name) : base(name)
        {
            InitializeStats();
            InitializeWeapons();
            InitializeActions();
        }

        protected override void InitializeWeapons()
        {
            WeaponInventory = new List<IWeapon>() {new BareHands()};
            WeaponInventory[0].MaxDamage = Globals.BareHandsOrcMax;
            WeaponInventory[0].MinDamage = Globals.BareHandsOrcMin;
            WeaponInventory[0].StaminaCost = Globals.BareHandsOrcStamina;
            WeaponEquiped = new List<IWeapon>() {WeaponInventory[0]};
            WeaponSkills = new int[Enum.GetNames(typeof(Enums.Weapons)).Length];
            WeaponSkills[(int) Enums.Weapons.BareHands] = (int)Enums.WeaponSkills.Average;
        }

        protected override void InitializeStats()
        {
            Stats[(int) Enums.CharacterStats.LifePoints] = Globals.LifePointsOrc;
            Stats[(int) Enums.CharacterStats.StaminaPoints] = Globals.StaminaOrc;
            MaxStats = new int[Enum.GetNames(typeof(Enums.CharacterStats)).Length];
            MaxStats[(int) Enums.CharacterStats.LifePoints] = Globals.LifePointsOrc;
            MaxStats[(int) Enums.CharacterStats.StaminaPoints] = Globals.StaminaOrc;
        }

        protected override void InitializeActions()
        {
            ActionsBattle = new List<IAction>
            {
                new Surrender(0, Globals.SurrenderLimitOrc),
                new Heal(0, Globals.HealLimitOrc),
                new Attack(0, 0)
            };
        }
    }
}