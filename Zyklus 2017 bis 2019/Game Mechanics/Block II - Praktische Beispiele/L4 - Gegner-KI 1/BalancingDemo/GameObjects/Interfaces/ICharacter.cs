using System.Collections.Generic;

namespace GameObjects.Interfaces
{
    public interface ICharacter
    {
        string Name { get; }
        int[] Stats { get; set; }
        int[] MaxStats { get; set; }
        List<IWeapon> WeaponInventory { get; set; }
        List<IWeapon> WeaponEquiped { get; set; }
        int[] WeaponSkills { get; set; }
        List<IAction> ActionsBattle { get; set; }
        ICharacter Target { get; set; }
        bool IsActiv { get; set; }

        bool IsAlive();
    }
}