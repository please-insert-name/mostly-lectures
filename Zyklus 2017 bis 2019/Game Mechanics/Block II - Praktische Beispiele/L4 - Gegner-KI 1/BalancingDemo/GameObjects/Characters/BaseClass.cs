using System;
using System.Collections.Generic;
using GameObjects.Interfaces;

namespace GameObjects.Characters
{
    public abstract class BaseClass : ICharacter
    {
        protected BaseClass(string name)
        {
            this.Name = name;
        }
        
        private int[] _stats = new int[Enum.GetNames(typeof(Enums.CharacterStats)).Length];
        public int[] Stats
        {
            get => _stats;
            set
            {
                for (var i = 0; i < value.Length; i++)
                {
                    if (value[i] > MaxStats[i])
                    {
                        value[i] = MaxStats[i];
                    }
                }

                _stats = value;
            }
        }
        
        public string Name { get; }
        public int[] MaxStats { get; set; }
        public List<IWeapon> WeaponInventory { get; set; }
        public List<IWeapon> WeaponEquiped { get; set; }
        public int[] WeaponSkills { get; set; }
        public List<IAction> ActionsBattle { get; set; }
        public ICharacter Target { get; set; }
        public bool IsActiv { get; set; } = true;

        public bool IsAlive()
        {
            return _stats[(int)Enums.CharacterStats.LifePoints] > 0 ? true : false;
        }

        protected abstract void InitializeWeapons();
        protected abstract void InitializeStats();
        protected abstract void InitializeActions();
    }
}