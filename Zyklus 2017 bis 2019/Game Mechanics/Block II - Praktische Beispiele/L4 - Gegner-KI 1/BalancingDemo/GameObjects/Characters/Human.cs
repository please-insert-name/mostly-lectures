using System;
using System.Collections.Generic;
using GameObjects.Actions;
using GameObjects.Interfaces;
using GameObjects.Weapons;

namespace GameObjects.Characters
{
    public sealed class Human : BaseClass
    {
        public Human(string name) : base(name)
        {
            InitializeStats();
            InitializeWeapons();
            InitializeActions();
        }

        protected override void InitializeWeapons()
        {
            WeaponInventory = new List<IWeapon>() {new BareHands()};
            WeaponInventory[0].MaxDamage = Globals.BareHandsHumanMax;
            WeaponInventory[0].MinDamage = Globals.BareHandsHumanMin;
            WeaponInventory[0].StaminaCost = Globals.BareHandsHumanStamina;
            WeaponEquiped = new List<IWeapon>() {WeaponInventory[0]};
            WeaponSkills = new int[Enum.GetNames(typeof(Enums.Weapons)).Length];
            WeaponSkills[(int) Enums.Weapons.BareHands] = (int)Enums.WeaponSkills.Average;
        }

        protected override void InitializeStats()
        {
            Stats[(int) Enums.CharacterStats.LifePoints] = Globals.LifePointsHuman;
            Stats[(int) Enums.CharacterStats.StaminaPoints] = Globals.StaminaHuman;
            MaxStats = new int[Enum.GetNames(typeof(Enums.CharacterStats)).Length];
            MaxStats[(int) Enums.CharacterStats.LifePoints] = Globals.LifePointsHuman;
            MaxStats[(int) Enums.CharacterStats.StaminaPoints] = Globals.StaminaHuman;
        }

        protected override void InitializeActions()
        {
            ActionsBattle = new List<IAction>
            {
                new Surrender(0, Globals.SurrenderLimitHuman),
                new Heal(0, Globals.HealLimitHuman),
                new Attack(0, 0)
            };
        }
    }
}